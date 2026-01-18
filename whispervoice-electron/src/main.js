const { app, BrowserWindow, ipcMain, clipboard, globalShortcut } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');

// Single instance lock - prevent multiple instances
const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    // Focus the window if a second instance is launched
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });
}

let mainWindow;
let settingsExpanded = false;

// Settings storage
let appSettings = {
  model: 'medium',
  cudaAvailable: false,
  device: 'cpu',
  autoPaste: true,
  alwaysOnTop: true,
  startMinimized: false,
  shortcut: 'CommandOrControl+Shift+Space',
  colorIdle: '#18181b',
  colorRecording: '#321923',
  colorAccent: '#f472b6',
  pillWidth: 220,
  pillHeight: 90,
  pillRadius: 26
};

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 260,
    height: 90,
    x: 100,
    y: 100,
    frame: false,
    transparent: true,
    alwaysOnTop: appSettings.alwaysOnTop !== false,
    skipTaskbar: true,
    resizable: false,
    hasShadow: false,
    backgroundColor: '#00000000',
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    }
  });

  // Don't use backgroundMaterial - it adds a visible backdrop
  // We want pure transparency with only the pill visible

  mainWindow.loadFile(path.join(__dirname, 'index.html'));

  // Remove menu
  mainWindow.setMenu(null);

  // Prevent window from showing in alt-tab
  mainWindow.setSkipTaskbar(true);

}

// Customizable shortcut - change this to your preferred key combo
const TOGGLE_SHORTCUT = 'CommandOrControl+Shift+Space';

