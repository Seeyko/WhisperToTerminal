"""
Context capture module.

Captures context from the active window including:
- Window title and process name
- Application type detection (IDE, browser, terminal, etc.)
- File path extraction from window titles
- Selected text capture via clipboard
- Browser URL extraction via UI Automation
- IDE line number extraction
- Terminal working directory capture
"""

import re
import time
from typing import Optional, Any

import psutil
import pyperclip
import win32api
import win32clipboard
import win32con
import win32gui
import win32process

from .types import AppType, SelectedText, WindowContext

# UI Automation imports (optional, for deeper context)
try:
    import comtypes
    import comtypes.client
    UI_AUTOMATION_AVAILABLE = True
except ImportError:
    UI_AUTOMATION_AVAILABLE = False


# Process name to app type mapping
APP_TYPE_MAPPING = {
    # IDEs
    "code.exe": AppType.IDE,
    "code - insiders.exe": AppType.IDE,
    "devenv.exe": AppType.IDE,
    "idea64.exe": AppType.IDE,
    "pycharm64.exe": AppType.IDE,
    "webstorm64.exe": AppType.IDE,
    "rider64.exe": AppType.IDE,
    "goland64.exe": AppType.IDE,
    "clion64.exe": AppType.IDE,
    "rubymine64.exe": AppType.IDE,
    "phpstorm64.exe": AppType.IDE,
    "cursor.exe": AppType.IDE,
    "windsurf.exe": AppType.IDE,
    "zed.exe": AppType.IDE,
    # Browsers
    "chrome.exe": AppType.BROWSER,
    "firefox.exe": AppType.BROWSER,
    "msedge.exe": AppType.BROWSER,
    "brave.exe": AppType.BROWSER,
    "opera.exe": AppType.BROWSER,
    "vivaldi.exe": AppType.BROWSER,
    "arc.exe": AppType.BROWSER,
    # Terminals
    "windowsterminal.exe": AppType.TERMINAL,
    "cmd.exe": AppType.TERMINAL,
    "powershell.exe": AppType.TERMINAL,
    "pwsh.exe": AppType.TERMINAL,
    "wt.exe": AppType.TERMINAL,
    "conhost.exe": AppType.TERMINAL,
    "mintty.exe": AppType.TERMINAL,
    "alacritty.exe": AppType.TERMINAL,
    "wezterm-gui.exe": AppType.TERMINAL,
    "hyper.exe": AppType.TERMINAL,
    # Text Editors
    "notepad.exe": AppType.EDITOR,
    "notepad++.exe": AppType.EDITOR,
    "sublime_text.exe": AppType.EDITOR,
    "atom.exe": AppType.EDITOR,
    # File Explorer
    "explorer.exe": AppType.EXPLORER,
    # Office
    "winword.exe": AppType.OFFICE,
    "excel.exe": AppType.OFFICE,
    "powerpnt.exe": AppType.OFFICE,
    "onenote.exe": AppType.OFFICE,
    "outlook.exe": AppType.OFFICE,
}

# Regex patterns for file path extraction from window titles
FILE_PATH_PATTERNS = [
    (r"^(.+?)\s+-\s+(.+?)\s+-\s+Visual Studio Code", "vscode"),
    (r"^(.+?)\s+-\s+(.+?)\s+-\s+Cursor", "cursor"),
    (r"^(.+?)\s+-\s+(.+?)\s+-\s+Windsurf", "windsurf"),
    (r"^(.+?)\s+-\s+(.+?)\s+-\s+\[(.+?)\]", "jetbrains"),
    (r"^(.+?)\s+-\s+Notepad\+\+", "notepadpp"),
    (r"^\*?(.+?)\s+-\s+Notepad$", "notepad"),
    (r"^(.+?)\s+-\s+Sublime Text", "sublime"),
    (r"^(.+?)\s+-\s+(.+?)\s+-\s+Microsoft Visual Studio", "visualstudio"),
    (r"([A-Za-z]:\\[^<>:\"|\?\*]+\.\w+)", "generic_path"),
]

# Browser URL patterns from window titles
BROWSER_URL_PATTERNS = [
    (r"^(.+?)\s+-\s+Google Chrome$", "chrome"),
    (r"^(.+?)\s+-\s+Microsoft Edge$", "edge"),
    (r"^(.+?)\s+-\s+Mozilla Firefox$", "firefox"),
    (r"^(.+?)\s+-\s+Brave$", "brave"),
]

