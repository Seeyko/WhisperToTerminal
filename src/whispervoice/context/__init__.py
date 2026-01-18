"""Context capture and monitoring modules."""

from .types import AppType, SelectedText, WindowContext
from .capture import (
    get_active_window_info,
    capture_selected_text,
    detect_application_type,
    extract_file_path,
    extract_browser_info,
    extract_terminal_info,
    extract_browser_url,
    extract_ide_line_info,
    extract_vscode_context,
    extract_terminal_context_deep,
    get_full_context,
    get_context_summary,
    ClipboardManager,
    UI_AUTOMATION_AVAILABLE,
)
from .monitor import ContextMonitor, ContextTimeline, ContextEvent, EventType, format_timeline_for_prompt

__all__ = [
    # Types
    "AppType",
    "SelectedText",
    "WindowContext",
    # Capture
    "get_active_window_info",
    "capture_selected_text",
    "detect_application_type",
    "extract_file_path",
    "extract_browser_info",
    "extract_terminal_info",
    "extract_browser_url",
    "extract_ide_line_info",
    "extract_vscode_context",
    "extract_terminal_context_deep",
    "get_full_context",
    "get_context_summary",
    "ClipboardManager",
    "UI_AUTOMATION_AVAILABLE",
    # Monitor
    "ContextMonitor",
    "ContextTimeline",
    "ContextEvent",
    "EventType",
    "format_timeline_for_prompt",
]