app.whenReady().then(() => {
  createWindow();

  // Register global shortcut to toggle recording
  globalShortcut.register(TOGGLE_SHORTCUT, () => {
    if (mainWindow) {
      mainWindow.webContents.send('toggle-recording');
      mainWindow.show();
    }
  });

  console.log(`Global shortcut registered: ${TOGGLE_SHORTCUT}`);

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('will-quit', () => {
  // Unregister all shortcuts
  globalShortcut.unregisterAll();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// IPC handlers for window dragging (Alt+drag)
ipcMain.handle('get-window-position', () => {
  if (mainWindow) {
    const [x, y] = mainWindow.getPosition();
    return { x, y };
  }
  return { x: 0, y: 0 };
});

ipcMain.on('move-window', (event, x, y) => {
  if (mainWindow) {
    const height = settingsExpanded ? 580 : 90;
    mainWindow.setBounds({
      x: Math.round(x),
      y: Math.round(y),
      width: 260,
      height: height
    });
  }
});

// Resize window when settings expand/collapse
ipcMain.on('resize-window', (event, expanded) => {
  settingsExpanded = expanded;
  if (mainWindow) {
    const [x, y] = mainWindow.getPosition();
    mainWindow.setBounds({
      x: x,
      y: y,
      width: 260,
      height: expanded ? 580 : 90
    });
  }
});

// IPC handlers for recording and transcription

ipcMain.handle('transcribe-audio', async (event, audioBuffer) => {
  try {
    // Save audio buffer to temp WAV file
    const tempFile = path.join(os.tmpdir(), 'whispervoice_recording.wav');

    // Convert Float32Array to 16-bit PCM WAV
    const buffer = Buffer.from(audioBuffer);
    const float32Array = new Float32Array(buffer.buffer, buffer.byteOffset, buffer.length / 4);

    // Create WAV file
    const wavBuffer = createWavBuffer(float32Array, 16000);
    fs.writeFileSync(tempFile, wavBuffer);

    // Transcribe with whisper
    const text = await transcribeAudio(tempFile);

    // Copy to clipboard
    clipboard.writeText(text);

    // Simulate paste (Ctrl+V)
    simulatePaste();

    return { success: true, text };
  } catch (error) {
    console.error('Transcription error:', error);
    return { success: false, error: error.message };
  }
});

function createWavBuffer(samples, sampleRate) {
  const numChannels = 1;
  const bitsPerSample = 16;
  const byteRate = sampleRate * numChannels * bitsPerSample / 8;
  const blockAlign = numChannels * bitsPerSample / 8;
  const dataSize = samples.length * 2; // 16-bit = 2 bytes per sample
  const bufferSize = 44 + dataSize;

  const buffer = Buffer.alloc(bufferSize);
  let offset = 0;

  // RIFF header
  buffer.write('RIFF', offset); offset += 4;
  buffer.writeUInt32LE(bufferSize - 8, offset); offset += 4;
  buffer.write('WAVE', offset); offset += 4;

  // fmt chunk
  buffer.write('fmt ', offset); offset += 4;
  buffer.writeUInt32LE(16, offset); offset += 4; // chunk size
  buffer.writeUInt16LE(1, offset); offset += 2; // PCM format
  buffer.writeUInt16LE(numChannels, offset); offset += 2;
  buffer.writeUInt32LE(sampleRate, offset); offset += 4;
  buffer.writeUInt32LE(byteRate, offset); offset += 4;
  buffer.writeUInt16LE(blockAlign, offset); offset += 2;
  buffer.writeUInt16LE(bitsPerSample, offset); offset += 2;

  // data chunk
  buffer.write('data', offset); offset += 4;
  buffer.writeUInt32LE(dataSize, offset); offset += 4;

  // Write samples
  for (let i = 0; i < samples.length; i++) {
    const sample = Math.max(-1, Math.min(1, samples[i]));
    const intSample = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
    buffer.writeInt16LE(Math.round(intSample), offset);
    offset += 2;
  }

  return buffer;
}

async function transcribeAudio(audioPath) {
  return new Promise((resolve, reject) => {
    // Use faster-whisper via Python script
    const scriptPath = path.join(__dirname, 'transcribe.py');
    const whisper = spawn('python', [scriptPath, audioPath, appSettings.model], { shell: true });

    sendDebugLog('info', `Transcribing with model: ${appSettings.model}`);

    let output = '';
    let errorOutput = '';

    whisper.stdout.on('data', (data) => {
      output += data.toString();
    });

    whisper.stderr.on('data', (data) => {
      errorOutput += data.toString();
      // Only log non-warning messages
      if (!data.toString().includes('UserWarning')) {
        console.log('Whisper:', data.toString());
      }
    });

    whisper.on('error', (err) => {
      console.error('Whisper spawn error:', err);
      reject(new Error('Install faster-whisper: pip install faster-whisper'));
    });

    whisper.on('close', (code) => {
      // Clean up audio file
      try { fs.unlinkSync(audioPath); } catch (e) {}

      if (output.trim()) {
        resolve(output.trim());
      } else {
        resolve('No transcription');
      }
    });
  });
}

function simulatePaste() {
  // Use PowerShell to simulate Ctrl+V
  const ps = spawn('powershell', [
    '-Command',
    `
    Add-Type -AssemblyName System.Windows.Forms
    Start-Sleep -Milliseconds 100
    [System.Windows.Forms.SendKeys]::SendWait('^v')
    `
  ]);
}

// Settings IPC handlers
ipcMain.handle('get-settings', () => {
  return appSettings;
});

ipcMain.handle('get-status', () => {
  return appSettings;
});

ipcMain.handle('set-setting', (event, key, value) => {
  appSettings[key] = value;
  saveSettings();

  // Apply certain settings immediately
  if (key === 'alwaysOnTop' && mainWindow) {
    mainWindow.setAlwaysOnTop(value);
  }

  return true;
});

ipcMain.handle('set-model', (event, model) => {
  appSettings.model = model;
  saveSettings();
  return true;
});

ipcMain.on('open-settings', () => {
  toggleSettingsWindow();
});

function saveSettings() {
  const configPath = path.join(app.getPath('userData'), 'settings.json');
  fs.writeFileSync(configPath, JSON.stringify(appSettings, null, 2));
}

// Send debug log to main window
function sendDebugLog(level, message) {
  if (mainWindow) {
    mainWindow.webContents.send('debug-log', { level, message });
  }
}

// Load settings on startup
function loadSettings() {
  const configPath = path.join(app.getPath('userData'), 'settings.json');
  try {
    if (fs.existsSync(configPath)) {
      const data = JSON.parse(fs.readFileSync(configPath, 'utf8'));
      appSettings = { ...appSettings, ...data };
    }
  } catch (e) {
    console.error('Failed to load settings:', e);
  }
}

// Call loadSettings before creating window
loadSettings();

