#!/usr/bin/env python3
"""
Continuous Context Monitor for WhisperVoice

Monitors and tracks context changes while the user is recording:
- Window focus changes (switching between apps)
- Selection changes (when user selects new text)
- Builds a timeline of all context events

This allows the user to navigate between windows, select multiple
pieces of text, and have everything captured with timestamps.
"""

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Callable
from enum import Enum

import pyperclip
import win32gui
import win32clipboard

from context_capture import (
    get_active_window_info,
    WindowContext,
    AppType,
    SelectedText,
    ClipboardManager,
)


class EventType(Enum):
    """Types of context events."""
    RECORDING_START = "recording_start"
    RECORDING_STOP = "recording_stop"
    WINDOW_FOCUS = "window_focus"
    TEXT_SELECTION = "text_selection"
    CLIPBOARD_CHANGE = "clipboard_change"


@dataclass
class ContextEvent:
    """A single context event in the timeline."""
    timestamp: float  # Seconds since recording started
    event_type: EventType
    window_context: Optional[WindowContext] = None
    selected_text: Optional[str] = None
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "timestamp": round(self.timestamp, 2),
            "event_type": self.event_type.value,
            "description": self.description,
            "window": self.window_context.to_dict() if self.window_context else None,
            "selected_text": self.selected_text[:500] if self.selected_text else None,
        }


@dataclass
class ContextTimeline:
    """Timeline of all context events during a recording session."""
    events: list[ContextEvent] = field(default_factory=list)
    start_time: float = 0
    end_time: float = 0

    def add_event(self, event: ContextEvent):
        """Add an event to the timeline."""
        self.events.append(event)

    def get_all_selections(self) -> list[tuple[float, str, WindowContext]]:
        """Get all text selections with their timestamps and contexts."""
        selections = []
        for event in self.events:
            if event.event_type == EventType.TEXT_SELECTION and event.selected_text:
                selections.append((
                    event.timestamp,
                    event.selected_text,
                    event.window_context
                ))
        return selections

    def get_all_windows(self) -> list[tuple[float, WindowContext]]:
        """Get all window focus events."""
        windows = []
        for event in self.events:
            if event.event_type == EventType.WINDOW_FOCUS and event.window_context:
                windows.append((event.timestamp, event.window_context))
        return windows

    def to_markdown(self) -> str:
        """Convert timeline to markdown format."""
        if not self.events:
            return ""

        lines = ["## Context Timeline\n"]

        for event in self.events:
            time_str = f"[{event.timestamp:.1f}s]"

            if event.event_type == EventType.WINDOW_FOCUS:
                ctx = event.window_context
                if ctx:
                    app = ctx.process_name.replace(".exe", "").title()
                    file_info = ctx.file_path or ctx.extra.get("filename", "")
                    lines.append(f"- {time_str} Switched to **{app}**" +
                               (f" - `{file_info}`" if file_info else ""))

            elif event.event_type == EventType.TEXT_SELECTION:
                text_preview = event.selected_text[:50] if event.selected_text else ""
                if len(event.selected_text or "") > 50:
                    text_preview += "..."
                lines.append(f"- {time_str} Selected: \"{text_preview}\"")

            elif event.event_type == EventType.RECORDING_START:
                lines.append(f"- {time_str} Recording started")

            elif event.event_type == EventType.RECORDING_STOP:
                lines.append(f"- {time_str} Recording stopped")

        return "\n".join(lines)


