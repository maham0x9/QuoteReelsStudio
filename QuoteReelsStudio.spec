# PyInstaller spec for QuoteReelsStudio
# Build with: python scripts/build_exe.py  (or: pyinstaller --noconfirm --clean QuoteReelsStudio.spec)
# Produces a one-folder app under dist/QuoteReelsStudio.
# noinspection PyUnresolvedReferences
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

datas = []
datas += collect_data_files("imageio_ffmpeg")  # bundle ffmpeg binary
datas += [("config.json", "."), ("app/assets", "app/assets")]

hiddenimports = []
hiddenimports += collect_submodules("PySide6")

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter"],
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
    name="QuoteReelsStudio",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="QuoteReelsStudio",
)
