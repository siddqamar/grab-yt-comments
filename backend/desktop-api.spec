from pathlib import Path


project_dir = Path.cwd()


a = Analysis(
    ["desktop_entry.py"],
    pathex=[str(project_dir)],
    binaries=[],
    datas=[],
    hiddenimports=[
        "api",
        "classifier",
        "scraper",
        "uvicorn",
        "uvicorn.config",
        "uvicorn.lifespan.on",
        "uvicorn.logging",
        "uvicorn.loops.auto",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets.auto",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["gradio", "pytest", "tests"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="grab-yt-comments-api",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)
