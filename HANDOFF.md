# WhisperVoice Native - Development Handoff Document

## Project Overview

Transform **WhisperVoice** from a Python/tkinter app into a **robust, beautiful native desktop application** using **Tauri + SvelteKit** with glassmorphism UI and GPU-accelerated transcription.

**Goal**: Achieve Cluely-level UI quality with:
- True Windows glassmorphism (Acrylic/Mica effects)
- Smooth animations
- Real-time waveform visualization
- GPU-accelerated Whisper transcription, with a wrapper to be able to plug it into other models (like Microsoft Phi4 ou Nvidia Canary)
- Future: Claude code session sync between my windows computer and my iPhone sync with push notifications, session live prompting etc...

---

## Current State

### What's Been Created
- **Tauri + Svelte project scaffolded** at `whispervoice-native/`
- **npm dependencies installed**
- **Base project structure** in place

### What's Missing
- **Rust not installed** - Need to install Rust toolchain
- **Rust dependencies not configured** - Need to update Cargo.toml
- **Glassmorphism UI** - Need to implement
- **Audio/Whisper/Context modules** - Need to implement
- Moving all to bun for better and faster compile and project managment
---

## Prerequisites to Install

### 1. Install Rust
```powershell
# Option A: Using rustup (recommended)
winget install Rustlang.Rustup

# Or download from: https://rustup.rs/

# After install, verify:
rustc --version
cargo --version
```

### 2. Install Visual Studio Build Tools (if not present)
Required for Windows native compilation:
```powershell
winget install Microsoft.VisualStudio.2022.BuildTools
```

### 3. CUDA Toolkit (optional, for GPU acceleration)
```powershell
# For NVIDIA GPU acceleration
winget install Nvidia.CUDA
```

---

## Tasks to Complete

### Task 1: Update Cargo.toml with Dependencies

**File**: `whispervoice-native/src-tauri/Cargo.toml`

Replace the contents with:

```toml
[package]
name = "whispervoice-native"
version = "0.1.0"
description = "WhisperVoice - Voice-to-text with context capture"
authors = ["Andri"]
edition = "2021"

[lib]
name = "whispervoice_native_lib"
crate-type = ["staticlib", "cdylib", "rlib"]

[build-dependencies]
tauri-build = { version = "2", features = [] }

[dependencies]
tauri = { version = "2", features = ["tray-icon"] }
tauri-plugin-opener = "2"
tauri-plugin-global-shortcut = "2"
tauri-plugin-clipboard-manager = "2"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
tokio = { version = "1", features = ["full"] }

# Audio capture
cpal = "0.15"
ringbuf = "0.3"

# Whisper transcription (comment out initially if causing build issues)
# whisper-rs = "0.11"

# Windows APIs
[target.'cfg(windows)'.dependencies]
windows = { version = "0.58", features = [
    "Win32_UI_WindowsAndMessaging",
    "Win32_UI_Accessibility",
    "Win32_System_ProcessStatus",
    "Win32_Foundation",
    "Win32_System_Threading"
]}
window-vibrancy = "0.5"

# State persistence
rusqlite = { version = "0.31", features = ["bundled"] }

# Logging
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }

# Error handling
thiserror = "1"
anyhow = "1"

[features]
default = []
cuda = []
```

---

### Task 2: Configure Tauri for Glassmorphism Window

**File**: `whispervoice-native/src-tauri/tauri.conf.json`

Replace with:

```json
{
  "$schema": "https://schema.tauri.app/config/2",
  "productName": "WhisperVoice",
  "version": "0.1.0",
  "identifier": "com.whispervoice.app",
  "build": {
    "beforeDevCommand": "npm run dev",
    "devUrl": "http://localhost:1420",
    "beforeBuildCommand": "npm run build",
    "frontendDist": "../build"
  },
  "app": {
    "windows": [
      {
        "title": "WhisperVoice",
        "width": 300,
        "height": 80,
        "resizable": false,
        "decorations": false,
        "transparent": true,
        "alwaysOnTop": true,
        "skipTaskbar": true,
        "center": false,
        "x": 100,
        "y": 100
      }
    ],
    "security": {
      "csp": null
    },
    "trayIcon": {
      "iconPath": "icons/icon.png",
      "iconAsTemplate": true
    }
  },
  "bundle": {
    "active": true,
    "targets": "all",
    "icon": [
      "icons/32x32.png",
      "icons/128x128.png",
      "icons/128x128@2x.png",
      "icons/icon.icns",
      "icons/icon.ico"
    ]
  },
  "plugins": {
    "global-shortcut": {}
  }
}
```

