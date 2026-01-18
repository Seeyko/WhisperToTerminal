"""
WhisperVoice - Voice prompting with context capture for Windows.

A voice-to-text tool that captures screen context while you speak.
"""

__version__ = "2.0.0"
__author__ = "WhisperVoice Contributors"

from .core.audio import AudioRecorder
from .core.transcription import WhisperTranscriber
from .context.capture import get_active_window_info, capture_selected_text
from .context.monitor import ContextMonitor
from .output.assembler import PromptAssembler

__all__ = [
    "AudioRecorder",
    "WhisperTranscriber",
    "get_active_window_info",
    "capture_selected_text",
    "ContextMonitor",
    "PromptAssembler",
]
