"""
Audio recording module.

Provides a reusable AudioRecorder class for capturing microphone input.
"""

import sys
from typing import Optional, Callable
import numpy as np
import sounddevice as sd


class AudioRecorder:
    """
    Records audio from the microphone.

    Usage:
        recorder = AudioRecorder(sample_rate=16000)
        recorder.start()
        # ... recording ...
        audio_data = recorder.stop()
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        dtype=np.float32,
        blocksize: int = 1024,
        on_audio: Optional[Callable[[np.ndarray], None]] = None,
    ):
        """
        Initialize the audio recorder.

        Args:
            sample_rate: Sample rate in Hz (default 16000 for Whisper)
            channels: Number of audio channels (default 1 for mono)
            dtype: Audio data type (default float32)
            blocksize: Audio block size (default 1024)
            on_audio: Optional callback for each audio chunk
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.dtype = dtype
        self.blocksize = blocksize
        self.on_audio = on_audio

        self._buffer: list[np.ndarray] = []
        self._stream: Optional[sd.InputStream] = None
        self._is_recording = False

    @property
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._is_recording

    def _audio_callback(self, indata, frames, time_info, status):
        """Internal callback for audio stream."""
        if status:
            print(f"Audio status: {status}", file=sys.stderr)

        if self._is_recording:
            self._buffer.append(indata.copy())
            if self.on_audio:
                self.on_audio(indata.copy())

    def start(self) -> bool:
        """
        Start recording audio.

        Returns:
            True if recording started successfully, False otherwise.
        """
        if self._is_recording:
            return False

        self._buffer = []

        try:
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=self.dtype,
                callback=self._audio_callback,
                blocksize=self.blocksize,
            )
            self._stream.start()
            self._is_recording = True
            return True
        except Exception as e:
            print(f"Failed to start recording: {e}", file=sys.stderr)
            return False

    def stop(self) -> Optional[np.ndarray]:
        """
        Stop recording and return the audio data.

        Returns:
            Numpy array of audio data, or None if no audio was recorded.
        """
        self._is_recording = False

        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

        if not self._buffer:
            return None

        try:
            audio_data = np.concatenate(self._buffer, axis=0).flatten()
            return audio_data
        except Exception:
            return None

    def get_duration(self) -> float:
        """
        Get the current recording duration in seconds.

        Returns:
            Duration in seconds.
        """
        if not self._buffer:
            return 0.0

        total_samples = sum(chunk.shape[0] for chunk in self._buffer)
        return total_samples / self.sample_rate


def normalize_audio(audio_data: np.ndarray) -> np.ndarray:
    """
    Normalize audio data to [-1, 1] range.

    Args:
        audio_data: Raw audio data

    Returns:
        Normalized audio data as float32
    """
    audio_data = audio_data.astype(np.float32)
    max_val = np.max(np.abs(audio_data))
    if max_val > 0:
        audio_data = audio_data / max_val
    return audio_data