---

### Task 3: Update main.rs with Glassmorphism Setup

**File**: `whispervoice-native/src-tauri/src/main.rs`

Replace with:

```rust
// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::Manager;

#[cfg(target_os = "windows")]
use window_vibrancy::apply_acrylic;

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .plugin(tauri_plugin_clipboard_manager::init())
        .setup(|app| {
            let window = app.get_webview_window("main").unwrap();

            // Apply Windows Acrylic effect for glassmorphism
            #[cfg(target_os = "windows")]
            {
                apply_acrylic(&window, Some((18, 18, 18, 200)))
                    .expect("Failed to apply acrylic effect");
            }

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            get_app_state,
            start_recording,
            stop_recording,
            get_waveform_data,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

// Tauri commands
#[tauri::command]
fn get_app_state() -> AppState {
    AppState {
        is_recording: false,
        status: "Ready".to_string(),
    }
}

#[tauri::command]
async fn start_recording() -> Result<(), String> {
    // TODO: Implement audio recording
    Ok(())
}

#[tauri::command]
async fn stop_recording() -> Result<String, String> {
    // TODO: Implement transcription
    Ok("Transcribed text".to_string())
}

#[tauri::command]
fn get_waveform_data() -> Vec<f32> {
    // TODO: Return real waveform data
    vec![0.1, 0.3, 0.5, 0.7, 0.5, 0.3, 0.1]
}

#[derive(serde::Serialize)]
struct AppState {
    is_recording: bool,
    status: String,
}
```

---

### Task 4: Update lib.rs

**File**: `whispervoice-native/src-tauri/src/lib.rs`

Replace with:

```rust
pub mod audio;
pub mod context;
pub mod transcription;
pub mod state;

// Re-export main types
pub use audio::AudioRecorder;
pub use context::ContextCapture;
```

Then create the module files:

**File**: `whispervoice-native/src-tauri/src/audio/mod.rs`
```rust
mod recorder;
pub use recorder::AudioRecorder;
```

**File**: `whispervoice-native/src-tauri/src/audio/recorder.rs`
```rust
use std::sync::{Arc, Mutex, atomic::{AtomicBool, Ordering}};
use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use thiserror::Error;

#[derive(Error, Debug)]
pub enum AudioError {
    #[error("No input device found")]
    NoInputDevice,
    #[error("Failed to get default config: {0}")]
    ConfigError(String),
    #[error("Stream error: {0}")]
    StreamError(String),
}

pub struct AudioRecorder {
    buffer: Arc<Mutex<Vec<f32>>>,
    is_recording: Arc<AtomicBool>,
    sample_rate: u32,
}

impl AudioRecorder {
    pub fn new() -> Result<Self, AudioError> {
        Ok(Self {
            buffer: Arc::new(Mutex::new(Vec::new())),
            is_recording: Arc::new(AtomicBool::new(false)),
            sample_rate: 16000,
        })
    }

    pub fn start(&self) -> Result<(), AudioError> {
        self.is_recording.store(true, Ordering::SeqCst);
        // TODO: Start audio stream
        Ok(())
    }

    pub fn stop(&self) -> Vec<f32> {
        self.is_recording.store(false, Ordering::SeqCst);
        let buffer = self.buffer.lock().unwrap();
        buffer.clone()
    }

    pub fn get_waveform(&self) -> Vec<f32> {
        // Return last N samples for visualization
        let buffer = self.buffer.lock().unwrap();
        let len = buffer.len();
        if len > 64 {
            buffer[len-64..].to_vec()
        } else {
            buffer.clone()
        }
    }
}
```

**File**: `whispervoice-native/src-tauri/src/context/mod.rs`
```rust
mod capture;
pub use capture::ContextCapture;
```

