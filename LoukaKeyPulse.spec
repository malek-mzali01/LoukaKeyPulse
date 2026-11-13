# Copyright (c) 2026 Malek Mzali (Louka). All rights reserved.

import os

NAME = "LoukaKeyPulse"
ADMIN = True
ONEFILE = True
HAS_ICON = os.path.isfile("icon.ico")

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=[("icon.ico", ".")] if HAS_ICON else [],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        "numpy", "pandas", "matplotlib", "scipy", "PIL",
        "pytest", "unittest", "pydoc", "doctest",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

common = dict(
    name=NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="icon.ico" if HAS_ICON else None,
    version="version_info.txt",
    uac_admin=ADMIN,
)

if ONEFILE:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        **common,
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        **common,
    )

    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=False,
        name=NAME,
    )
