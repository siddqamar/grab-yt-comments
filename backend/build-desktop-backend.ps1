$ErrorActionPreference = "Stop"

$backendDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $backendDir

uv run --with pyinstaller pyinstaller desktop-api.spec --noconfirm --clean