**File**: `whispervoice-native/src-tauri/src/context/capture.rs`
```rust
use serde::Serialize;

#[derive(Debug, Clone, Serialize)]
pub enum AppType {
    Ide,
    Browser,
    Terminal,
    Editor,
    Unknown,
}

#[derive(Debug, Clone, Serialize)]
pub struct WindowContext {
    pub title: String,
    pub process_name: String,
    pub app_type: AppType,
    pub file_path: Option<String>,
    pub url: Option<String>,
}

pub struct ContextCapture;

impl ContextCapture {
    pub fn new() -> Self {
        Self
    }

    pub fn get_active_window(&self) -> Option<WindowContext> {
        #[cfg(target_os = "windows")]
        {
            // TODO: Implement Windows context capture using windows-rs
            Some(WindowContext {
                title: "Test Window".to_string(),
                process_name: "test.exe".to_string(),
                app_type: AppType::Unknown,
                file_path: None,
                url: None,
            })
        }

        #[cfg(not(target_os = "windows"))]
        None
    }
}
```

**File**: `whispervoice-native/src-tauri/src/transcription/mod.rs`
```rust
// TODO: Add whisper-rs integration
pub struct WhisperEngine;

impl WhisperEngine {
    pub fn new(_model: &str) -> Self {
        Self
    }

    pub fn transcribe(&self, _audio: &[f32]) -> String {
        // TODO: Implement actual transcription
        "Transcribed text placeholder".to_string()
    }
}
```

**File**: `whispervoice-native/src-tauri/src/state/mod.rs`
```rust
// TODO: Add SQLite state persistence
pub struct StateManager;
```

---

### Task 5: Create Glassmorphism UI Components

**File**: `whispervoice-native/src/lib/components/FloatingPill.svelte`

```svelte
<script lang="ts">
  import { invoke } from "@tauri-apps/api/core";
  import { onMount, onDestroy } from "svelte";

  let isRecording = $state(false);
  let statusText = $state("Ready");
  let recordingTime = $state("0:00");
  let waveformData = $state<number[]>([]);

  let animationFrame: number;
  let startTime: number;

  async function toggleRecording() {
    if (isRecording) {
      const result = await invoke<string>("stop_recording");
      isRecording = false;
      statusText = "Ready";
      console.log("Transcribed:", result);
    } else {
      await invoke("start_recording");
      isRecording = true;
      statusText = "Recording...";
      startTime = Date.now();
      updateTimer();
    }
  }

  function updateTimer() {
    if (!isRecording) return;

    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;
    recordingTime = `${minutes}:${seconds.toString().padStart(2, '0')}`;

    animationFrame = requestAnimationFrame(updateTimer);
  }

  async function fetchWaveform() {
    if (isRecording) {
      waveformData = await invoke<number[]>("get_waveform_data");
    }
    setTimeout(fetchWaveform, 50);
  }

  onMount(() => {
    fetchWaveform();
  });

  onDestroy(() => {
    if (animationFrame) cancelAnimationFrame(animationFrame);
  });
</script>

<button
  class="floating-pill"
  class:recording={isRecording}
  onclick={toggleRecording}
>
  <div class="status-dot" class:pulse={isRecording}></div>

  {#if isRecording}
    <div class="waveform">
      {#each waveformData as value, i}
        <div
          class="bar"
          style="height: {Math.max(4, value * 24)}px"
        ></div>
      {/each}
    </div>
    <span class="timer">{recordingTime}</span>
  {:else}
    <span class="status-text">{statusText}</span>
  {/if}
</button>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    background: transparent;
    overflow: hidden;
  }

  .floating-pill {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 20px;
    border-radius: 28px;
    border: none;
    cursor: pointer;

    /* Glassmorphism - the blur comes from window-vibrancy */
    background: rgba(30, 30, 46, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow:
      0 8px 32px rgba(0, 0, 0, 0.4),
      inset 0 1px 0 rgba(255, 255, 255, 0.1);

    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  }

  .floating-pill:hover {
    transform: scale(1.02);
    box-shadow:
      0 12px 40px rgba(0, 0, 0, 0.5),
      inset 0 1px 0 rgba(255, 255, 255, 0.15);
  }

  .floating-pill.recording {
    background: rgba(243, 139, 168, 0.15);
    border-color: rgba(243, 139, 168, 0.3);
  }

  .status-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #a6e3a1;
    transition: all 0.3s ease;
    flex-shrink: 0;
  }

  .status-dot.pulse {
    background: #f38ba8;
    animation: pulse 1.5s ease-in-out infinite;
  }

  @keyframes pulse {
    0%, 100% {
      box-shadow: 0 0 0 0 rgba(243, 139, 168, 0.5);
      transform: scale(1);
    }
    50% {
      box-shadow: 0 0 0 8px rgba(243, 139, 168, 0);
      transform: scale(1.1);
    }
  }

  .status-text {
    color: #cdd6f4;
    font-size: 14px;
    font-weight: 500;
  }

  .timer {
    color: #f38ba8;
    font-size: 14px;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
  }

  .waveform {
    display: flex;
    align-items: center;
    gap: 2px;
    height: 24px;
  }

  .bar {
    width: 3px;
    background: #f38ba8;
    border-radius: 2px;
    transition: height 0.05s ease;
  }
</style>
```

