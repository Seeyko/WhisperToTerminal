"""
Modern floating indicator for WhisperVoice.

A pill-shaped floating window that shows the current recording state.
"""

import queue
import tkinter as tk
from typing import Optional, Callable


# Colors (modern palette)
COLORS = {
    "loading": {"bg": "#1e1e2e", "fg": "#6c7086", "accent": "#89b4fa"},
    "ready": {"bg": "#1e1e2e", "fg": "#a6e3a1", "accent": "#a6e3a1"},
    "recording": {"bg": "#1e1e2e", "fg": "#f38ba8", "accent": "#f38ba8"},
    "transcribing": {"bg": "#1e1e2e", "fg": "#f9e2af", "accent": "#f9e2af"},
}

STATE_LABELS = {
    "loading": "Loading...",
    "ready": "Ready",
    "recording": "Recording",
    "transcribing": "Processing...",
}


class ModernIndicator:
    """A modern pill-shaped floating indicator."""

    def __init__(self, command_queue: Optional[queue.Queue] = None):
        """
        Initialize the indicator.

        Args:
            command_queue: Queue for receiving state update commands.
                          Commands are tuples: ("state", state_name) or ("quit",)
        """
        self.command_queue = command_queue or queue.Queue()

        self.root = tk.Tk()
        self.root.title("Whisper")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.95)

        # Pill dimensions
        self.width = 140
        self.height = 40
        self.corner_radius = 20

        # Create main frame with dark background
        self.frame = tk.Frame(self.root, bg="#1e1e2e", highlightthickness=0)
        self.frame.pack(fill="both", expand=True)

        # Canvas for custom drawing
        self.canvas = tk.Canvas(
            self.frame,
            width=self.width,
            height=self.height,
            bg="#1e1e2e",
            highlightthickness=0
        )
        self.canvas.pack()

        # Draw rounded rectangle background
        self.bg_rect = self._rounded_rect(
            2, 2, self.width - 2, self.height - 2,
            self.corner_radius,
            fill="#1e1e2e",
            outline="#313244",
            width=2
        )

        # Status dot (left side)
        self.dot_x = 22
        self.dot_y = self.height // 2
        self.dot_radius = 8
        self.dot = self.canvas.create_oval(
            self.dot_x - self.dot_radius,
            self.dot_y - self.dot_radius,
            self.dot_x + self.dot_radius,
            self.dot_y + self.dot_radius,
            fill="#6c7086",
            outline=""
        )

        # Pulsing ring (for recording animation)
        self.pulse_ring = self.canvas.create_oval(
            self.dot_x - self.dot_radius - 4,
            self.dot_y - self.dot_radius - 4,
            self.dot_x + self.dot_radius + 4,
            self.dot_y + self.dot_radius + 4,
            fill="",
            outline="#f38ba8",
            width=2,
            state="hidden"
        )

        # Status text (right side)
        self.text = self.canvas.create_text(
            self.width // 2 + 10,
            self.height // 2,
            text="Loading...",
            fill="#6c7086",
            font=("Segoe UI", 10, "bold"),
            anchor="center"
        )

        # Position at bottom center
        self._position_window()

        # Drag support
        self.canvas.bind("<Button-1>", self._start_drag)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self._drag_x = 0
        self._drag_y = 0

        # Animation state
        self._pulse_state = 0
        self._animating = False

        # Make window shape rounded (Windows 11 style)
        self.root.wm_attributes("-transparentcolor", "")

        # State change callback
        self._on_state_change: Optional[Callable[[str], None]] = None

    def _rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        """Draw a rounded rectangle."""
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
            x1 + radius, y1,
        ]
        return self.canvas.create_polygon(points, smooth=True, **kwargs)

    def _position_window(self):
        """Position at bottom center of screen."""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - self.width) // 2
        y = screen_height - self.height - 60
        self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")

    def _start_drag(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_drag(self, event):
        x = self.root.winfo_x() + event.x - self._drag_x
        y = self.root.winfo_y() + event.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    def _animate_pulse(self):
        """Animate pulsing ring for recording."""
        if not self._animating:
            self.canvas.itemconfig(self.pulse_ring, state="hidden")
            return

        self._pulse_state = (self._pulse_state + 1) % 20

        # Update ring size
        r = self.dot_radius + 4 + (self._pulse_state % 10)
        self.canvas.coords(
            self.pulse_ring,
            self.dot_x - r, self.dot_y - r,
            self.dot_x + r, self.dot_y + r
        )
        self.canvas.itemconfig(self.pulse_ring, state="normal")

        self.root.after(50, self._animate_pulse)

    def set_state(self, state: str):
        """
        Update indicator state.

        Args:
            state: One of "loading", "ready", "recording", "transcribing"
        """
        colors = COLORS.get(state, COLORS["loading"])
        label = STATE_LABELS.get(state, "")

        # Update colors
        self.canvas.itemconfig(self.dot, fill=colors["accent"])
        self.canvas.itemconfig(self.text, text=label, fill=colors["fg"])
        self.canvas.itemconfig(self.pulse_ring, outline=colors["accent"])

        # Start/stop animation
        if state == "recording":
            if not self._animating:
                self._animating = True
                self._animate_pulse()
        else:
            self._animating = False
            self.canvas.itemconfig(self.pulse_ring, state="hidden")

        self.root.update()

        # Callback
        if self._on_state_change:
            self._on_state_change(state)

    def set_on_state_change(self, callback: Callable[[str], None]):
        """Set callback for state changes."""
        self._on_state_change = callback

    def process_queue(self):
        """Process commands from queue (thread-safe updates)."""
        try:
            while True:
                cmd = self.command_queue.get_nowait()
                if cmd[0] == "state":
                    self.set_state(cmd[1])
                elif cmd[0] == "quit":
                    self.root.quit()
                    return
        except queue.Empty:
            pass
        self.root.after(50, self.process_queue)

    def run(self):
        """Start the tkinter main loop."""
        self.root.after(50, self.process_queue)
        self.root.mainloop()

    def quit(self):
        """Close the indicator."""
        self.root.quit()
        self.root.destroy()
