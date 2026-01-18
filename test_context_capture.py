#!/usr/bin/env python3
"""
Unit tests for context_capture module.
"""

import pytest
from context_capture import (
    AppType,
    WindowContext,
    SelectedText,
    ClipboardManager,
    detect_application_type,
    extract_file_path,
    extract_browser_info,
    extract_terminal_info,
    extract_ide_line_info,
    extract_vscode_context,
    extract_terminal_context_deep,
    get_context_summary,
    UI_AUTOMATION_AVAILABLE,
)


class TestDetectApplicationType:
    """Tests for detect_application_type function."""

    def test_vscode_by_process(self):
        assert detect_application_type("code.exe") == AppType.IDE

    def test_cursor_by_process(self):
        assert detect_application_type("cursor.exe") == AppType.IDE

    def test_chrome_by_process(self):
        assert detect_application_type("chrome.exe") == AppType.BROWSER

    def test_edge_by_process(self):
        assert detect_application_type("msedge.exe") == AppType.BROWSER

    def test_windows_terminal(self):
        assert detect_application_type("windowsterminal.exe") == AppType.TERMINAL

    def test_powershell(self):
        assert detect_application_type("powershell.exe") == AppType.TERMINAL

    def test_notepad(self):
        assert detect_application_type("notepad.exe") == AppType.EDITOR

    def test_notepadpp(self):
        assert detect_application_type("notepad++.exe") == AppType.EDITOR

    def test_explorer(self):
        assert detect_application_type("explorer.exe") == AppType.EXPLORER

    def test_unknown_process(self):
        assert detect_application_type("unknownapp.exe") == AppType.UNKNOWN

    def test_vscode_by_title(self):
        assert detect_application_type(
            "unknown.exe", "file.py - project - Visual Studio Code"
        ) == AppType.IDE

    def test_chrome_by_title(self):
        assert detect_application_type(
            "unknown.exe", "Google - Google Chrome"
        ) == AppType.BROWSER

    def test_terminal_by_title(self):
        assert detect_application_type(
            "unknown.exe", "Windows PowerShell"
        ) == AppType.TERMINAL


class TestExtractFilePath:
    """Tests for extract_file_path function."""

    def test_vscode_simple(self):
        title = "file.py - myproject - Visual Studio Code"
        result = extract_file_path(title)
        assert result is not None
        assert result["extra"]["filename"] == "file.py"
        assert result["extra"]["folder"] == "myproject"

    def test_vscode_full_path(self):
        title = "file.py - C:\\Users\\test\\project - Visual Studio Code"
        result = extract_file_path(title)
        assert result is not None
        assert result["file_path"] == "C:\\Users\\test\\project\\file.py"

    def test_cursor_simple(self):
        title = "main.rs - rust-project - Cursor"
        result = extract_file_path(title)
        assert result is not None
        assert result["extra"]["filename"] == "main.rs"
        assert result["extra"]["folder"] == "rust-project"

    def test_windsurf_simple(self):
        title = "index.ts - webapp - Windsurf"
        result = extract_file_path(title)
        assert result is not None
        assert result["extra"]["filename"] == "index.ts"
        assert result["extra"]["folder"] == "webapp"

    def test_jetbrains(self):
        title = "App.java - myproject - [C:\\dev\\myproject] - IntelliJ IDEA"
        result = extract_file_path(title)
        assert result is not None
        assert result["file_path"] == "C:\\dev\\myproject"
        assert result["extra"]["filename"] == "App.java"
        assert result["extra"]["project"] == "myproject"

    def test_notepadpp(self):
        title = "C:\\Users\\test\\file.txt - Notepad++"
        result = extract_file_path(title)
        assert result is not None
        assert result["file_path"] == "C:\\Users\\test\\file.txt"

    def test_notepad_simple(self):
        title = "document.txt - Notepad"
        result = extract_file_path(title)
        assert result is not None
        assert result["extra"]["filename"] == "document.txt"

    def test_notepad_unsaved(self):
        title = "*Untitled - Notepad"
        result = extract_file_path(title)
        assert result is not None
        assert result["extra"]["filename"] == "Untitled"

    def test_sublime(self):
        title = "config.json - Sublime Text"
        result = extract_file_path(title)
        assert result is not None
        assert result["extra"]["filename"] == "config.json"

    def test_visual_studio(self):
        title = "Program.cs - ConsoleApp - Microsoft Visual Studio"
        result = extract_file_path(title)
        assert result is not None
        assert result["extra"]["filename"] == "Program.cs"
        assert result["extra"]["project"] == "ConsoleApp"

    def test_generic_path_in_title(self):
        title = "Some App - C:\\path\\to\\file.txt - Other Info"
        result = extract_file_path(title)
        assert result is not None
        assert result["file_path"] == "C:\\path\\to\\file.txt"

    def test_no_match(self):
        title = "Some Random Title"
        result = extract_file_path(title)
        assert result is None