class ContextMonitor:
    """
    Monitors context changes continuously during recording.

    Tracks:
    - Window focus changes (user switching between apps)
    - Text selections (via clipboard monitoring)
    - Builds a timeline of all events with timestamps
    """

    def __init__(self, poll_interval: float = 0.3):
        """
        Initialize the context monitor.

        Args:
            poll_interval: How often to check for changes (seconds)
        """
        self.poll_interval = poll_interval
        self.timeline = ContextTimeline()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._start_time = 0

        # State tracking
        self._last_window_handle = 0
        self._last_clipboard_content = ""
        self._clipboard_mgr = ClipboardManager()

    def start(self):
        """Start monitoring context changes."""
        if self._running:
            return

        self._running = True
        self._start_time = time.time()
        self.timeline = ContextTimeline()
        self.timeline.start_time = self._start_time

        # Capture initial state
        self._last_clipboard_content = self._get_clipboard_safe()
        self._last_window_handle = win32gui.GetForegroundWindow()

        # Record initial context
        initial_context = get_active_window_info(capture_selection=False)
        self.timeline.add_event(ContextEvent(
            timestamp=0,
            event_type=EventType.RECORDING_START,
            window_context=initial_context,
            description="Recording started"
        ))

        if initial_context:
            self.timeline.add_event(ContextEvent(
                timestamp=0,
                event_type=EventType.WINDOW_FOCUS,
                window_context=initial_context,
                description=f"Initial window: {initial_context.process_name}"
            ))

        # Start monitoring thread
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self) -> ContextTimeline:
        """
        Stop monitoring and return the timeline.

        Returns:
            ContextTimeline with all captured events
        """
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)

        self.timeline.end_time = time.time()

        # Record stop event
        elapsed = time.time() - self._start_time
        self.timeline.add_event(ContextEvent(
            timestamp=elapsed,
            event_type=EventType.RECORDING_STOP,
            description="Recording stopped"
        ))

        return self.timeline

    def _get_clipboard_safe(self) -> str:
        """Safely get clipboard content."""
        try:
            return pyperclip.paste() or ""
        except Exception:
            return ""

    def _get_elapsed(self) -> float:
        """Get elapsed time since recording started."""
        return time.time() - self._start_time

    def _monitor_loop(self):
        """Main monitoring loop - runs in background thread."""
        while self._running:
            try:
                self._check_window_change()
                self._check_clipboard_change()
            except Exception as e:
                # Don't crash the monitor on errors
                pass

            time.sleep(self.poll_interval)

    def _check_window_change(self):
        """Check if the active window has changed."""
        current_hwnd = win32gui.GetForegroundWindow()

        if current_hwnd != self._last_window_handle and current_hwnd != 0:
            self._last_window_handle = current_hwnd

            # Get context for new window
            context = get_active_window_info(capture_selection=False)
            if context:
                self.timeline.add_event(ContextEvent(
                    timestamp=self._get_elapsed(),
                    event_type=EventType.WINDOW_FOCUS,
                    window_context=context,
                    description=f"Switched to {context.process_name}"
                ))

    def _check_clipboard_change(self):
        """Check if clipboard content has changed (user selected new text)."""
        current_content = self._get_clipboard_safe()

        # Check if content changed and is not empty
        if (current_content and
            current_content != self._last_clipboard_content and
            len(current_content.strip()) > 0):

            self._last_clipboard_content = current_content

            # Get current window context
            context = get_active_window_info(capture_selection=False)

            self.timeline.add_event(ContextEvent(
                timestamp=self._get_elapsed(),
                event_type=EventType.TEXT_SELECTION,
                window_context=context,
                selected_text=current_content,
                description=f"Text selected ({len(current_content)} chars)"
            ))

    def get_timeline(self) -> ContextTimeline:
        """Get the current timeline (can be called while monitoring)."""
        return self.timeline


def format_timeline_for_prompt(timeline: ContextTimeline) -> str:
    """
    Format the timeline for inclusion in a prompt.

    Groups selections by window and formats them nicely.

    Args:
        timeline: The context timeline

    Returns:
        Formatted markdown string
    """
    if not timeline.events:
        return ""

    sections = []

    # Get unique windows and their selections
    window_selections: dict[str, list[tuple[float, str]]] = {}

    for event in timeline.events:
        if event.event_type == EventType.TEXT_SELECTION and event.selected_text:
            # Key by window info
            ctx = event.window_context
            if ctx:
                key = f"{ctx.process_name}|{ctx.file_path or ctx.extra.get('filename', 'unknown')}"
                if key not in window_selections:
                    window_selections[key] = []
                window_selections[key].append((event.timestamp, event.selected_text))

    # Format each window's selections
    for key, selections in window_selections.items():
        parts = key.split("|")
        app_name = parts[0].replace(".exe", "").title() if parts else "Unknown"
        file_name = parts[1] if len(parts) > 1 else ""

        section_lines = [f"### From {app_name}" + (f" - `{file_name}`" if file_name else "")]

        for timestamp, text in selections:
            # Detect language from file extension if possible
            lang = ""
            if file_name:
                ext_map = {
                    ".py": "python", ".js": "javascript", ".ts": "typescript",
                    ".tsx": "tsx", ".jsx": "jsx", ".java": "java", ".go": "go",
                    ".rs": "rust", ".rb": "ruby", ".php": "php", ".cs": "csharp",
                    ".cpp": "cpp", ".c": "c", ".sh": "bash", ".ps1": "powershell",
                    ".html": "html", ".css": "css", ".json": "json", ".yaml": "yaml",
                    ".sql": "sql", ".md": "markdown",
                }
                for ext, language in ext_map.items():
                    if file_name.endswith(ext):
                        lang = language
                        break

            section_lines.append(f"\n**[{timestamp:.1f}s]**")
            section_lines.append(f"```{lang}")
            section_lines.append(text.strip())
            section_lines.append("```")

        sections.append("\n".join(section_lines))

    if sections:
        return "## Selected Code/Text\n\n" + "\n\n".join(sections)

    return ""


# Standalone test
if __name__ == "__main__":
    print("Testing Context Monitor...")
    print("=" * 60)
    print("Instructions:")
    print("1. Switch between windows")
    print("2. Select and copy text (Ctrl+C)")
    print("3. Wait 10 seconds for the test to complete")
    print("=" * 60)

    monitor = ContextMonitor(poll_interval=0.2)
    monitor.start()

    # Run for 10 seconds
    time.sleep(10)

    timeline = monitor.stop()

    print("\n" + "=" * 60)
    print("TIMELINE:")
    print("=" * 60)
    print(timeline.to_markdown())

    print("\n" + "=" * 60)
    print("FORMATTED FOR PROMPT:")
    print("=" * 60)
    print(format_timeline_for_prompt(timeline))
