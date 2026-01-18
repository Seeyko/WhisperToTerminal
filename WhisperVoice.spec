# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for WhisperVoice
# Build with: pyinstaller WhisperVoice.spec

import os

# Find whisper assets dynamically
import whisper
whisper_path = os.path.dirname(whisper.__file__)
whisper_assets = os.path.join(whisper_path, 'assets')

a = Analysis(
    ['whisper_app.py'],
    pathex=[],
    binaries=[],
    datas=[(whisper_assets, 'whisper/assets')],
    hiddenimports=['tiktoken_ext.openai_public', 'tiktoken_ext'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='WhisperVoice',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