class TestExtractBrowserInfo:
    """Tests for extract_browser_info function."""

    def test_chrome(self):
        title = "GitHub - Where the world builds software - Google Chrome"
        result = extract_browser_info(title)
        assert result is not None
        assert result["extra"]["page_title"] == "GitHub - Where the world builds software"
        assert result["extra"]["browser"] == "chrome"

    def test_edge(self):
        title = "Microsoft - Microsoft Edge"
        result = extract_browser_info(title)
        assert result is not None
        assert result["extra"]["page_title"] == "Microsoft"
        assert result["extra"]["browser"] == "edge"

    def test_firefox(self):
        title = "Mozilla Firefox Home - Mozilla Firefox"
        result = extract_browser_info(title)
        assert result is not None
        assert result["extra"]["page_title"] == "Mozilla Firefox Home"
        assert result["extra"]["browser"] == "firefox"

    def test_brave(self):
        title = "New Tab - Brave"
        result = extract_browser_info(title)
        assert result is not None
        assert result["extra"]["page_title"] == "New Tab"
        assert result["extra"]["browser"] == "brave"

    def test_no_match(self):
        title = "Some Random Window"
        result = extract_browser_info(title)
        assert result is None


class TestExtractTerminalInfo:
    """Tests for extract_terminal_info function."""

    def test_windows_terminal_path(self):
        title = "C:\\Users\\test\\project"
        result = extract_terminal_info(title)
        assert result is not None
        assert result["cwd"] == "C:\\Users\\test\\project"

    def test_windows_terminal_admin(self):
        title = "Administrator: C:\\Windows\\System32"
        result = extract_terminal_info(title)
        assert result is not None
        assert result["cwd"] == "C:\\Windows\\System32"

    def test_powershell_prompt(self):
        title = "PS C:\\Users\\test>"
        result = extract_terminal_info(title)
        assert result is not None
        assert result["cwd"] == "C:\\Users\\test"

    def test_git_bash(self):
        title = "MINGW64:/c/Users/test/project"
        result = extract_terminal_info(title)
        assert result is not None
        assert result["cwd"] == "C:\\Users\\test\\project"

    def test_no_match(self):
        title = "Windows Terminal"
        result = extract_terminal_info(title)
        assert result is None


class TestSelectedText:
    """Tests for SelectedText dataclass."""

    def test_basic_text(self):
        selected = SelectedText(text="Hello World", source="clipboard")
        assert selected.text == "Hello World"
        assert selected.source == "clipboard"
        assert selected.char_count == 11
        assert selected.line_count == 1

    def test_multiline_text(self):
        text = "Line 1\nLine 2\nLine 3"
        selected = SelectedText(text=text, source="clipboard")
        assert selected.char_count == 20
        assert selected.line_count == 3

    def test_empty_text(self):
        selected = SelectedText(text="", source="clipboard")
        assert selected.char_count == 0
        assert selected.line_count == 0  # Empty string has no lines

    def test_to_dict(self):
        selected = SelectedText(text="Test", source="uiautomation")
        result = selected.to_dict()
        assert result["text"] == "Test"
        assert result["source"] == "uiautomation"
        assert result["char_count"] == 4
        assert result["line_count"] == 1


