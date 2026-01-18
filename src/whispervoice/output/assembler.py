"""
Prompt Assembler Module for WhisperVoice.

Assembles captured context into formatted prompts for AI assistants.
Supports customizable templates and smart formatting based on context type.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from string import Template
from typing import Optional

from ..context.types import WindowContext, AppType, SelectedText


# Default templates for different contexts
DEFAULT_TEMPLATES = {
    "default": """## Voice Input
$voice_input

$context_section$selected_section""",

    "ide": """## Voice Input
$voice_input

## Context
- **Application**: $app_name
- **File**: `$file_path`$line_info
$extra_context
$selected_section""",

    "browser": """## Voice Input
$voice_input

## Context
- **Application**: $app_name ($browser_type)
- **Page**: $page_title
$url_info
$selected_section""",

    "terminal": """## Voice Input
$voice_input

## Context
- **Application**: $app_name ($terminal_type)
- **Working Directory**: `$cwd`
$selected_section""",

    "minimal": """$voice_input

---
Context: $app_name | $file_or_url
$selected_section""",

    "code_review": """## Code Review Request
$voice_input

## File Information
- **File**: `$file_path`
- **Application**: $app_name

## Code to Review
$selected_section""",

    "bug_report": """## Bug Report
$voice_input

## Environment
- **Application**: $app_name
- **File**: `$file_path`$line_info

## Relevant Code
$selected_section""",
}


@dataclass
class PromptConfig:
    """Configuration for prompt assembly."""
    template_name: str = "default"
    custom_template: Optional[str] = None
    include_context: bool = True
    include_selection: bool = True
    code_block_lang: str = ""
    max_selection_chars: int = 10000
    extra_fields: dict = field(default_factory=dict)


class PromptAssembler:
    """
    Assembles prompts from voice input and context.

    Supports multiple template types and smart formatting
    based on the application type.
    """

    def __init__(self, config: Optional[PromptConfig] = None):
        self.config = config or PromptConfig()
        self.templates = DEFAULT_TEMPLATES.copy()
        self._load_user_templates()

    def _load_user_templates(self):
        """Load user-defined templates from config file."""
        config_paths = [
            Path.home() / ".whispervoice" / "templates.json",
            Path.home() / ".config" / "whispervoice" / "templates.json",
            Path("templates.json"),
        ]

        for config_path in config_paths:
            if config_path.exists():
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        user_templates = json.load(f)
                        self.templates.update(user_templates)
                except Exception:
                    pass
                break

    def _detect_code_language(self, context: Optional[WindowContext]) -> str:
        """Detect programming language from file extension or context."""
        if not context:
            return ""

        file_path = context.file_path or context.extra.get("filename", "")
        if not file_path:
            return ""

        ext_to_lang = {
            ".py": "python", ".js": "javascript", ".ts": "typescript",
            ".tsx": "tsx", ".jsx": "jsx", ".java": "java", ".kt": "kotlin",
            ".go": "go", ".rs": "rust", ".rb": "ruby", ".php": "php",
            ".cs": "csharp", ".cpp": "cpp", ".c": "c", ".h": "c",
            ".hpp": "cpp", ".swift": "swift", ".scala": "scala", ".r": "r",
            ".sql": "sql", ".sh": "bash", ".bash": "bash", ".zsh": "zsh",
            ".ps1": "powershell", ".html": "html", ".css": "css",
            ".scss": "scss", ".sass": "sass", ".less": "less",
            ".json": "json", ".yaml": "yaml", ".yml": "yaml",
            ".xml": "xml", ".md": "markdown", ".toml": "toml",
            ".ini": "ini", ".cfg": "ini", ".dockerfile": "dockerfile",
            ".vue": "vue", ".svelte": "svelte",
        }

        ext = Path(file_path).suffix.lower()
        return ext_to_lang.get(ext, "")

    def _select_template(self, context: Optional[WindowContext]) -> str:
        """Select the best template based on context and config."""
        if self.config.custom_template:
            return self.config.custom_template

        if not self.config.include_context:
            return """## Voice Input
