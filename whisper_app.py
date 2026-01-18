#!/usr/bin/env python3
"""
Whisper Voice-to-Text Application

A Windows application with visual indicator for voice-to-text transcription.
Press Ctrl+Shift+Space to start/stop recording.
"""

import sys
import time
import threading
import queue
import numpy as np
import sounddevice as sd
import keyboard
import pyperclip
import whisper
import pystray
from PIL import Image, ImageDraw
import tkinter as tk

# Configuration
HOTKEY = "ctrl+shift+space"
SAMPLE_RATE = 16000
MODEL_NAME = "small"

# Colors (modern palette)
COLORS = {
    "loading": {"bg": "#1e1e2e", "fg": "#6c7086", "accent": "#89b4fa"},
    "ready": {"bg": "#1e1e2e", "fg": "#a6e3a1", "accent": "#a6e3a1"},
    "recording": {"bg": "#1e1e2e", "fg": "#f38ba8", "accent": "#f38ba8"},
    "transcribing": {"bg": "#1e1e2e", "fg": "#f9e2af", "accent": "#f9e2af"},
}

# Global state
is_recording = False
is_processing = False
audio_buffer = []
stream = None
model = None
indicator = None
tray_icon = None
command_queue = queue.Queue()


class ModernIndicator:
    """A modern pill-shaped floating indicator."""

    def __init__(self):
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
        self.bg_rect = self.rounded_rect(
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
        self.position_window()

        # Drag support
        self.canvas.bind("<Button-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.drag_x = 0
        self.drag_y = 0

        # Animation state
        self.pulse_state = 0
        self.animating = False

        # Make window shape rounded (Windows 11 style)
        self.root.wm_attributes("-transparentcolor", "")

    def rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
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

    def position_window(self):
        """Position at bottom center of screen."""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - self.width) // 2
        y = screen_height - self.height - 60
        self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")

    def start_drag(self, event):
        self.drag_x = event.x
        self.drag_y = event.y

    def on_drag(self, event):
        x = self.root.winfo_x() + event.x - self.drag_x
        y = self.root.winfo_y() + event.y - self.drag_y
        self.root.geometry(f"+{x}+{y}")

    def animate_pulse(self):
        """Animate pulsing ring for recording."""
        if not self.animating:
            self.canvas.itemconfig(self.pulse_ring, state="hidden")
            return

        self.pulse_state = (self.pulse_state + 1) % 20

        # Pulse opacity effect
        if self.pulse_state < 10:
            scale = 1 + (self.pulse_state * 0.05)
            opacity_hex = hex(int(255 * (1 - self.pulse_state / 10)))[2:].zfill(2)
        else:
            scale = 1 + ((20 - self.pulse_state) * 0.05)
            opacity_hex = hex(int(255 * ((self.pulse_state - 10) / 10)))[2:].zfill(2)

        # Update ring size
        r = self.dot_radius + 4 + (self.pulse_state % 10)
        self.canvas.coords(
            self.pulse_ring,
            self.dot_x - r, self.dot_y - r,
            self.dot_x + r, self.dot_y + r
        )
        self.canvas.itemconfig(self.pulse_ring, state="normal")

        self.root.after(50, self.animate_pulse)

    def set_state(self, state):
        """Update indicator state."""
        colors = COLORS.get(state, COLORS["loading"])

        labels = {
            "loading": "Loading...",
            "ready": "Ready",
            "recording": "Recording",
            "transcribing": "Processing..."
        }

        # Update colors
        self.canvas.itemconfig(self.dot, fill=colors["accent"])
        self.canvas.itemconfig(self.text, text=labels.get(state, ""), fill=colors["fg"])
        self.canvas.itemconfig(self.pulse_ring, outline=colors["accent"])

        # Start/stop animation
        if state == "recording":
            if not self.animating:
                self.animating = True
                self.animate_pulse()
        else:
            self.animating = False
            self.canvas.itemconfig(self.pulse_ring, state="hidden")

        self.root.update()

    def process_queue(self):
        """Process commands from queue (thread-safe updates)."""
        try:
            while True:
                cmd = command_queue.get_nowait()
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


def update_state(state):
    """Thread-safe state update."""
    command_queue.put(("state", state))
    update_tray_icon(COLORS.get(state, COLORS["loading"])["accent"])


def create_tray_icon_image(color):
    """Create tray icon."""
    size = 64
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse([8, 8, size - 8, size - 8], fill=color)
    return image


def on_tray_quit(icon, item):
    """Handle quit from tray menu."""
    global tray_icon
    icon.stop()
    command_queue.put(("quit",))


def setup_tray_icon():
    """Create system tray icon."""
    global tray_icon

    image = create_tray_icon_image(COLORS["loading"]["accent"])
    menu = pystray.Menu(
        pystray.MenuItem("Whisper Voice-to-Text", lambda: None, enabled=False),
        pystray.MenuItem(f"Hotkey: {HOTKEY.upper()}", lambda: None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", on_tray_quit)
    )

    tray_icon = pystray.Icon("whisper", image, "Whisper Voice-to-Text", menu)
    tray_icon.run_detached()


def update_tray_icon(color):
    """Update tray icon color."""
    global tray_icon
    if tray_icon:
        try:
            tray_icon.icon = create_tray_icon_image(color)
        except Exception:
            pass


def load_model():
    """Load Whisper model."""
    global model
    update_state("loading")
    model = whisper.load_model(MODEL_NAME)
    update_state("ready")


def audio_callback(indata, frames, time_info, status):
    """Audio stream callback."""
    if is_recording:
        audio_buffer.append(indata.copy())


def start_recording():
    """Start recording audio."""
    global is_recording, is_processing, audio_buffer, stream

    # Don't start if already processing
    if is_processing:
        return False

    # Clear buffer and start fresh
    audio_buffer = []

    try:
        stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype=np.float32,
            callback=audio_callback,
            blocksize=1024
        )
        stream.start()
        is_recording = True
        update_state("recording")
        return True
    except Exception as e:
        print(f"Recording error: {e}", file=sys.stderr)
        update_state("ready")
        return False


def stop_recording():
    """Stop recording and return audio data."""
    global is_recording, stream

    is_recording = False

    if stream:
        try:
            stream.stop()
            stream.close()
        except Exception:
            pass
        stream = None

    if not audio_buffer:
        return None

    try:
        return np.concatenate(audio_buffer, axis=0).flatten()
    except Exception:
        return None


def transcribe_and_paste(audio_data):
    """Transcribe audio and paste result."""
    global is_processing

    is_processing = True
    update_state("transcribing")

    try:
        if audio_data is None or len(audio_data) < SAMPLE_RATE * 0.5:
            # Less than 0.5 seconds of audio
            print("Audio too short", file=sys.stderr)
            return

        # Normalize audio
        audio_data = audio_data.astype(np.float32)
        if np.max(np.abs(audio_data)) > 0:
            audio_data = audio_data / np.max(np.abs(audio_data))

        result = model.transcribe(
            audio_data,
            language=None,
            fp16=False,
            condition_on_previous_text=False
        )

        text = result["text"].strip()

        if text:
            pyperclip.copy(text)
            time.sleep(0.1)
            keyboard.send("ctrl+v")

    except Exception as e:
        print(f"Transcription error: {e}", file=sys.stderr)
    finally:
        is_processing = False
        update_state("ready")


def on_hotkey():
    """Handle hotkey press."""
    global is_recording, is_processing

    # Ignore if still processing previous recording
    if is_processing:
        return

    if not is_recording:
        start_recording()
    else:
        audio_data = stop_recording()
        if audio_data is not None and len(audio_data) > 0:
            threading.Thread(
                target=transcribe_and_paste,
                args=(audio_data,),
                daemon=True
            ).start()
        else:
            update_state("ready")


def main():
    """Main entry point."""
    global indicator

    # Create the floating indicator
    indicator = ModernIndicator()

    # Setup tray icon
    threading.Thread(target=setup_tray_icon, daemon=True).start()

    # Load model in background
    threading.Thread(target=load_model, daemon=True).start()

    # Register hotkey
    keyboard.add_hotkey(HOTKEY, on_hotkey, suppress=True)

    # Run the indicator
    try:
        indicator.run()
    except KeyboardInterrupt:
        pass
    finally:
        if is_recording:
            stop_recording()
        if tray_icon:
            tray_icon.stop()


if __name__ == "__main__":
    main()
