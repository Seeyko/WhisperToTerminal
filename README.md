# WhisperVoice

> **Voice prompting that feels like talking to a teammate looking over your shoulder**

A Windows voice-to-text application that captures your screen context while you speak. Press a hotkey, speak naturally while pointing at code or UI elements, and get a rich AI-ready prompt with all the context included.

**Inspired by [Tight.sh](https://tight.sh/) for macOS** - now available for Windows.

**100% local and offline** - No internet connection required after initial model download.

## What Makes This Different

Unlike simple voice-to-text tools, WhisperVoice **continuously monitors your context** while you speak:

| You're Working In | What Gets Captured |
|-------------------|-------------------|
| **VSCode/Cursor/Windsurf** | File path, line number, selected code, language |
| **Chrome/Edge/Firefox** | URL, page title, selected text |
| **Terminal** | Working directory, shell type, admin status |
| **Any Application** | Window title, app type, selected text |

### Continuous Monitoring (NEW!)

**While you're recording**, WhisperVoice tracks:
- **Window switches** - Navigate between apps, each switch is timestamped
- **Multiple selections** - Select text in different windows, all captured
- **Timeline of actions** - Every selection and window focus is correlated with your speech

**No extra hotkeys needed** - just speak and point. Select code in VSCode, switch to Chrome to grab a URL, select more code - everything is captured with timestamps showing when each action happened during your recording.

## Example Output

### Simple Recording
When you say "Can you explain this function?" while having code selected in VSCode:

```markdown
## Voice Input
Can you explain this function?

## Context
- **Application**: Code
- **File**: `C:\dev\myproject\main.py`
- **Line**: 42

## Selected Code
```python
def calculate_total(items):
    return sum(item.price for item in items)
```
```

### Multi-Selection Recording (NEW!)
When you navigate between windows and select multiple texts while speaking:

```markdown
## Voice Input
I'm seeing an error in the API response. Here's the endpoint code and the browser showing the error.

## Selected Code/Text

### From Code - `api/routes.py`

**[1.2s]**
```python
@app.route('/users')
def get_users():
    return jsonify(users)
```

### From Chrome - `localhost:3000/users`

**[3.8s]**
```
TypeError: Cannot read property 'map' of undefined
```

## Context Timeline

- [0.0s] Recording started
- [0.0s] Switched to **Code** - `api/routes.py`
- [1.2s] Selected: "@app.route('/users')..."
- [2.5s] Switched to **Chrome** - `localhost:3000/users`
- [3.8s] Selected: "TypeError: Cannot read..."
- [5.1s] Recording stopped
```

This rich prompt is automatically copied to your clipboard and pasted - ready for Claude, ChatGPT, or any AI assistant.

## Features

- **Single Hotkey**: Press `Ctrl+Shift+Space` to start/stop recording
- **Continuous Monitoring**: Tracks window switches and selections while you speak
- **Multi-Selection**: Select text in multiple windows, all captured with timestamps
- **Context Timeline**: See when each action happened relative to your speech
- **Smart Formatting**: Templates adapt to IDE, browser, or terminal context
- **Code Detection**: Auto-detects 40+ programming languages for syntax highlighting
- **Multi-Language**: Voice recognition supports 16+ languages with auto-detection
- **Local Inference**: Runs entirely on your machine using OpenAI Whisper
- **Modern UI**: Floating pill-shaped indicator with status colors
- **System Tray**: Runs quietly in the background

## Quick Start

### Prerequisites
- Windows 10/11
- Python 3.10+
- A working microphone

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/WhisperVoice.git
cd WhisperVoice

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python whisper_app.py
```

On first launch, Whisper downloads the `small` model (~461 MB). This only happens once.

## Usage

1. **Start the application** - A small indicator appears at the bottom of your screen
2. **Press `Ctrl+Shift+Space`** - Recording starts (indicator turns pink)
3. **Speak and point** - Talk while selecting code, switching windows, copying text
4. **Press `Ctrl+Shift+Space` again** - Recording stops (indicator turns yellow)
5. **Rich prompt is pasted** - Voice + all selections + context timeline, formatted as markdown

### Continuous Monitoring Workflow

While recording, you can:
- **Switch windows freely** - Each focus change is logged with timestamp
- **Select multiple texts** - Use Ctrl+C in any app, each selection is captured
- **Navigate your codebase** - Open files, scroll, select different snippets
- **Reference browser content** - Switch to browser, select error messages or docs

Everything is captured with timestamps that correlate with your speech!

### Tips

- No need to pre-select text - select while speaking for natural workflow
- Works in any application - IDEs, browsers, terminals, text editors
- Timestamps help the AI understand the sequence of what you're showing
- Speak naturally - Whisper handles accents and background noise well

## Project Structure

```
WhisperVoice/
├── whisper_app.py           # Entry point (thin wrapper)
├── src/
│   └── whispervoice/        # Main package
│       ├── app.py           # Application orchestration
│       ├── core/            # Core functionality
│       │   ├── audio.py     # Audio recording
│       │   └── transcription.py  # Whisper transcription
│       ├── context/         # Context capture
│       │   ├── capture.py   # Window/selection capture
│       │   ├── monitor.py   # Continuous monitoring
│       │   └── types.py     # Data classes
│       ├── output/          # Output formatting
│       │   └── assembler.py # Prompt assembly
│       └── ui/              # User interface
│           ├── indicator.py # Floating indicator
│           └── tray.py      # System tray
├── tests/                   # Unit tests (93 tests)
│   ├── test_context.py
│   └── test_output.py
├── requirements.txt
└── README.md
```

## Configuration

Edit constants in `whisper_app.py`:

```python
HOTKEY = "ctrl+shift+space"  # Change the activation hotkey
MODEL_NAME = "small"         # Whisper model size
```

### Custom Prompt Templates

Create `~/.whispervoice/templates.json` to customize prompt formatting:

```json
{
    "my_template": "Request: $voice_input\n\nCode:\n$selected_section"
}
```

### Whisper Models

| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| `tiny` | 39 MB | Fastest | Lower |
| `base` | 74 MB | Fast | Good |
| `small` | 244 MB | Medium | Better |
| `medium` | 769 MB | Slow | High |
| `large` | 1550 MB | Slowest | Highest |

## How Context Capture Works

WhisperVoice uses multiple techniques to capture context:

1. **Window Information** (`win32gui`) - Gets active window title and process name
2. **Title Parsing** - Extracts file paths, line numbers from IDE window titles
3. **UI Automation** (`comtypes`) - Reads browser URL bars, status bars
4. **Clipboard Monitoring** - Detects when you copy text (Ctrl+C) in any app

### Continuous Monitoring (While Recording)

When you press the hotkey to start recording:
1. A **background monitor** starts polling every 200ms
2. **Window focus changes** are detected and logged with timestamps
3. **Clipboard changes** are detected (when you Ctrl+C anywhere)
4. Each event is added to a **timeline** with relative timestamps

When you stop recording:
1. The monitor stops and returns the complete timeline
2. Your voice is transcribed
3. Everything is assembled into a rich, timestamped prompt

This allows you to **speak naturally while demonstrating** - point at code, switch windows, select error messages - and have everything captured in context.

## Supported Applications

### IDEs & Editors
- Visual Studio Code, Cursor, Windsurf
- JetBrains IDEs (IntelliJ, PyCharm, WebStorm, etc.)
- Visual Studio, Notepad++, Sublime Text

### Browsers
- Chrome, Edge, Firefox, Brave, Arc
- URL extraction via UI Automation

### Terminals
- Windows Terminal, PowerShell, Command Prompt
- Git Bash, Alacritty, WezTerm
- Working directory and shell detection

## Troubleshooting

### "No audio recorded"
- Check microphone is working and selected as default input
- Ensure recording is at least 0.5 seconds

### Context not captured
- Make sure the target window is focused when you press the hotkey
- Some applications may not expose title information

### Hotkey conflicts
- Another app may be using `Ctrl+Shift+Space`
- Try running as administrator

## Dependencies

- [openai-whisper](https://github.com/openai/whisper) - Speech recognition
- [pywin32](https://github.com/mhammond/pywin32) - Windows API access
- [comtypes](https://github.com/enthought/comtypes) - UI Automation
- [psutil](https://github.com/giampaolo/psutil) - Process information
- [sounddevice](https://python-sounddevice.readthedocs.io/) - Audio capture
- [keyboard](https://github.com/boppreh/keyboard) - Global hotkeys
- [pyperclip](https://github.com/asweigart/pyperclip) - Clipboard operations

## License

MIT License - See [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Roadmap

- [x] Phase 1.1: Active window context capture
- [x] Phase 1.2: Selected text capture
- [x] Phase 1.3: Deep file/URL/terminal context
- [x] Phase 1.4: Continuous monitoring & timeline
- [x] Phase 4.1: Smart prompt templates
- [ ] Phase 2: Point & Speak (UI element picker)
- [ ] Phase 3: Deep IDE integration
- [ ] Phase 4.2: Output to Claude Code CLI
- [ ] Phase 5: Settings UI & polish

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for the incredible speech recognition model
- [Tight.sh](https://tight.sh/) for the inspiration