# Terminal title patterns for CWD extraction
TERMINAL_CWD_PATTERNS = [
    (r"(?:Administrator:\s*)?([A-Za-z]:\\[^<>:\"|\?\*]*)", "wt"),
    (r"PS\s+([A-Za-z]:\\[^>]+)>?", "powershell"),
    (r"MINGW\d*:(/[^\s]+)", "gitbash"),
]


class ClipboardManager:
    """Manages clipboard state for preserving and restoring content."""

    CF_TEXT = win32con.CF_TEXT
    CF_UNICODETEXT = win32con.CF_UNICODETEXT
    CF_HDROP = win32con.CF_HDROP

    def __init__(self):
        self._saved_data: dict[int, Any] = {}
        self._has_saved = False

    def save(self) -> bool:
        """Save current clipboard contents."""
        self._saved_data = {}
        self._has_saved = False

        try:
            win32clipboard.OpenClipboard()
            try:
                if win32clipboard.IsClipboardFormatAvailable(self.CF_UNICODETEXT):
                    self._saved_data[self.CF_UNICODETEXT] = win32clipboard.GetClipboardData(
                        self.CF_UNICODETEXT
                    )
                elif win32clipboard.IsClipboardFormatAvailable(self.CF_TEXT):
                    self._saved_data[self.CF_TEXT] = win32clipboard.GetClipboardData(
                        self.CF_TEXT
                    )
                self._has_saved = True
                return True
            finally:
                win32clipboard.CloseClipboard()
        except Exception:
            return False

    def restore(self) -> bool:
        """Restore previously saved clipboard contents."""
        if not self._has_saved:
            return False

        try:
            win32clipboard.OpenClipboard()
            try:
                win32clipboard.EmptyClipboard()
                for fmt, data in self._saved_data.items():
                    if data is not None:
                        win32clipboard.SetClipboardData(fmt, data)
                return True
            finally:
                win32clipboard.CloseClipboard()
        except Exception:
            return False

    def clear_saved(self):
        """Clear saved clipboard data."""
        self._saved_data = {}
        self._has_saved = False


def _send_copy_command():
    """Send Ctrl+C to copy selected text."""
    VK_CONTROL = 0x11
    VK_C = 0x43
    KEYEVENTF_KEYUP = 0x0002

    win32api.keybd_event(VK_CONTROL, 0, 0, 0)
    win32api.keybd_event(VK_C, 0, 0, 0)
    win32api.keybd_event(VK_C, 0, KEYEVENTF_KEYUP, 0)
    win32api.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)


def capture_selected_text(
    preserve_clipboard: bool = True,
    timeout_ms: int = 200
) -> Optional[SelectedText]:
    """
    Capture currently selected text from any application.

    Args:
        preserve_clipboard: If True, save and restore original clipboard.
        timeout_ms: Time to wait for clipboard update in milliseconds.

    Returns:
        SelectedText object with captured text, or None if no selection.
    """
    clipboard_mgr = ClipboardManager()

    try:
        if preserve_clipboard:
            clipboard_mgr.save()

        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.CloseClipboard()
        except Exception:
            pass

        time.sleep(0.05)
        _send_copy_command()
        time.sleep(timeout_ms / 1000.0)

        try:
            text = pyperclip.paste()
        except Exception:
            text = None

        if text and text.strip():
            return SelectedText(text=text, source="clipboard")

        return None

    finally:
        if preserve_clipboard:
            time.sleep(0.05)
            clipboard_mgr.restore()


def detect_application_type(process_name: str, window_title: str = "") -> AppType:
    """Detect the application type from process name and window title."""
    if process_name in APP_TYPE_MAPPING:
        return APP_TYPE_MAPPING[process_name]

    title_lower = window_title.lower()

    if any(kw in title_lower for kw in ["visual studio code", "vscode", "cursor", "windsurf"]):
        return AppType.IDE
    if any(kw in title_lower for kw in ["intellij", "pycharm", "webstorm", "rider"]):
        return AppType.IDE
    if any(kw in title_lower for kw in ["chrome", "firefox", "edge", "brave", "safari"]):
        return AppType.BROWSER
    if any(kw in title_lower for kw in ["powershell", "command prompt", "terminal", "bash", "cmd"]):
        return AppType.TERMINAL

    return AppType.UNKNOWN