$voice_input
$selected_section"""

        template_name = self.config.template_name

        if template_name in ("auto", "default") and context:
            if context.app_type == AppType.IDE:
                template_name = "ide"
            elif context.app_type == AppType.BROWSER:
                template_name = "browser"
            elif context.app_type == AppType.TERMINAL:
                template_name = "terminal"
            elif context.app_type == AppType.EDITOR:
                template_name = "ide"

        return self.templates.get(template_name, self.templates["default"])

    def _format_selected_text(self, selected: Optional[SelectedText], lang: str = "") -> str:
        """Format selected text as a code block."""
        if not selected or not selected.text:
            return ""

        text = selected.text

        if len(text) > self.config.max_selection_chars:
            text = text[:self.config.max_selection_chars]
            text += f"\n... (truncated, {selected.char_count - self.config.max_selection_chars} more chars)"

        return f"## Selected Code\n```{lang}\n{text}\n```"

    def _build_context_section(self, context: WindowContext) -> str:
        """Build the context section from WindowContext."""
        lines = ["## Context"]

        app_name = context.process_name.replace(".exe", "").title()
        lines.append(f"- **Application**: {app_name}")

        if context.file_path:
            lines.append(f"- **File**: `{context.file_path}`")
        elif context.extra.get("filename"):
            folder = context.extra.get("folder", "")
            filename = context.extra.get("filename")
            if folder:
                lines.append(f"- **File**: `{filename}` in `{folder}`")
            else:
                lines.append(f"- **File**: `{filename}`")

        if context.line_number:
            lines.append(f"- **Line**: {context.line_number}")

        if context.url:
            lines.append(f"- **URL**: {context.url}")
        elif context.extra.get("page_title"):
            lines.append(f"- **Page**: {context.extra['page_title']}")

        if context.app_type == AppType.TERMINAL:
            if context.extra.get("terminal_type"):
                lines.append(f"- **Shell**: {context.extra['terminal_type']}")

        if context.extra.get("project"):
            lines.append(f"- **Project**: {context.extra['project']}")

        return "\n".join(lines) + "\n"

    def assemble(self, voice_input: str, context: Optional[WindowContext] = None) -> str:
        """
        Assemble a formatted prompt from voice input and context.

        Args:
            voice_input: The transcribed voice input text.
            context: Optional WindowContext with app/file/selection info.

        Returns:
            Formatted prompt string ready for AI assistant.
        """
        template_str = self._select_template(context)
        lang = self.config.code_block_lang or self._detect_code_language(context)

        variables = {
            "voice_input": voice_input.strip(),
            "context_section": "",
            "selected_section": "",
            "app_name": "",
            "file_path": "",
            "file_or_url": "",
            "line_info": "",
            "url_info": "",
            "page_title": "",
            "browser_type": "",
            "terminal_type": "",
            "cwd": "",
            "extra_context": "",
        }

        if context and self.config.include_context:
            variables["app_name"] = context.process_name.replace(".exe", "").title()

            if context.file_path:
                variables["file_path"] = context.file_path
                variables["file_or_url"] = context.file_path
            elif context.extra.get("filename"):
                folder = context.extra.get("folder", "")
                filename = context.extra.get("filename")
                variables["file_path"] = f"{filename}" + (f" ({folder})" if folder else "")
                variables["file_or_url"] = variables["file_path"]

            if context.line_number:
                variables["line_info"] = f"\n- **Line**: {context.line_number}"

            if context.url:
                variables["url_info"] = f"\n- **URL**: {context.url}"
                variables["file_or_url"] = context.url
            if context.extra.get("page_title"):
                variables["page_title"] = context.extra["page_title"]
                if not variables["file_or_url"]:
                    variables["file_or_url"] = context.extra["page_title"]
            if context.extra.get("browser"):
                variables["browser_type"] = context.extra["browser"]

            if context.extra.get("terminal_type"):
                variables["terminal_type"] = context.extra["terminal_type"]
            if context.app_type == AppType.TERMINAL and context.file_path:
                variables["cwd"] = context.file_path

            extra_lines = []
            if context.extra.get("project"):
                extra_lines.append(f"- **Project**: {context.extra['project']}")
            variables["extra_context"] = "\n".join(extra_lines)

            variables["context_section"] = self._build_context_section(context)

            if self.config.include_selection and context.selected_text:
                variables["selected_section"] = self._format_selected_text(
                    context.selected_text, lang
                )

        try:
            template = Template(template_str)
            result = template.safe_substitute(variables)
        except Exception:
            result = f"## Voice Input\n{voice_input}"
            if context and context.selected_text:
                result += f"\n\n{variables['selected_section']}"

        result = "\n".join(line for line in result.split("\n") if line.strip() or line == "")
        result = result.strip()

        return result

    def list_templates(self) -> list[str]:
        """Return list of available template names."""
        return list(self.templates.keys())

    def get_template(self, name: str) -> Optional[str]:
        """Get a template by name."""
        return self.templates.get(name)

    def add_template(self, name: str, template: str):
        """Add or update a template."""
        self.templates[name] = template


def assemble_prompt(
    voice_input: str,
    context: Optional[WindowContext] = None,
    template_name: str = "default",
) -> str:
    """Convenience function to assemble a prompt."""
    config = PromptConfig(template_name=template_name)
    assembler = PromptAssembler(config)
    return assembler.assemble(voice_input, context)
