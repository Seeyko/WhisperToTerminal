# WhisperVoice

A lightweight Windows voice-to-text application powered by OpenAI's Whisper model. Press a hotkey, speak, and your words are automatically transcribed and pasted at the cursor position.

**100% local and offline** - No internet connection required after initial model download.

## Features

- **Hotkey Activated**: Press `Ctrl+Shift+Space` to start/stop recording
- **Auto-Paste**: Transcribed text is automatically pasted at cursor position
- **Multi-Language**: Supports 16+ languages with automatic detection
- **Local Inference**: Runs entirely on your machine using OpenAI Whisper
- **Modern UI**: Floating pill-shaped indicator with status colors
- **System Tray**: Runs quietly in the background
- **Two Modes**: GUI app with visual indicator, or lightweight CLI version

## Screenshots

| State | Indicator |
|-------|-----------|
| Ready | Green dot - "Ready" |
| Recording | Pink pulsing dot - "Recording" |
| Processing | Yellow dot - "Processing..." |

## Installation

### Prerequisites

- Windows 10/11
- Python 3.10+
- A working microphone

### From Source

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/WhisperVoice.git
   cd WhisperVoice
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install additional dependencies for GUI and system tray**
   ```bash
   pip install pystray pillow
   ```

5. **Run the application**
   ```bash
   # GUI version with visual indicator
   python whisper_app.py

   # Or CLI version (lighter, console output only)
   python whisper_hotkey.py
   ```

### First Run

On first launch, Whisper will download the `small` model (~461 MB). This only happens once - the model is cached locally for future use.

## Building a Standalone Executable

To create a portable `.exe` that doesn't require Python:

1. **Install PyInstaller**
   ```bash
   pip install pyinstaller
   ```

2. **Build the executable**
   ```bash
   pyinstaller WhisperVoice.spec
   ```

3. **Find the executable**
   ```
   dist/WhisperVoice.exe
   ```

The executable bundles everything needed including the Whisper assets. Note: The Whisper model itself is NOT bundled - it will be downloaded on first run.

## Auto-Start on Login

To have WhisperVoice start automatically when you log into Windows:

```powershell
# Install to startup
powershell -ExecutionPolicy Bypass -File scripts\install_startup.ps1

# Remove from startup
powershell -ExecutionPolicy Bypass -File scripts\uninstall_startup.ps1
```

## Usage

1. **Start the application** - A small indicator appears at the bottom of your screen
2. **Press `Ctrl+Shift+Space`** - The indicator turns pink and starts pulsing (recording)
3. **Speak your text**
4. **Press `Ctrl+Shift+Space` again** - Recording stops, indicator turns yellow (processing)
5. **Text appears at cursor** - The transcribed text is automatically pasted

### Tips

- Speak clearly at a normal pace
- Works best in quiet environments
- Minimum recording length is 0.5 seconds
- The indicator can be dragged to any position on screen

## Configuration

Edit the constants at the top of `whisper_app.py` to customize:

```python
HOTKEY = "ctrl+shift+space"  # Change the activation hotkey
SAMPLE_RATE = 16000          # Audio sample rate (16kHz is Whisper's native)
MODEL_NAME = "small"         # Whisper model size (see below)
```

### Whisper Models

| Model | Size | Speed | Accuracy | VRAM |
|-------|------|-------|----------|------|
| `tiny` | 39 MB | Fastest | Lower | ~1 GB |
| `base` | 74 MB | Fast | Good | ~1 GB |
| `small` | 244 MB | Medium | Better | ~2 GB |
| `medium` | 769 MB | Slow | High | ~5 GB |
| `large` | 1550 MB | Slowest | Highest | ~10 GB |

The default `small` model offers a good balance of speed and accuracy for most use cases.

## Project Structure

```
WhisperVoice/
├── whisper_app.py       # Main GUI application
├── whisper_hotkey.py    # CLI version (no GUI)
├── requirements.txt     # Python dependencies
├── WhisperVoice.spec    # PyInstaller build configuration
├── scripts/
│   ├── install_startup.ps1    # Add to Windows startup
│   ├── uninstall_startup.ps1  # Remove from Windows startup
│   └── start_whisper.vbs      # Silent launcher script
└── README.md
```

## Troubleshooting

### "No audio recorded" or transcription is empty
- Check that your microphone is working and selected as default input
- Ensure you're speaking loud enough
- Try recording for at least 1-2 seconds

### Model download fails
- Check your internet connection
- The model is downloaded from Hugging Face - ensure it's accessible
- Try running with admin privileges

### High CPU usage during transcription
- This is normal - Whisper runs on CPU by default
- Consider using a smaller model (`tiny` or `base`)
- For GPU acceleration, install `torch` with CUDA support

### Hotkey doesn't work
- Make sure no other application is using `Ctrl+Shift+Space`
- Try running as administrator
- Check that the application is running (look for tray icon)

## Dependencies

- [openai-whisper](https://github.com/openai/whisper) - Speech recognition
- [sounddevice](https://python-sounddevice.readthedocs.io/) - Audio capture
- [keyboard](https://github.com/boppreh/keyboard) - Global hotkeys
- [pyperclip](https://github.com/asweigart/pyperclip) - Clipboard operations
- [numpy](https://numpy.org/) - Audio processing
- [pystray](https://github.com/moses-palmer/pystray) - System tray (GUI version)
- [Pillow](https://pillow.readthedocs.io/) - Icon generation (GUI version)

## License

MIT License - See [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for the incredible speech recognition model
- Inspired by [Tight.sh](https://tight.sh/) for macOS