---

### Task 6: Update Main Page

**File**: `whispervoice-native/src/routes/+page.svelte`

Replace with:

```svelte
<script lang="ts">
  import FloatingPill from "$lib/components/FloatingPill.svelte";
</script>

<main>
  <FloatingPill />
</main>

<style>
  main {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background: transparent;
  }
</style>
```

---

### Task 7: Create Component Directory

Create the components directory structure:

```
whispervoice-native/src/lib/components/FloatingPill.svelte
```

---

### Task 8: Update app.html for Transparency

**File**: `whispervoice-native/src/app.html`

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%sveltekit.assets%/favicon.png" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>WhisperVoice</title>
    <style>
      html, body {
        margin: 0;
        padding: 0;
        background: transparent !important;
        overflow: hidden;
      }
    </style>
    %sveltekit.head%
  </head>
  <body data-sveltekit-preload-data="hover">
    <div style="display: contents">%sveltekit.body%</div>
  </body>
</html>
```

---

## Build & Run Commands

After completing the tasks above:

```bash
cd whispervoice-native

# Install Rust dependencies and build
npm run tauri dev

# Build for production
npm run tauri build
```

---

## Project Structure After Tasks

```
whispervoice-native/
├── src-tauri/
│   ├── Cargo.toml              # Updated with dependencies
│   ├── tauri.conf.json         # Updated for glassmorphism window
│   └── src/
│       ├── main.rs             # Updated with vibrancy setup
│       ├── lib.rs              # Module exports
│       ├── audio/
│       │   ├── mod.rs
│       │   └── recorder.rs     # Audio capture
│       ├── context/
│       │   ├── mod.rs
│       │   └── capture.rs      # Window context capture
│       ├── transcription/
│       │   └── mod.rs          # Whisper integration (TODO)
│       └── state/
│           └── mod.rs          # SQLite persistence (TODO)
├── src/
│   ├── app.html                # Updated for transparency
│   ├── lib/
│   │   └── components/
│   │       └── FloatingPill.svelte  # Main UI component
│   └── routes/
│       └── +page.svelte        # Updated main page
└── package.json
```

---

## Key Technologies

| Component | Library | Purpose |
|-----------|---------|---------|
| Framework | Tauri 2 | Native app shell |
| Frontend | Svelte 5 | Reactive UI |
| Glassmorphism | window-vibrancy | Windows Acrylic/Mica |
| Audio | cpal | Cross-platform audio capture |
| Transcription | whisper-rs | Speech-to-text (TODO) |
| Windows API | windows-rs | Context capture |
| State | rusqlite | Settings persistence |

---

## References

- [Tauri v2 Docs](https://v2.tauri.app/)
- [window-vibrancy](https://github.com/tauri-apps/window-vibrancy)
- [whisper-rs](https://github.com/tazz4843/whisper-rs)
- [cpal](https://github.com/RustAudio/cpal)
- [Catppuccin Colors](https://github.com/catppuccin/catppuccin)

---

## Summary of What Needs to Be Done

1. **Install Rust** (prerequisite)
2. **Update Cargo.toml** with dependencies
3. **Update tauri.conf.json** for transparent window
4. **Update main.rs** with glassmorphism setup
5. **Create Rust modules** (audio, context, transcription, state)
6. **Create FloatingPill.svelte** component
7. **Update +page.svelte** to use FloatingPill
8. **Update app.html** for transparency
9. **Run `npm run tauri dev`** to test

The glassmorphism effect should work immediately once Rust is installed and the project builds.

You can adapt the plan while you make it.
You must read online resources before creatings apps, for up to date install and documentation and catch all the latest versions of the framework you use.