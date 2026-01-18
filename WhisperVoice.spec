# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for WhisperVoice.

Build with: pyinstaller WhisperVoice.spec
"""

import sys
from pathlib import Path

block_cipher = None

# Add src to path for imports
src_path = Path('.') / 'src'

a = Analysis(
    ['whisper_app.py'],
    pathex=[str(src_path)],
    binaries=[],
    datas=[
        # Include the whispervoice package
        ('src/whispervoice', 'whispervoice'),
    ],
    hiddenimports=[
        'whispervoice',
        'whispervoice.app',
        'whispervoice.core',
        'whispervoice.core.audio',
        'whispervoice.core.transcription',
        'whispervoice.context',
        'whispervoice.context.capture',
        'whispervoice.context.monitor',
        'whispervoice.context.types',
        'whispervoice.output',
        'whispervoice.output.assembler',
        'whispervoice.ui',
        'whispervoice.ui.indicator',
        'whispervoice.ui.tray',
        # Dependencies
        'whisper',
        'tiktoken',
        'tiktoken_ext',
        'tiktoken_ext.openai_public',
        'sounddevice',
        'numpy',
        'pyperclip',
        'keyboard',
        'pystray',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'win32gui',
        'win32process',
        'win32clipboard',
        'win32con',
        'win32api',
        'psutil',
        'comtypes',
        'comtypes.client',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'pandas',
        'IPython',
        'jupyter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WhisperVoice',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one
)
