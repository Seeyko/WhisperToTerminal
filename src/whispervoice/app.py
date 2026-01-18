"""
WhisperVoice Application.

Main application that ties together all components:
- Audio recording
- Speech transcription
- Context capture and monitoring
- Prompt assembly
- UI (indicator and tray)
"""

import sys
import time
import threading
import queue
from typing import Optional

import keyboard
import pyperclip

from .core.audio import AudioRecorder, normalize_audio
from .core.transcription import WhisperTranscriber
from .context.capture import get_active_window_info
from .context.monitor import ContextMonitor, ContextTimeline, format_timeline_for_prompt
from .context.types import WindowContext
from .output.assembler import PromptAssembler
from .ui.indicator import ModernIndicator, COLORS
from .ui.tray import TrayIcon


class WhisperVoiceApp:
    """
    Main WhisperVoice application.

    Coordinates all components and handles the recording workflow.
    """

    def __init__(
        self,
        hotkey: str = "ctrl+shift+space",
        model_name: str = "small",
        sample_rate: int = 16000,
    ):
        """
        Initialize the application.

        Args:
            hotkey: Keyboard shortcut to start/stop recording
            model_name: Whisper model size
            sample_rate: Audio sample rate
        """
        self.hotkey = hotkey
        self.model_name = model_name
        self.sample_rate = sample_rate

        # Components
        self._recorder = AudioRecorder(sample_rate=sample_rate)
        self._transcriber = WhisperTranscriber(
            model_name=model_name,
            on_load_progress=lambda msg: print(msg)
        )
        self._assembler = PromptAssembler()

        # State
        self._is_processing = False
        self._captured_context: Optional[WindowContext] = None
        self._context_monitor: Optional[ContextMonitor] = None

        # UI
        self._command_queue = queue.Queue()
        self._indicator: Optional[ModernIndicator] = None
        self._tray: Optional[TrayIcon] = None

    def _update_state(self, state: str):
        """Thread-safe state update."""
        self._command_queue.put(("state", state))
        if self._tray:
            self._tray.set_state(state)

    def _start_recording(self) -> bool:
        """Start recording with context monitoring."""
        if self._is_processing:
            return False

        # Capture initial context
        self._captured_context = get_active_window_info(capture_selection=False)
        if self._captured_context:
            print(f"[Context] {self._captured_context.process_name} - {self._captured_context.app_type.value}")

        # Start context monitoring
        self._context_monitor = ContextMonitor(poll_interval=0.2)
        self._context_monitor.start()
        print("[Monitor] Continuous context monitoring started")

        # Start audio recording
        if self._recorder.start():
            self._update_state("recording")
            return True
        else:
            if self._context_monitor:
                self._context_monitor.stop()
            self._update_state("ready")
            return False

    def _stop_recording(self) -> tuple[Optional[any], Optional[ContextTimeline]]:
        """Stop recording and return audio data plus timeline."""
        # Stop context monitoring
        timeline = None
        if self._context_monitor:
            timeline = self._context_monitor.stop()
            num_events = len(timeline.events) if timeline else 0
            print(f"[Monitor] Stopped - captured {num_events} context events")
            self._context_monitor = None

        # Stop audio recording
        audio_data = self._recorder.stop()

        return audio_data, timeline

    def _transcribe_and_paste(
        self,
        audio_data,
        context: Optional[WindowContext],
        timeline: Optional[ContextTimeline]
    ):
        """Transcribe audio and paste result."""
        self._is_processing = True
        self._update_state("transcribing")

        try:
            # Check minimum audio length (0.5 seconds)
            if audio_data is None or len(audio_data) < self.sample_rate * 0.5:
                print("Audio too short", file=sys.stderr)
                return

            # Transcribe
            result = self._transcriber.transcribe(audio_data)
            if not result or result.is_empty:
                print("No speech detected", file=sys.stderr)
                return

            text = result.text
            print(f"[{result.language}] {text}")

            # Assemble prompt
            output = self._assembler.assemble(text, context)

            # Add timeline if available
            if timeline and timeline.events:
                timeline_output = format_timeline_for_prompt(timeline)
                if timeline_output:
                    # Remove existing selection section if present
                    if "## Selected Code" in output:
                        idx = output.find("## Selected Code")
                        if idx > 0:
                            output = output[:idx].rstrip()

                    output = output + "\n\n" + timeline_output

                # Add timeline summary
                timeline_md = timeline.to_markdown()
                if timeline_md:
                    output = output + "\n\n" + timeline_md

            # Copy and paste
            pyperclip.copy(output)
            time.sleep(0.1)
            keyboard.send("ctrl+v")

        except Exception as e:
            print(f"Transcription error: {e}", file=sys.stderr)
        finally:
            self._is_processing = False
            self._update_state("ready")

    def _on_hotkey(self):
        """Handle hotkey press."""
        if self._is_processing:
            return

        if not self._recorder.is_recording:
            self._start_recording()
        else:
            audio_data, timeline = self._stop_recording()
            if audio_data is not None and len(audio_data) > 0:
                context = self._captured_context
                self._captured_context = None

                threading.Thread(
                    target=self._transcribe_and_paste,
                    args=(audio_data, context, timeline),
                    daemon=True
                ).start()
            else:
                self._captured_context = None
                self._update_state("ready")

    def _on_quit(self):
        """Handle quit request."""
        self._command_queue.put(("quit",))

    def run(self):
        """Run the application."""
        # Create UI
        self._indicator = ModernIndicator(self._command_queue)
        self._tray = TrayIcon(
            name="WhisperVoice",
            hotkey=self.hotkey,
            on_quit=self._on_quit
        )

        # Start tray in background
        threading.Thread(target=self._tray.start, daemon=True).start()

        # Load model in background
        def load_model():
            self._update_state("loading")
            self._transcriber.load_model()
            self._update_state("ready")

        threading.Thread(target=load_model, daemon=True).start()

        # Register hotkey
        keyboard.add_hotkey(self.hotkey, self._on_hotkey, suppress=True)

        # Run indicator (blocks until quit)
        try:
            self._indicator.run()
        except KeyboardInterrupt:
            pass
        finally:
            if self._recorder.is_recording:
                self._recorder.stop()
            if self._tray:
                self._tray.stop()


def main():
    """Entry point for GUI application."""
    app = WhisperVoiceApp()
    app.run()


if __name__ == "__main__":
    main()
