# raycast.spec
# PyInstaller build spec for RayCast launcher
#
# Run with:  pyinstaller raycast.spec
# Output:    dist\RayCast\RayCast.exe

import sys
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # include the ui package
        ('ui', 'ui'),
    ],
    hiddenimports=[
        # pywin32 modules PyInstaller sometimes misses
        'win32api',
        'win32con',
        'win32gui',
        'win32ui',
        'win32process',
        'win32com',
        'win32com.client',
        'win32com.shell',
        'win32com.shell.shell',
        'pywintypes',
        # psutil
        'psutil',
        # pillow
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        # tkinter
        'tkinter',
        'tkinter.ttk',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # trim unused stdlib bloat
        'unittest', 'email', 'html', 'http', 'xml',
        'xmlrpc', 'pydoc', 'doctest', 'difflib',
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
    [],
    exclude_binaries=True,
    name='PyCast',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                  # compress binaries (needs upx.exe in PATH)
    console=False,             # no black CMD window on launch
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='pycast.ico',  # uncomment and add an .ico file if you have one
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PyCast',
)
