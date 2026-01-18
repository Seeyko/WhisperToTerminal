#!/usr/bin/env python3
"""
Unit tests for prompt_assembler module.
"""

import pytest
from context_capture import AppType, WindowContext, SelectedText
from prompt_assembler import (
    PromptAssembler,
    PromptConfig,
    assemble_prompt,
    DEFAULT_TEMPLATES,
)


@pytest.fixture
def mock_ide_context():
    """Create a mock IDE context for testing."""
    return WindowContext(
        window_handle=1,
        window_title="main.py - myproject - Visual Studio Code",
        process_name="code.exe",
        process_id=1234,
        app_type=AppType.IDE,
        file_path="C:\\dev\\myproject\\main.py",
        selected_text=SelectedText(
            text="def hello():\n    print('Hello')",
            source="clipboard"
        ),
        extra={"folder": "myproject", "filename": "main.py"},
    )


@pytest.fixture
def mock_browser_context():
    """Create a mock browser context for testing."""
    return WindowContext(
        window_handle=2,
        window_title="GitHub - Google Chrome",
        process_name="chrome.exe",
        process_id=5678,
        app_type=AppType.BROWSER,
        url="https://github.com/user/repo",
        extra={"page_title": "GitHub", "browser": "chrome"},
    )


@pytest.fixture
def mock_terminal_context():
    """Create a mock terminal context for testing."""
    return WindowContext(
        window_handle=3,
        window_title="C:\\Users\\test",
        process_name="windowsterminal.exe",
        process_id=9012,
        app_type=AppType.TERMINAL,
        file_path="C:\\Users\\test",
        extra={"terminal_type": "wt"},
    )


class TestPromptAssembler:
    """Tests for PromptAssembler class."""

    def test_basic_assembly(self):
        assembler = PromptAssembler()
        result = assembler.assemble("Hello world")
        assert "Hello world" in result
        assert "## Voice Input" in result

    def test_assembly_with_ide_context(self, mock_ide_context):
        assembler = PromptAssembler()
        result = assembler.assemble("Explain this code", mock_ide_context)

        assert "Explain this code" in result
        assert "Code" in result  # app name
        assert "main.py" in result
        assert "def hello():" in result
        assert "```" in result  # code block

    def test_assembly_with_browser_context(self, mock_browser_context):
        assembler = PromptAssembler()
        result = assembler.assemble("What is this page about?", mock_browser_context)

        assert "What is this page about?" in result
        assert "Chrome" in result
        assert "GitHub" in result

    def test_assembly_with_terminal_context(self, mock_terminal_context):
        assembler = PromptAssembler()
        result = assembler.assemble("How do I list files?", mock_terminal_context)

        assert "How do I list files?" in result
        assert "Windowsterminal" in result

    def test_auto_template_selection_ide(self, mock_ide_context):
        config = PromptConfig(template_name="auto")
        assembler = PromptAssembler(config)
        result = assembler.assemble("Test", mock_ide_context)

        # IDE template should include file path prominently
        assert "File" in result

    def test_auto_template_selection_browser(self, mock_browser_context):
        config = PromptConfig(template_name="auto")
        assembler = PromptAssembler(config)
        result = assembler.assemble("Test", mock_browser_context)

        # Browser template should include page info
        assert "Page" in result or "GitHub" in result

    def test_minimal_template(self, mock_ide_context):
        config = PromptConfig(template_name="minimal")
        assembler = PromptAssembler(config)
        result = assembler.assemble("Quick question", mock_ide_context)

        # Minimal template is more concise
        assert "Quick question" in result
        assert "---" in result

    def test_code_review_template(self, mock_ide_context):
        config = PromptConfig(template_name="code_review")
        assembler = PromptAssembler(config)
        result = assembler.assemble("Review this", mock_ide_context)

        assert "Code Review Request" in result
        assert "Review this" in result

    def test_bug_report_template(self, mock_ide_context):
        config = PromptConfig(template_name="bug_report")
        assembler = PromptAssembler(config)
        result = assembler.assemble("There is a bug", mock_ide_context)

        assert "Bug Report" in result
        assert "Environment" in result

    def test_custom_template(self, mock_ide_context):
        config = PromptConfig(
            custom_template="User said: $voice_input\nFile: $file_path"
        )
        assembler = PromptAssembler(config)
        result = assembler.assemble("Test input", mock_ide_context)

        assert "User said: Test input" in result
        assert "File: C:\\dev\\myproject\\main.py" in result

    def test_exclude_context(self, mock_ide_context):
        config = PromptConfig(include_context=False)
        assembler = PromptAssembler(config)
        result = assembler.assemble("Test", mock_ide_context)

        # Context section should be minimal or absent
        assert "## Context" not in result or "Application" not in result

    def test_exclude_selection(self, mock_ide_context):
        config = PromptConfig(include_selection=False)
        assembler = PromptAssembler(config)
        result = assembler.assemble("Test", mock_ide_context)

        # Selected code should not appear
        assert "def hello():" not in result

    def test_truncate_long_selection(self):
        long_text = "x" * 15000
        context = WindowContext(
            window_handle=1,
            window_title="test.py",
            process_name="code.exe",
            process_id=1,
            app_type=AppType.IDE,
            selected_text=SelectedText(text=long_text, source="clipboard"),
        )
        config = PromptConfig(max_selection_chars=1000)
        assembler = PromptAssembler(config)
        result = assembler.assemble("Test", context)

        assert "truncated" in result
        assert len(result) < 15000


