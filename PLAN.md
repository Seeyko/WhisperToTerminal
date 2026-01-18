# WhisperVoice → TightWindows Evolution Plan

Transform WhisperVoice into a full **Tight.sh clone for Windows** - a voice-prompting tool for developers that captures context from your screen while you speak.

## Vision

> "Prompting that feels like talking to a teammate looking over your shoulder"

Speak naturally while highlighting code and pointing to elements on your screen. The tool captures everything and formats it into a rich prompt for AI assistants.

---

## Current State (v2.0)

### Completed Features
- [x] Local voice-to-text with Whisper
- [x] Hotkey activation (Ctrl+Shift+Space)
- [x] Auto-paste transcribed text
- [x] Modern floating UI indicator
- [x] System tray integration
- [x] Continuous context monitoring during recording
- [x] Multi-selection support with timestamps
- [x] Window focus tracking
- [x] Smart prompt templates (IDE, browser, terminal)
- [x] 40+ programming language detection
- [x] **Refactored src/ package structure**
- [x] **GitHub Actions CI/CD for building .exe**

### Project Structure (v2.0)
```
WhisperVoice/
├── whisper_app.py           # Entry point (thin wrapper)
├── src/whispervoice/        # Main package
│   ├── app.py               # Application orchestration
│   ├── core/
│   │   ├── audio.py         # AudioRecorder class
│   │   └── transcription.py # WhisperTranscriber class
│   ├── context/
│   │   ├── capture.py       # Window/selection capture
│   │   ├── monitor.py       # Continuous monitoring
│   │   └── types.py         # Data classes
│   ├── output/
│   │   └── assembler.py     # Prompt assembly
│   └── ui/
│       ├── indicator.py     # Floating indicator
│       └── tray.py          # System tray
├── tests/                   # 93 unit tests
├── .github/workflows/       # CI/CD
│   └── build.yml            # Build .exe on push
├── WhisperVoice.spec        # PyInstaller config
└── requirements.txt
```

---

## Building the App

### Local Build
```bash
# Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# Run tests
python -m pytest tests/ -v

# Build executable
pyinstaller WhisperVoice.spec

# Output: dist/WhisperVoice.exe
```

### GitHub Actions (Automatic)
- Builds on every push to master/main
- Builds on pull requests
- Uploads artifact: `WhisperVoice-Windows`
- Attaches to releases automatically

---

## Future Improvements (TODO)

### Phase 5: UI/UX Polish (HIGH PRIORITY)

#### 5.1 Modern UI Redesign
- [ ] **Catppuccin/Dracula theme support** - Match modern dev tool aesthetics
- [ ] **Glassmorphism indicator** - Frosted glass effect on Windows 11
- [ ] **Smooth animations** - Fade in/out, pulse effects
- [ ] **Recording waveform visualization** - Show audio levels while recording
- [ ] **Toast notifications** - Non-intrusive status updates

#### 5.2 Robustness & Error Handling
- [ ] **Graceful microphone errors** - Clear message if mic unavailable
- [ ] **Model download progress** - Show download bar on first launch
- [ ] **Retry logic** - Auto-retry on transient failures
- [ ] **Crash recovery** - Restore state after unexpected exit
- [ ] **Logging system** - Debug logs for troubleshooting

#### 5.3 Settings UI
- [ ] **Settings window** - GUI for configuration
- [ ] **Hotkey customization** - Let users change shortcuts
- [ ] **Model selection** - Switch between tiny/base/small/medium
- [ ] **Theme selection** - Light/dark/system
- [ ] **Output destination** - Clipboard, file, or direct to app

#### 5.4 Audio Feedback
- [ ] **Sound effects** - Beeps for start/stop/error
- [ ] **Volume indicator** - Show if mic is picking up audio
- [ ] **Silence detection** - Auto-stop after prolonged silence

---

### Phase 6: Performance Optimization

#### 6.1 Faster Transcription
- [ ] **faster-whisper integration** - 4x faster inference
- [ ] **GPU acceleration** - CUDA support for NVIDIA GPUs
- [ ] **Streaming transcription** - Show words as they're recognized
- [ ] **Model caching** - Keep model in memory between recordings

#### 6.2 Resource Optimization
- [ ] **Lazy loading** - Only load Whisper when first recording
- [ ] **Memory management** - Unload model when idle
- [ ] **Startup optimization** - Faster app launch

---

### Phase 7: Advanced Features

#### 7.1 Screenshot Support
- [ ] **Screen region capture** - Select area to include
- [ ] **Window screenshot** - Capture active window
- [ ] **Clipboard image support** - Include copied images
- [ ] **Base64 encoding** - For AI API compatibility

