# WhisperVoice → TightWindows Evolution Plan

Transform WhisperVoice into a full **Tight.sh clone for Windows** - a voice-prompting tool for developers that captures context from your screen while you speak.

## Vision

> "Prompting that feels like talking to a teammate looking over your shoulder"

Speak naturally while highlighting code and pointing to elements on your screen. The tool captures everything and formats it into a rich prompt for AI assistants.

---

## Current State (v1.0)

- [x] Local voice-to-text with Whisper
- [x] Hotkey activation (Ctrl+Shift+Space)
- [x] Auto-paste transcribed text
- [x] Modern floating UI indicator
- [x] System tray integration

---

## Target Features (Tight.sh Parity)

### Phase 1: Context Capture Layer

**Goal**: Capture metadata from the active window and selection.

#### 1.1 Active Window Context
- [x] Get active window title and process name (`win32gui`)
- [x] Detect application type (IDE, browser, terminal, etc.)
- [x] Extract file path from window title (VSCode, Notepad++, etc.)

#### 1.2 Selected Text Capture
- [x] Capture selected text from any application
- [x] Method 1: Clipboard sniffing (Ctrl+C simulation)
- [ ] Method 2: UI Automation API for supported apps (optional enhancement)
- [x] Preserve selection metadata (start/end positions if available)

#### 1.3 File Context
- [x] For IDEs: Extract current file path and line number
- [x] For browsers: Extract current URL
- [x] For terminals: Extract current working directory and last command

#### 1.4 Continuous Monitoring (NEW!)
- [x] Background monitor during recording (polls every 200ms)
- [x] Window focus change tracking with timestamps
- [x] Clipboard change detection (multi-selection support)
- [x] Timeline of all context events
- [x] Format timeline for prompt inclusion
- [x] Integrate with whisper_app.py

**Tech Stack**:
- `pywin32` / `win32gui` - Window information
- `pyperclip` - Clipboard operations
- `comtypes` + `UIAutomationCore` - UI Automation
- `threading` - Background monitoring

---

### Phase 2: Point & Speak (UI Element Picker)

**Goal**: Let users select UI elements while speaking.

#### 2.1 Element Picker Overlay
- [ ] Global hotkey to activate picker mode (e.g., Ctrl+Shift+P)
- [ ] Semi-transparent overlay on screen
- [ ] Highlight elements on hover
- [ ] Click to select element

#### 2.2 Element Information Extraction
- [ ] Element type (button, input, link, etc.)
- [ ] Element text/label
- [ ] Element position and size
- [ ] Parent/child hierarchy (limited depth)

#### 2.3 Screenshot Capture
- [ ] Capture selected region
- [ ] Capture specific element bounds
- [ ] Option to include in prompt as base64 or file reference

**Tech Stack**:
- `tkinter` or `PyQt5` - Overlay window
- `UIAutomation` - Element inspection
- `PIL` / `mss` - Screenshots

---

### Phase 3: IDE Integration

**Goal**: Deep integration with development tools.

#### 3.1 VSCode Integration
- [ ] Detect VSCode as active window
- [ ] Extract: file path, line number, selection range
- [ ] Option 1: Parse window title (basic)
- [ ] Option 2: VSCode extension for richer data (advanced)

#### 3.2 Terminal Integration
- [ ] Detect terminal emulators (Windows Terminal, CMD, PowerShell, Git Bash)
- [ ] Capture current directory
- [ ] Capture last command and output (if possible)

#### 3.3 Browser Integration
- [ ] Detect browser as active window
- [ ] Extract current URL from title or accessibility
- [ ] Optional: Browser extension for DOM selection

**Tech Stack**:
- Window title parsing (regex patterns)
- `psutil` - Process information
- Optional: VSCode extension API, Chrome Native Messaging

---

### Phase 4: Prompt Assembly & Output

**Goal**: Format captured context into useful prompts.

#### 4.1 Prompt Templates
- [x] Default template with context sections
- [x] Customizable templates (user config)
- [x] Smart formatting based on context type

#### 4.2 Output Options
- [ ] Clipboard (current behavior)
- [ ] Direct paste at cursor
- [ ] Send to Claude Code CLI
- [ ] Send to Cursor/Windsurf
- [ ] Save to file

#### 4.3 Prompt Format Example
```markdown
## Voice Input
{transcribed_text}

## Context
- **Application**: VSCode
- **File**: `src/components/Button.tsx`
- **Line**: 42-58

## Selected Code
```typescript
{selected_code}
```

## Screenshot
[Attached: element_screenshot.png]
```

---

### Phase 5: Configuration & Polish

#### 5.1 Settings UI
- [ ] Hotkey customization
- [ ] Model selection (tiny/base/small/medium)
- [ ] Output destination
- [ ] Template editor

#### 5.2 Performance
- [ ] Lazy model loading
- [ ] GPU acceleration (CUDA) option
- [ ] Faster model options (whisper.cpp, faster-whisper)

#### 5.3 UX Polish
- [ ] Improved visual feedback
- [ ] Sound effects toggle
- [ ] Onboarding flow
- [ ] Error messages

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    TightWindows                         │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Voice     │  │   Context   │  │   Element   │     │
│  │   Capture   │  │   Capture   │  │   Picker    │     │
│  │  (Whisper)  │  │  (Win32)    │  │  (UIA)      │     │
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

## Implementation Order

1. **Phase 1.1** - Active window context (quick win) ✅
2. **Phase 1.2** - Selected text capture ✅
3. **Phase 4.1** - Basic prompt assembly ✅
4. **Phase 1.3** - File/URL context ✅
5. **Phase 1.4** - Continuous monitoring & timeline ✅
6. **Phase 3.1** - VSCode integration
7. **Phase 2** - Element picker (complex)
8. **Phase 5** - Polish and settings

---

## Dependencies to Add

```txt
# requirements.txt additions
pywin32          # Windows API access
comtypes         # UI Automation
psutil           # Process info
mss              # Fast screenshots
```

---

## Quick Start for Next Session

```
Resume context:
- Project: WhisperVoice (C:\Users\andri\IdeaProjects\WhisperToTerminal)
- Goal: Transform into Tight.sh clone for Windows
- Start with: Phase 1.1 - Active window context capture
- Main file to modify: whisper_app.py
- Add new module: context_capture.py
```

---

## References

- [Tight.sh](https://tight.sh/) - macOS inspiration
- [pywin32 docs](https://github.com/mhammond/pywin32)
- [UI Automation Python](https://github.com/yinkaisheng/Python-UIAutomation-for-Windows)
- [faster-whisper](https://github.com/guillaumekln/faster-whisper) - 4x faster inference