def extract_file_path(window_title: str, process_name: str = "") -> Optional[dict]:
    """Extract file path information from a window title."""
    result = {"file_path": None, "line_number": None, "extra": {}}

    for pattern, source in FILE_PATH_PATTERNS:
        match = re.search(pattern, window_title, re.IGNORECASE)
        if match:
            groups = match.groups()

            if source in ["vscode", "cursor", "windsurf"]:
                filename = groups[0].strip()
                folder_path = groups[1].strip() if len(groups) > 1 else ""
                if re.match(r"^[A-Za-z]:\\", folder_path):
                    result["file_path"] = f"{folder_path}\\{filename}"
                else:
                    result["extra"]["filename"] = filename
                    result["extra"]["folder"] = folder_path

            elif source == "jetbrains":
                filename = groups[0].strip()
                project = groups[1].strip() if len(groups) > 1 else ""
                path = groups[2].strip() if len(groups) > 2 else ""
                if path:
                    result["file_path"] = path
                result["extra"]["filename"] = filename
                result["extra"]["project"] = project

            elif source in ["notepadpp", "notepad", "sublime"]:
                file_info = groups[0].strip().lstrip("*").strip()
                if re.match(r"^[A-Za-z]:\\", file_info):
                    result["file_path"] = file_info
                else:
                    result["extra"]["filename"] = file_info

            elif source == "visualstudio":
                filename = groups[0].strip()
                project = groups[1].strip() if len(groups) > 1 else ""
                result["extra"]["filename"] = filename
                result["extra"]["project"] = project

            elif source == "generic_path":
                result["file_path"] = groups[0].strip()

            return result if (result["file_path"] or result["extra"]) else None

    return None


def extract_browser_info(window_title: str) -> Optional[dict]:
    """Extract browser information from window title."""
    for pattern, browser in BROWSER_URL_PATTERNS:
        match = re.match(pattern, window_title, re.IGNORECASE)
        if match:
            page_title = match.group(1).strip()
            return {
                "url": None,
                "extra": {"page_title": page_title, "browser": browser}
            }
    return None


def extract_terminal_info(window_title: str) -> Optional[dict]:
    """Extract terminal information from window title."""
    for pattern, terminal_type in TERMINAL_CWD_PATTERNS:
        match = re.search(pattern, window_title)
        if match:
            cwd = match.group(1).strip()

            if terminal_type == "gitbash" and cwd.startswith("/"):
                if len(cwd) >= 2 and cwd[0] == "/" and cwd[1].isalpha():
                    drive = cwd[1].upper()
                    rest = cwd[2:].replace("/", "\\") if len(cwd) > 2 else ""
                    cwd = f"{drive}:{rest}"

            return {"cwd": cwd, "extra": {"terminal_type": terminal_type}}

    return None


# UI Automation functions

def _init_ui_automation():
    """Initialize UI Automation COM interface."""
    if not UI_AUTOMATION_AVAILABLE:
        return None

    try:
        comtypes.CoInitialize()
        uia = comtypes.client.CreateObject(
            "{ff48dba4-60ef-4201-aa87-54103eef594e}",
            interface=comtypes.gen.UIAutomationClient.IUIAutomation
        )
        return uia
    except Exception:
        return None


def extract_browser_url(hwnd: int, process_name: str) -> Optional[str]:
    """Extract the current URL from a browser window using UI Automation."""
    if not UI_AUTOMATION_AVAILABLE:
        return None

    try:
        uia = _init_ui_automation()
        if not uia:
            return None

        element = uia.ElementFromHandle(hwnd)
        if not element:
            return None

        condition = uia.CreatePropertyCondition(30003, 50004)
        address_bar = element.FindFirst(4, condition)

        if address_bar:
            try:
                value_pattern = address_bar.GetCurrentPattern(10002)
                if value_pattern:
                    url = value_pattern.CurrentValue
                    if url and (url.startswith("http") or url.startswith("file://")):
                        return url
            except Exception:
                pass

            try:
                name = address_bar.CurrentName
                if name and (name.startswith("http") or "://" in name):
                    return name
            except Exception:
                pass

        return None
    except Exception:
        return None


