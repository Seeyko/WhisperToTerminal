#!/usr/bin/env python3
"""
WhisperVoice - Voice prompting with context capture for Windows.

Press Ctrl+Shift+Space to start/stop recording.
Transcribed text with context is automatically pasted.
"""

import sys
from pathlib import Path

# Add src to path for package imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from whispervoice.app import main

if __name__ == "__main__":
    main()
