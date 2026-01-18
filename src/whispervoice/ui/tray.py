"""
System tray icon for WhisperVoice.

Provides a tray icon with status indicator and menu.
"""

from typing import Optional, Callable

import pystray
from PIL import Image, ImageDraw

from .indicator import COLORS


class TrayIcon:
    """System tray icon with status indicator."""

    def __init__(
        self,
        name: str = "WhisperVoice",
        hotkey: str = "ctrl+shift+space",
        on_quit: Optional[Callable] = None,
    ):
        """
        Initialize the tray icon.

        Args:
            name: Application name for tooltip
            hotkey: Hotkey string for display
            on_quit: Callback when quit is selected
        """
        self.name = name
        self.hotkey = hotkey
        self._on_quit = on_quit
        self._icon: Optional[pystray.Icon] = None
        self._current_color = COLORS["loading"]["accent"]

    def _create_icon_image(self, color: str) -> Image.Image:
        """Create tray icon image with given color."""
        size = 64
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse([8, 8, size - 8, size - 8], fill=color)
        return image

    def _on_menu_quit(self, icon, item):
        """Handle quit from tray menu."""
        icon.stop()
        if self._on_quit:
            self._on_quit()

    def start(self):
        """Start the tray icon (runs in background)."""
        image = self._create_icon_image(self._current_color)

        menu = pystray.Menu(
            pystray.MenuItem(self.name, lambda: None, enabled=False),
            pystray.MenuItem(f"Hotkey: {self.hotkey.upper()}", lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._on_menu_quit)
        )

        self._icon = pystray.Icon("whisper", image, self.name, menu)
        self._icon.run_detached()

    def stop(self):
        """Stop the tray icon."""
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass
            self._icon = None

    def update_color(self, color: str):
        """
        Update the tray icon color.

        Args:
            color: Hex color string (e.g., "#a6e3a1")
        """
        self._current_color = color
        if self._icon:
            try:
                self._icon.icon = self._create_icon_image(color)
            except Exception:
                pass

    def set_state(self, state: str):
        """
        Update icon color based on state.

        Args:
            state: One of "loading", "ready", "recording", "transcribing"
        """
        colors = COLORS.get(state, COLORS["loading"])
        self.update_color(colors["accent"])
