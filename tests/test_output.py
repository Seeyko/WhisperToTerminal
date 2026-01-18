#!/usr/bin/env python3
"""Unit tests for prompt assembler module."""

import pytest
from whispervoice.context.types import AppType, WindowContext, SelectedText
from whispervoice.output import PromptAssembler, PromptConfig, assemble_prompt


class TestPromptAssembler:
    """Tests for PromptAssembler class."""

    def test_basic_assembly(self):
        assembler = PromptAssembler()
        result = assembler.assemble("Hello world")
        assert "## Voice Input" in result
        assert "Hello world" in result

    def test_assembly_with_ide_context(self):
        selected = SelectedText(text="print('hello')", source="clipboard")
        context = WindowContext(
            window_handle=1,
            window_title="test.py - project - Visual Studio Code",
            process_name="code.exe",
            process_id=1,
            app_type=AppType.IDE,
            file_path="C:\\project\\test.py",
            selected_text=selected,
        )
        assembler = PromptAssembler()
        result = assembler.assemble("Explain this code", context)

        assert "## Voice Input" in result
        assert "Explain this code" in result
        assert "Code" in result
        assert "test.py" in result
        assert "print('hello')" in result
        assert "```python" in result

    def test_assembly_with_browser_context(self):
        context = WindowContext(
            window_handle=1,
            window_title="GitHub - Google Chrome",
            process_name="chrome.exe",
            process_id=1,
            app_type=AppType.BROWSER,
            url="https://github.com",
            extra={"page_title": "GitHub", "browser": "chrome"},
        )
        assembler = PromptAssembler()
        result = assembler.assemble("What is this website?", context)

        assert "## Voice Input" in result
        assert "What is this website?" in result
        assert "Chrome" in result

    def test_assembly_with_terminal_context(self):
        context = WindowContext(
            window_handle=1,
            window_title="C:\\Users\\test",
            process_name="windowsterminal.exe",
            process_id=1,
            app_type=AppType.TERMINAL,
            file_path="C:\\Users\\test",
            extra={"terminal_type": "wt"},
        )
        assembler = PromptAssembler()
        result = assembler.assemble("List files here", context)

        assert "## Voice Input" in result
        assert "List files here" in result

    def test_auto_template_selection_ide(self):
        context = WindowContext(
            window_handle=1,
            window_title="test.py - VSCode",
            process_name="code.exe",
            process_id=1,
            app_type=AppType.IDE,
            file_path="test.py",
        )
        config = PromptConfig(template_name="auto")
        assembler = PromptAssembler(config)
        result = assembler.assemble("Test", context)

        assert "File" in result

    def test_auto_template_selection_browser(self):
        context = WindowContext(
            window_handle=1,
            window_title="Test - Chrome",
            process_name="chrome.exe",
            process_id=1,
            app_type=AppType.BROWSER,
            extra={"page_title": "Test", "browser": "chrome"},
        )
        config = PromptConfig(template_name="auto")
        assembler = PromptAssembler(config)
        result = assembler.assemble("Test", context)

        assert "Chrome" in result

    def test_minimal_template(self):
        context = WindowContext(
            window_handle=1,
            window_title="test.py - VSCode",
            process_name="code.exe",
            process_id=1,
            app_type=AppType.IDE,
            file_path="test.py",
        )
        config = PromptConfig(template_name="minimal")
        assembler = PromptAssembler(config)
        result = assembler.assemble("Quick question", context)

        assert "Quick question" in result
        assert "---" in result

    def test_code_review_template(self):
        selected = SelectedText(text="def foo(): pass", source="clipboard")
        context = WindowContext(
            window_handle=1,
            window_title="test.py - VSCode",
            process_name="code.exe",
            process_id=1,
            app_type=AppType.IDE,
            file_path="test.py",
            selected_text=selected,
        )
        config = PromptConfig(template_name="code_review")
        assembler = PromptAssembler(config)
        result = assembler.assemble("Review this", context)

        assert "Code Review" in result
        assert "def foo(): pass" in result

    def test_bug_report_template(self):
        selected = SelectedText(text="error_line()", source="clipboard")
        context = WindowContext(
            window_handle=1,
            window_title="test.py - VSCode",
            process_name="code.exe",
            process_id=1,
            app_type=AppType.IDE,
            file_path="test.py",
            line_number=42,
            selected_text=selected,
        )
        config = PromptConfig(template_name="bug_report")
        assembler = PromptAssembler(config)
        result = assembler.assemble("Found a bug", context)

        assert "Bug Report" in result
        assert "42" in result

    def test_custom_template(self):
        config = PromptConfig(custom_template="CUSTOM: $voice_input")
        assembler = PromptAssembler(config)
        result = assembler.assemble("Test input")

        assert result == "CUSTOM: Test input"

    def test_exclude_context(self):
        context = WindowContext(
            window_handle=1,
            window_title="test.py - VSCode",
            process_name="code.exe",
            process_id=1,
            app_type=AppType.IDE,
            file_path="C:\\project\\test.py",
        )
        config = PromptConfig(include_context=False)
        assembler = PromptAssembler(config)
        result = assembler.assemble("Just voice", context)

        assert "Just voice" in result
        assert "C:\\project\\test.py" not in result

    def test_exclude_selection(self):
        selected = SelectedText(text="selected code", source="clipboard")
        context = WindowContext(
            window_handle=1,
            window_title="test.py - VSCode",
            process_name="code.exe",
            process_id=1,
            app_type=AppType.IDE,
            selected_text=selected,
        )
        config = PromptConfig(include_selection=False)
        assembler = PromptAssembler(config)
        result = assembler.assemble("Test", context)

        assert "selected code" not in result

    def test_truncate_long_selection(self):
        long_text = "x" * 15000
        selected = SelectedText(text=long_text, source="clipboard")
        context = WindowContext(
            window_handle=1,
            window_title="test.py - VSCode",
            process_name="code.exe",
            process_id=1,
            app_type=AppType.IDE,
            selected_text=selected,
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
            window_title="test.py - VSCode",
            process_name="code.exe",
            process_id=1,
            app_type=AppType.IDE,
            file_path="test.py",
            selected_text=SelectedText(text="print('hi')", source="clipboard"),
        )
        assembler = PromptAssembler()
        result = assembler.assemble("Test", context)

        assert "```python" in result

    def test_typescript_detection(self):
        context = WindowContext(
            window_handle=1,
            window_title="app.ts - VSCode",
            process_name="code.exe",
            process_id=1,
            app_type=AppType.IDE,
            file_path="app.ts",
            selected_text=SelectedText(text="const x = 1;", source="clipboard"),
        )
        assembler = PromptAssembler()
        result = assembler.assemble("Test", context)

        assert "```typescript" in result

    def test_javascript_detection(self):
        context = WindowContext(
            window_handle=1,
            window_title="app.js - VSCode",
            process_name="code.exe",
            process_id=1,
            app_type=AppType.IDE,
            file_path="app.js",
            selected_text=SelectedText(text="let x = 1;", source="clipboard"),
        )
        assembler = PromptAssembler()
        result = assembler.assemble("Test", context)

        assert "```javascript" in result

    def test_rust_detection(self):
        context = WindowContext(
            window_handle=1,
            window_title="main.rs - VSCode",
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
            window_title="test.py - VSCode",
            process_name="code.exe",
            process_id=1,
            app_type=AppType.IDE,
            file_path="test.py",
            selected_text=SelectedText(text="code", source="clipboard"),
        )
        config = PromptConfig(code_block_lang="ruby")
        assembler = PromptAssembler(config)
        result = assembler.assemble("Test", context)

        assert "```ruby" in result


