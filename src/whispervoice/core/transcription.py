"""
Whisper transcription module.

Provides a WhisperTranscriber class for speech-to-text conversion.
"""

import sys
from typing import Optional, Callable
from dataclasses import dataclass

import numpy as np

# Whisper is imported lazily to speed up startup
_whisper = None


def _get_whisper():
    """Lazy import of whisper module."""
    global _whisper
    if _whisper is None:
        import whisper
        _whisper = whisper
    return _whisper


@dataclass
class TranscriptionResult:
    """Result of a transcription."""
    text: str
    language: str
    segments: list
    duration: float

    @property
    def is_empty(self) -> bool:
        """Check if transcription is empty."""
        return not self.text or not self.text.strip()


class WhisperTranscriber:
    """
    Transcribes audio using OpenAI Whisper.

    Usage:
        transcriber = WhisperTranscriber(model_name="small")
        transcriber.load_model()  # Optional, auto-loads on first transcribe
        result = transcriber.transcribe(audio_data)
        print(result.text)
    """

    VALID_MODELS = ["tiny", "base", "small", "medium", "large"]

    def __init__(
        self,
        model_name: str = "small",
        device: Optional[str] = None,
        on_load_progress: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize the transcriber.

        Args:
            model_name: Whisper model size (tiny, base, small, medium, large)
            device: Device to use (None for auto, "cpu", "cuda")
            on_load_progress: Callback for load progress messages
        """
        if model_name not in self.VALID_MODELS:
            raise ValueError(f"Invalid model: {model_name}. Must be one of {self.VALID_MODELS}")

        self.model_name = model_name
        self.device = device
        self.on_load_progress = on_load_progress
        self._model = None

    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._model is not None

    def load_model(self) -> bool:
        """
        Load the Whisper model.

        Returns:
            True if model loaded successfully.
        """
        if self._model is not None:
            return True

        try:
            if self.on_load_progress:
                self.on_load_progress(f"Loading Whisper '{self.model_name}' model...")

            whisper = _get_whisper()
            self._model = whisper.load_model(self.model_name, device=self.device)

            if self.on_load_progress:
                self.on_load_progress("Model loaded successfully.")

            return True

        except Exception as e:
            print(f"Failed to load model: {e}", file=sys.stderr)
            return False

    def transcribe(
        self,
        audio_data: np.ndarray,
        language: Optional[str] = None,
        fp16: bool = False,
        condition_on_previous_text: bool = False,
    ) -> Optional[TranscriptionResult]:
        """
        Transcribe audio data to text.

        Args:
            audio_data: Audio data as numpy array (float32, 16kHz)
            language: Language code (None for auto-detection)
            fp16: Use FP16 inference (requires CUDA)
            condition_on_previous_text: Condition on previous text

        Returns:
            TranscriptionResult or None on error.
        """
        # Auto-load model if needed
        if not self.is_loaded:
            if not self.load_model():
                return None

        try:
            # Normalize audio
            audio_data = audio_data.astype(np.float32)
            max_val = np.max(np.abs(audio_data))
            if max_val > 0:
                audio_data = audio_data / max_val

            # Transcribe
            result = self._model.transcribe(
                audio_data,
                language=language,
                fp16=fp16,
                condition_on_previous_text=condition_on_previous_text,
            )

            return TranscriptionResult(
                text=result["text"].strip(),
                language=result.get("language", "unknown"),
                segments=result.get("segments", []),
                duration=len(audio_data) / 16000,  # Assume 16kHz
            )

        except Exception as e:
            print(f"Transcription error: {e}", file=sys.stderr)
            return None

    def transcribe_file(self, file_path: str, **kwargs) -> Optional[TranscriptionResult]:
        """
        Transcribe audio from a file.

        Args:
            file_path: Path to audio file
            **kwargs: Additional arguments for transcribe()

        Returns:
            TranscriptionResult or None on error.
        """
        if not self.is_loaded:
            if not self.load_model():
                return None

        try:
            whisper = _get_whisper()
            audio = whisper.load_audio(file_path)
            return self.transcribe(audio, **kwargs)
        except Exception as e:
            print(f"Failed to load audio file: {e}", file=sys.stderr)
            return None