class TestCodeLanguageDetection:
    """Tests for code language detection."""

    def test_python_detection(self):
        context = WindowContext(
            window_handle=1,
            window_title="test",
            process_name="code.exe",
            process_id=1,
            app_type=AppType.IDE,
            file_path="C:\\dev\\main.py",
            selected_text=SelectedText(text="print('hi')", source="clipboard"),
        )
        assembler = PromptAssembler()
        result = assembler.assemble("Test", context)

        assert "```python" in result

    def test_typescript_detection(self):
        context = WindowContext(
            window_handle=1,
            window_title="test",
            process_name="code.exe",
            process_id=1,
            app_type=AppType.IDE,
            file_path="C:\\dev\\app.tsx",
            selected_text=SelectedText(text="const x = 1;", source="clipboard"),
        )
        assembler = PromptAssembler()
        result = assembler.assemble("Test", context)

        assert "```tsx" in result

    def test_javascript_detection(self):
        context = WindowContext(
            window_handle=1,
            window_title="test",
            process_name="code.exe",
            process_id=1,
            app_type=AppType.IDE,
            file_path="index.js",
            selected_text=SelectedText(text="let x = 1;", source="clipboard"),
        )
        assembler = PromptAssembler()
        result = assembler.assemble("Test", context)

        assert "```javascript" in result

    def test_rust_detection(self):
        context = WindowContext(
            window_handle=1,
            window_title="test",
            process_name="code.exe",
            process_id=1,
            app_type=AppType.IDE,
            file_path="main.rs",
            selected_text=SelectedText(text="fn main() {}", source="clipboard"),
        )
        assembler = PromptAssembler()
        result = assembler.assemble("Test", context)

        assert "```rust" in result

    def test_explicit_language_override(self):
        context = WindowContext(
            window_handle=1,
            window_title="test",
            process_name="code.exe",
            process_id=1,
            app_type=AppType.IDE,
            file_path="main.py",
            selected_text=SelectedText(text="code", source="clipboard"),
        )
        config = PromptConfig(code_block_lang="sql")
        assembler = PromptAssembler(config)
        result = assembler.assemble("Test", context)

        assert "```sql" in result


class TestListTemplates:
    """Tests for template listing and retrieval."""

    def test_list_templates(self):
        assembler = PromptAssembler()
        templates = assembler.list_templates()

        assert "default" in templates
        assert "ide" in templates
        assert "browser" in templates
        assert "terminal" in templates
        assert "minimal" in templates

    def test_get_template(self):
        assembler = PromptAssembler()
        template = assembler.get_template("default")

        assert template is not None
        assert "$voice_input" in template

    def test_get_nonexistent_template(self):
        assembler = PromptAssembler()
        template = assembler.get_template("nonexistent")

        assert template is None

    def test_add_template(self):
        assembler = PromptAssembler()
        assembler.add_template("custom", "Custom: $voice_input")

        assert "custom" in assembler.list_templates()
        assert assembler.get_template("custom") == "Custom: $voice_input"


class TestConvenienceFunction:
    """Tests for assemble_prompt convenience function."""

    def test_basic_usage(self):
        result = assemble_prompt("Hello")
        assert "Hello" in result

    def test_with_context(self, mock_ide_context):
        result = assemble_prompt("Test", mock_ide_context)
        assert "Test" in result
        assert "main.py" in result

    def test_with_template_name(self, mock_ide_context):
        result = assemble_prompt("Test", mock_ide_context, template_name="minimal")
        assert "Test" in result
        assert "---" in result


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_voice_input(self):
        assembler = PromptAssembler()
        result = assembler.assemble("")
        assert "## Voice Input" in result

    def test_none_context(self):
        assembler = PromptAssembler()
        result = assembler.assemble("Test", None)
        assert "Test" in result

    def test_context_without_selection(self):
        context = WindowContext(
            window_handle=1,
            window_title="test",
            process_name="code.exe",
            process_id=1,
            app_type=AppType.IDE,
            file_path="test.py",
        )
        assembler = PromptAssembler()
        result = assembler.assemble("Test", context)

        assert "Test" in result
        assert "## Selected Code" not in result

    def test_special_characters_in_input(self):
        assembler = PromptAssembler()
        result = assembler.assemble("Test with $pecial ch@racters & <tags>")
        assert "$pecial" in result
        assert "<tags>" in result

    def test_multiline_voice_input(self):
        assembler = PromptAssembler()
        result = assembler.assemble("Line 1\nLine 2\nLine 3")
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
