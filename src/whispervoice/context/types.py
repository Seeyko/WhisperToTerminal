"""
Data types for context capture.

Contains dataclasses and enums used throughout the context module.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class AppType(Enum):
    """Application type classification."""
    IDE = "ide"
    BROWSER = "browser"
    TERMINAL = "terminal"
    EDITOR = "editor"
    EXPLORER = "explorer"
    OFFICE = "office"
    UNKNOWN = "unknown"


@dataclass
class SelectedText:
    """Information about selected/highlighted text."""
    text: str
    source: str  # "clipboard", "uiautomation"
    char_count: int = 0
    line_count: int = 0

    def __post_init__(self):
        if self.text:
            self.char_count = len(self.text)
            self.line_count = self.text.count('\n') + 1

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "text": self.text,
            "source": self.source,
            "char_count": self.char_count,
            "line_count": self.line_count,
        }


@dataclass
class WindowContext:
    """Context information from the active window."""
    window_handle: int
    window_title: str
    process_name: str
    process_id: int
    app_type: AppType
    file_path: Optional[str] = None
    url: Optional[str] = None
    line_number: Optional[int] = None
    selected_text: Optional[SelectedText] = None
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "window_title": self.window_title,
            "process_name": self.process_name,
            "process_id": self.process_id,
            "app_type": self.app_type.value,
            "file_path": self.file_path,
            "url": self.url,
            "line_number": self.line_number,
            "selected_text": self.selected_text.to_dict() if self.selected_text else None,
            "extra": self.extra,
        }