class TestListTemplates:
    """Tests for template listing."""

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
        assembler.add_template("custom", "CUSTOM: $voice_input")

        assert "custom" in assembler.list_templates()
        assert assembler.get_template("custom") == "CUSTOM: $voice_input"


class TestConvenienceFunction:
    """Tests for assemble_prompt convenience function."""

    def test_basic_usage(self):
        result = assemble_prompt("Hello")
        assert "Hello" in result

    def test_with_context(self):
        context = WindowContext(
            window_handle=1,
            window_title="test.py - VSCode",
            process_name="code.exe",
            process_id=1,
            app_type=AppType.IDE,
        )
        result = assemble_prompt("Hello", context)
        assert "Hello" in result

    def test_with_template_name(self):
        result = assemble_prompt("Hello", template_name="minimal")
        assert "Hello" in result
        assert "---" in result


class TestEdgeCases:
    """Tests for edge cases."""

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
            window_title="test.py - VSCode",
            process_name="code.exe",
            process_id=1,
            app_type=AppType.IDE,
        )
        assembler = PromptAssembler()
        result = assembler.assemble("Test", context)
        assert "Test" in result

    def test_special_characters_in_input(self):
        assembler = PromptAssembler()
        result = assembler.assemble("Test with $pecial & <chars>")
        assert "$pecial" in result or "pecial" in result

    def test_multiline_voice_input(self):
        assembler = PromptAssembler()
        result = assembler.assemble("Line 1\nLine 2\nLine 3")
        assert "Line 1" in result
        assert "Line 3" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