class TestWindowContext:
    """Tests for WindowContext dataclass."""

    def test_to_dict(self):
        context = WindowContext(
            window_handle=12345,
            window_title="test.py - project - Visual Studio Code",
            process_name="code.exe",
            process_id=1234,
            app_type=AppType.IDE,
            file_path="C:\\project\\test.py",
            url=None,
            line_number=42,
            extra={"project": "myproject"},
        )
        result = context.to_dict()

        assert result["window_title"] == "test.py - project - Visual Studio Code"
        assert result["process_name"] == "code.exe"
        assert result["process_id"] == 1234
        assert result["app_type"] == "ide"
        assert result["file_path"] == "C:\\project\\test.py"
        assert result["url"] is None
        assert result["line_number"] == 42
        assert result["extra"]["project"] == "myproject"

    def test_to_dict_with_selected_text(self):
        selected = SelectedText(text="selected code", source="clipboard")
        context = WindowContext(
            window_handle=12345,
            window_title="test.py - Visual Studio Code",
            process_name="code.exe",
            process_id=1234,
            app_type=AppType.IDE,
            selected_text=selected,
        )
        result = context.to_dict()

        assert result["selected_text"] is not None
        assert result["selected_text"]["text"] == "selected code"
        assert result["selected_text"]["source"] == "clipboard"

    def test_to_dict_without_selected_text(self):
        context = WindowContext(
            window_handle=12345,
            window_title="test.py - Visual Studio Code",
            process_name="code.exe",
            process_id=1234,
            app_type=AppType.IDE,
        )
        result = context.to_dict()

        assert result["selected_text"] is None


class TestGetContextSummary:
    """Tests for get_context_summary function."""

    def test_none_context(self):
        result = get_context_summary(None)
        assert "No active window context" in result

    def test_ide_context(self):
        context = WindowContext(
            window_handle=1,
            window_title="test.py - project - Visual Studio Code",
            process_name="code.exe",
            process_id=1,
            app_type=AppType.IDE,
            file_path="C:\\project\\test.py",
        )
        result = get_context_summary(context)

        assert "code.exe" in result
        assert "ide" in result
        assert "C:\\project\\test.py" in result

    def test_browser_context(self):
        context = WindowContext(
            window_handle=1,
            window_title="GitHub - Google Chrome",
            process_name="chrome.exe",
            process_id=1,
            app_type=AppType.BROWSER,
            url="https://github.com",
        )
        result = get_context_summary(context)

        assert "chrome.exe" in result
        assert "browser" in result
        assert "https://github.com" in result

    def test_context_with_selected_text(self):
        selected = SelectedText(text="function foo() {\n  return 42;\n}", source="clipboard")
        context = WindowContext(
            window_handle=1,
            window_title="test.js - Visual Studio Code",
            process_name="code.exe",
            process_id=1,
            app_type=AppType.IDE,
            selected_text=selected,
        )
        result = get_context_summary(context)

        assert "Selected: 31 chars" in result
        assert "3 lines" in result
        assert "function foo()" in result

    def test_context_with_long_selected_text(self):
        # Create text longer than 100 chars
        long_text = "a" * 150
        selected = SelectedText(text=long_text, source="clipboard")
        context = WindowContext(
            window_handle=1,
            window_title="test.txt - Notepad",
            process_name="notepad.exe",
            process_id=1,
            app_type=AppType.EDITOR,
            selected_text=selected,
        )
        result = get_context_summary(context)

        assert "Selected: 150 chars" in result
        assert "..." in result  # Text should be truncated


