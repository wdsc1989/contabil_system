"""
Script para criar executável do Sistema Contábil
Usa PyInstaller para empacotar tudo em um único .exe
"""

# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('pages', 'pages'),
        ('models', 'models'),
        ('services', 'services'),
        ('config', 'config'),
        ('utils', 'utils'),
        ('tests', 'tests'),
    ],
    hiddenimports=[
        'streamlit',
        'streamlit.runtime.scriptrunner.magic_funcs',
        'pandas',
        'plotly',
        'sqlalchemy',
        'bcrypt',
        'pdfplumber',
        'ofxparse',
        'reportlab',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='SistemaContabil',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)


