#!/usr/bin/env python3
"""
Whisper Voice-to-Text Hotkey Application

Press Ctrl+Shift+Space to start/stop recording.
Transcribed text is automatically pasted at cursor position.
Supports French and English with auto-detection.

Can run silently in background with audio feedback (beeps).
"""

import sys
import time
import threading
import winsound
import numpy as np
import sounddevice as sd
import keyboard
import pyperclip
import whisper

# Configuration
HOTKEY = "ctrl+shift+space"
SAMPLE_RATE = 16000  # Whisper's native sample rate
MODEL_NAME = "small"  # Good balance for FR/EN

# Audio feedback (frequency in Hz, duration in ms)
BEEP_START = (600, 150)    # Low beep = recording started
BEEP_STOP = (800, 150)     # Higher beep = recording stopped
BEEP_DONE = (1000, 100)    # High short beep = transcription done
BEEP_ERROR = (300, 300)    # Low long beep = error

# Global state
is_recording = False
audio_buffer = []
stream = None
model = None


def load_model():
    """Load Whisper model (downloads if not cached)."""
    global model
    print(f"Loading Whisper '{MODEL_NAME}' model...")
    model = whisper.load_model(MODEL_NAME)
    print("Model loaded. Ready!")
    print(f"\nPress {HOTKEY.upper()} to start/stop recording.")
    print("Press Ctrl+C to exit.\n")


def audio_callback(indata, frames, time_info, status):
    """Callback for audio stream - stores audio chunks."""
    if status:
        print(f"Audio status: {status}", file=sys.stderr)
    audio_buffer.append(indata.copy())


def beep(sound):
    """Play a beep sound in background."""
    threading.Thread(
        target=lambda: winsound.Beep(sound[0], sound[1]),
        daemon=True
    ).start()


def start_recording():
    """Start recording audio from microphone."""
    global is_recording, audio_buffer, stream

    audio_buffer = []
    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype=np.float32,
        callback=audio_callback
    )
    stream.start()
    is_recording = True
    beep(BEEP_START)
    print("Recording... (press hotkey again to stop)")


def stop_recording():
    """Stop recording and return audio data."""
    global is_recording, stream

    if stream:
        stream.stop()
        stream.close()
        stream = None
    is_recording = False
    beep(BEEP_STOP)

    if not audio_buffer:
        return None

    # Concatenate all audio chunks
    audio_data = np.concatenate(audio_buffer, axis=0).flatten()
    return audio_data


def transcribe_and_paste(audio_data):
    """Transcribe audio with Whisper and paste result."""
    if audio_data is None or len(audio_data) == 0:
        print("No audio recorded.")
        beep(BEEP_ERROR)
        return

    print("Transcribing...")

    try:
        # Transcribe with auto language detection
        result = model.transcribe(
            audio_data,
            language=None,  # Auto-detect FR/EN
            fp16=False  # Use fp32 for CPU compatibility
        )

        text = result["text"].strip()
        detected_lang = result.get("language", "unknown")

        if not text:
            print("No speech detected.")
            beep(BEEP_ERROR)
            return

        print(f"[{detected_lang}] {text}")

        # Copy to clipboard and paste
        pyperclip.copy(text)
        time.sleep(0.05)  # Small delay for clipboard
        keyboard.send("ctrl+v")
        beep(BEEP_DONE)

    except Exception as e:
        print(f"Transcription error: {e}")
        beep(BEEP_ERROR)


def on_hotkey():
    """Handle hotkey press - toggle recording."""
    global is_recording

    if not is_recording:
        start_recording()
    else:
        audio_data = stop_recording()
        # Run transcription in background to not block hotkey handler
        threading.Thread(
            target=transcribe_and_paste,
            args=(audio_data,),
            daemon=True
        ).start()


def main():
    """Main entry point."""
    print("=" * 50)
    print("Whisper Voice-to-Text")
    print("=" * 50)

    # Load model at startup
    load_model()

    # Register hotkey
    keyboard.add_hotkey(HOTKEY, on_hotkey, suppress=True)

    # Keep running
    try:
        keyboard.wait()  # Block forever, waiting for hotkey events
    except KeyboardInterrupt:
        print("\nExiting...")
        if is_recording:
            stop_recording()


if __name__ == "__main__":
    main()