def extract_ide_line_info(window_title: str, process_name: str) -> Optional[dict]:
    """Extract line number information from IDE window titles."""
    result = {"line_number": None, "column": None}

    match = re.search(r"\[Line\s+(\d+),?\s*Col\.?\s*(\d+)?\]", window_title, re.IGNORECASE)
    if match:
        result["line_number"] = int(match.group(1))
        if match.group(2):
            result["column"] = int(match.group(2))
        return result

    match = re.search(r":(\d+)(?::(\d+))?\s*[-–]", window_title)
    if match:
        result["line_number"] = int(match.group(1))
        if match.group(2):
            result["column"] = int(match.group(2))
        return result

    match = re.search(r"Ln\s+(\d+),?\s*Col\s+(\d+)", window_title, re.IGNORECASE)
    if match:
        result["line_number"] = int(match.group(1))
        result["column"] = int(match.group(2))
        return result

    return None if not result["line_number"] else result


def extract_vscode_context(window_title: str) -> Optional[dict]:
    """Extract detailed context from VSCode/Cursor/Windsurf window title."""
    result = {
        "filename": None,
        "folder": None,
        "line_number": None,
        "is_dirty": False,
        "workspace_type": None,
    }

    if window_title.startswith("● ") or window_title.startswith("• "):
        result["is_dirty"] = True
        window_title = window_title[2:]

    patterns = [
        r"^(.+?):(\d+)?\s+-\s+(.+?)\s+-\s+(Visual Studio Code|Cursor|Windsurf)",
        r"^(.+?)\s+-\s+(.+?)\s+-\s+(Visual Studio Code|Cursor|Windsurf)",
    ]

    for pattern in patterns:
        match = re.match(pattern, window_title)
        if match:
            groups = match.groups()
            if len(groups) == 4:
                result["filename"] = groups[0].strip()
                result["line_number"] = int(groups[1]) if groups[1] else None
                result["folder"] = groups[2].strip()
            elif len(groups) == 3:
                result["filename"] = groups[0].strip()
                result["folder"] = groups[1].strip()
            return result

    return None


def extract_terminal_context_deep(hwnd: int, window_title: str, process_name: str) -> Optional[dict]:
    """Extract deeper terminal context."""
    result = {"cwd": None, "shell": None, "terminal_app": None, "is_admin": False}

    terminal_apps = {
        "windowsterminal.exe": "Windows Terminal",
        "wt.exe": "Windows Terminal",
        "cmd.exe": "Command Prompt",
        "powershell.exe": "PowerShell",
        "pwsh.exe": "PowerShell Core",
        "mintty.exe": "Git Bash",
        "alacritty.exe": "Alacritty",
        "wezterm-gui.exe": "WezTerm",
        "hyper.exe": "Hyper",
    }
    result["terminal_app"] = terminal_apps.get(process_name, process_name)

    if "Administrator" in window_title or "admin" in window_title.lower():
        result["is_admin"] = True

    basic_info = extract_terminal_info(window_title)
    if basic_info:
        result["cwd"] = basic_info.get("cwd")
        result["shell"] = basic_info.get("extra", {}).get("terminal_type")

    if "PowerShell" in window_title:
        result["shell"] = "powershell"
    elif "MINGW" in window_title or "Git" in window_title.lower():
        result["shell"] = "bash"
    elif "Command Prompt" in window_title or "cmd" in window_title.lower():
        result["shell"] = "cmd"

    return result if result["cwd"] or result["shell"] else None