#### 7.2 Output Integrations
- [ ] **Claude Code CLI** - Direct pipe to `claude`
- [ ] **Cursor integration** - Paste into Cursor chat
- [ ] **Windsurf integration** - Native Windsurf support
- [ ] **File export** - Save prompts to markdown files

#### 7.3 Advanced Context
- [ ] **Git context** - Current branch, recent commits
- [ ] **LSP integration** - Symbol information from language servers
- [ ] **Error context** - Capture terminal errors automatically

---

## Known Issues / Bugs to Fix

- [ ] **UI Automation occasionally fails** - Browser URL extraction not 100% reliable
- [ ] **High CPU during monitoring** - Optimize polling interval
- [ ] **Clipboard race conditions** - Rare issues with rapid selections
- [ ] **PyInstaller warnings** - Clean up hidden imports

---

## Quick Start for Next Session

```
Resume context:
- Project: WhisperVoice (C:\Users\andri\IdeaProjects\WhisperToTerminal)
- Package: src/whispervoice/
- Entry point: whisper_app.py
- Tests: python -m pytest tests/ -v
- Build: pyinstaller WhisperVoice.spec

Current priorities:
1. Phase 5.1 - Modern UI redesign (glassmorphism, animations)
2. Phase 5.2 - Robustness improvements (error handling)
3. Phase 6.1 - faster-whisper integration for speed

Key files to modify:
- src/whispervoice/ui/indicator.py - UI improvements
- src/whispervoice/core/transcription.py - faster-whisper
- src/whispervoice/app.py - New features integration
```

---

## Target Features (Tight.sh Parity)

### Phase 1: Context Capture Layer ✅ COMPLETE

#### 1.1 Active Window Context ✅
- [x] Get active window title and process name
- [x] Detect application type (IDE, browser, terminal, etc.)
- [x] Extract file path from window title

#### 1.2 Selected Text Capture ✅
- [x] Capture selected text from any application
- [x] Clipboard sniffing (Ctrl+C simulation)
- [x] Preserve selection metadata

#### 1.3 File Context ✅
- [x] For IDEs: Extract current file path and line number
- [x] For browsers: Extract current URL
- [x] For terminals: Extract current working directory

#### 1.4 Continuous Monitoring ✅
- [x] Background monitor during recording
- [x] Window focus change tracking with timestamps
- [x] Clipboard change detection (multi-selection)
- [x] Timeline of all context events

---

### Phase 2: Point & Speak (UI Element Picker)

**Goal**: Let users select UI elements while speaking.

- [ ] Global hotkey to activate picker mode
- [ ] Semi-transparent overlay on screen
- [ ] Highlight elements on hover
- [ ] Click to select element
- [ ] Extract element type, text, position

**Tech Stack**: tkinter, UIAutomation, PIL/mss

---

### Phase 3: IDE Integration

**Goal**: Deep integration with development tools.

- [ ] VSCode extension for richer data
- [ ] Terminal command/output capture
- [ ] Browser extension for DOM selection

---

### Phase 4: Prompt Assembly & Output ✅ PARTIAL

#### 4.1 Prompt Templates ✅
- [x] Default template with context sections
- [x] Customizable templates (user config)
- [x] Smart formatting based on context type

#### 4.2 Output Options (TODO)
- [x] Clipboard paste
- [ ] Direct paste at cursor
- [ ] Send to Claude Code CLI
- [ ] Send to Cursor/Windsurf
- [ ] Save to file

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    WhisperVoice                          │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Voice     │  │   Context   │  │   Context   │     │
│  │   Capture   │  │   Capture   │  │   Monitor   │     │
│  │  (Whisper)  │  │  (Win32)    │  │ (Timeline)  │     │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘     │
│         │                │                │             │
│         └────────────────┼────────────────┘             │
│                          ▼                              │
│                ┌─────────────────┐                      │
│                │ Prompt Assembler │                      │
│                └────────┬────────┘                      │
│                         ▼                              │
│         ┌───────────────┼───────────────┐              │
│         ▼               ▼               ▼              │
│    ┌─────────┐    ┌─────────┐    ┌─────────┐          │
│    │Clipboard│    │Claude   │    │  File   │          │
│    │  Paste  │    │  Code   │    │  Save   │          │
│    └─────────┘    └─────────┘    └─────────┘          │
└─────────────────────────────────────────────────────────┘
```

---

## References

- [Tight.sh](https://tight.sh/) - macOS inspiration
- [faster-whisper](https://github.com/guillaumekln/faster-whisper) - 4x faster inference
- [pywin32 docs](https://github.com/mhammond/pywin32)
- [UI Automation Python](https://github.com/yinkaisheng/Python-UIAutomation-for-Windows)
- [Catppuccin](https://github.com/catppuccin) - Modern color palette