class TestExtractIDELineInfo:
    """Tests for extract_ide_line_info function (Phase 1.3)."""

    def test_notepadpp_format(self):
        title = "myfile.py - Notepad++ [Line 42, Col 15]"
        result = extract_ide_line_info(title, "notepad++.exe")
        assert result is not None
        assert result["line_number"] == 42
        assert result["column"] == 15

    def test_line_col_format(self):
        title = "editor - Ln 100, Col 5"
        result = extract_ide_line_info(title, "editor.exe")
        assert result is not None
        assert result["line_number"] == 100
        assert result["column"] == 5

    def test_colon_format(self):
        title = "file.py:25 - project - Editor"
        result = extract_ide_line_info(title, "editor.exe")
        assert result is not None
        assert result["line_number"] == 25

    def test_colon_with_column(self):
        title = "file.py:25:10 - project - Editor"
        result = extract_ide_line_info(title, "editor.exe")
        assert result is not None
        assert result["line_number"] == 25
        assert result["column"] == 10

    def test_no_line_info(self):
        title = "file.py - project - Visual Studio Code"
        result = extract_ide_line_info(title, "code.exe")
        assert result is None


class TestExtractVSCodeContext:
    """Tests for extract_vscode_context function (Phase 1.3)."""

    def test_basic_vscode(self):
        title = "main.py - myproject - Visual Studio Code"
        result = extract_vscode_context(title)
        assert result is not None
        assert result["filename"] == "main.py"
        assert result["folder"] == "myproject"

    def test_cursor(self):
        title = "index.ts - webapp - Cursor"
        result = extract_vscode_context(title)
        assert result is not None
        assert result["filename"] == "index.ts"
        assert result["folder"] == "webapp"

    def test_windsurf(self):
        title = "app.rs - rust-project - Windsurf"
        result = extract_vscode_context(title)
        assert result is not None
        assert result["filename"] == "app.rs"
        assert result["folder"] == "rust-project"

    def test_dirty_file(self):
        title = "● main.py - project - Visual Studio Code"
        result = extract_vscode_context(title)
        assert result is not None
        assert result["is_dirty"] == True
        assert result["filename"] == "main.py"

    def test_with_line_number(self):
        title = "main.py:42 - project - Visual Studio Code"
        result = extract_vscode_context(title)
        assert result is not None
        assert result["filename"] == "main.py"
        assert result["line_number"] == 42

    def test_non_vscode(self):
        title = "Some Other Application"
        result = extract_vscode_context(title)
        assert result is None


class TestExtractTerminalContextDeep:
    """Tests for extract_terminal_context_deep function (Phase 1.3)."""

    def test_windows_terminal(self):
        result = extract_terminal_context_deep(
            1, "C:\\Users\\test\\project", "windowsterminal.exe"
        )
        assert result is not None
        assert result["terminal_app"] == "Windows Terminal"
        assert result["cwd"] == "C:\\Users\\test\\project"

    def test_powershell(self):
        result = extract_terminal_context_deep(
            1, "Windows PowerShell", "powershell.exe"
        )
        assert result is not None
        assert result["terminal_app"] == "PowerShell"
        assert result["shell"] == "powershell"

    def test_admin_detection(self):
        result = extract_terminal_context_deep(
            1, "Administrator: C:\\Windows\\System32", "cmd.exe"
        )
        assert result is not None
        assert result["is_admin"] == True

    def test_git_bash(self):
        result = extract_terminal_context_deep(
            1, "MINGW64:/c/Users/test", "mintty.exe"
        )
        assert result is not None
        assert result["terminal_app"] == "Git Bash"
        assert result["shell"] == "bash"


class TestUIAutomationAvailable:
    """Tests for UI Automation availability."""

    def test_ui_automation_flag(self):
        # UI Automation should be available on Windows with comtypes
        assert UI_AUTOMATION_AVAILABLE == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