def get_full_context(
    hwnd: int,
    window_title: str,
    process_name: str,
    app_type: AppType
) -> dict:
    """Get comprehensive context using all available methods."""
    context = {"file_path": None, "url": None, "line_number": None, "column": None, "extra": {}}

    if app_type == AppType.IDE or app_type == AppType.EDITOR:
        if any(ide in process_name for ide in ["code", "cursor", "windsurf"]):
            vscode_ctx = extract_vscode_context(window_title)
            if vscode_ctx:
                context["extra"].update({k: v for k, v in vscode_ctx.items() if v is not None})
                if vscode_ctx.get("line_number"):
                    context["line_number"] = vscode_ctx["line_number"]

        file_info = extract_file_path(window_title, process_name)
        if file_info:
            context["file_path"] = file_info.get("file_path")
            context["extra"].update(file_info.get("extra", {}))

        line_info = extract_ide_line_info(window_title, process_name)
        if line_info:
            if line_info.get("line_number"):
                context["line_number"] = line_info["line_number"]
            if line_info.get("column"):
                context["column"] = line_info["column"]

    elif app_type == AppType.BROWSER:
        url = extract_browser_url(hwnd, process_name)
        if url:
            context["url"] = url

        browser_info = extract_browser_info(window_title)
        if browser_info:
            context["extra"].update(browser_info.get("extra", {}))

    elif app_type == AppType.TERMINAL:
        terminal_ctx = extract_terminal_context_deep(hwnd, window_title, process_name)
        if terminal_ctx:
            context["file_path"] = terminal_ctx.get("cwd")
            context["extra"]["shell"] = terminal_ctx.get("shell")
            context["extra"]["terminal_app"] = terminal_ctx.get("terminal_app")
            context["extra"]["is_admin"] = terminal_ctx.get("is_admin")

    return context


def get_active_window_info(
    capture_selection: bool = False,
    preserve_clipboard: bool = True,
    deep_context: bool = True
) -> Optional[WindowContext]:
    """
    Get information about the currently active window.

    Args:
        capture_selection: If True, also capture selected text via Ctrl+C.
        preserve_clipboard: If True, preserve original clipboard when capturing.
        deep_context: If True, use UI Automation for deeper context extraction.

    Returns:
        WindowContext with comprehensive window information, or None if failed.
    """
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None

        window_title = win32gui.GetWindowText(hwnd)
        if not window_title:
            return None

        _, process_id = win32process.GetWindowThreadProcessId(hwnd)

        try:
            process = psutil.Process(process_id)
            process_name = process.name().lower()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            process_name = "unknown"

        app_type = detect_application_type(process_name, window_title)

        file_path = None
        url = None
        line_number = None
        selected_text = None
        extra = {}

        if deep_context:
            full_ctx = get_full_context(hwnd, window_title, process_name, app_type)
            file_path = full_ctx.get("file_path")
            url = full_ctx.get("url")
            line_number = full_ctx.get("line_number")
            extra = full_ctx.get("extra", {})
            if full_ctx.get("column"):
                extra["column"] = full_ctx["column"]
        else:
            if app_type == AppType.IDE or app_type == AppType.EDITOR:
                file_info = extract_file_path(window_title, process_name)
                if file_info:
                    file_path = file_info.get("file_path")
                    line_number = file_info.get("line_number")
                    extra = file_info.get("extra", {})
            elif app_type == AppType.BROWSER:
                url_info = extract_browser_info(window_title)
                if url_info:
                    url = url_info.get("url")
                    extra = url_info.get("extra", {})
            elif app_type == AppType.TERMINAL:
                terminal_info = extract_terminal_info(window_title)
                if terminal_info:
                    file_path = terminal_info.get("cwd")
                    extra = terminal_info.get("extra", {})

        if capture_selection:
            selected_text = capture_selected_text(preserve_clipboard=preserve_clipboard)

        return WindowContext(
            window_handle=hwnd,
            window_title=window_title,
            process_name=process_name,
            process_id=process_id,
            app_type=app_type,
            file_path=file_path,
            url=url,
            line_number=line_number,
            selected_text=selected_text,
            extra=extra,
        )

    except Exception:
        return None


def get_context_summary(context: Optional[WindowContext]) -> str:
    """Generate a human-readable summary of the window context."""
    if not context:
        return "No active window context available."

    lines = [
        f"Application: {context.process_name} ({context.app_type.value})",
        f"Window: {context.window_title}",
    ]

    if context.file_path:
        lines.append(f"File: {context.file_path}")
    if context.line_number:
        lines.append(f"Line: {context.line_number}")
    if context.url:
        lines.append(f"URL: {context.url}")

    if context.selected_text:
        text_preview = context.selected_text.text[:100]
        if len(context.selected_text.text) > 100:
            text_preview += "..."
        lines.append(f"Selected: {context.selected_text.char_count} chars, {context.selected_text.line_count} lines")
        lines.append(f"Preview: {text_preview}")

    if context.extra:
        for key, value in context.extra.items():
            lines.append(f"{key.capitalize()}: {value}")

    return "\n".join(lines)
