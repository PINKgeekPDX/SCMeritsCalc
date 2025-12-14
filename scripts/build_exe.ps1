param(
  [string]$Python = ".\.venv\\Scripts\\python.exe",
  [string]$DistDir = "dist",
  [string]$BuildName = "SCMC"
)

Write-Host "==> Preparing virtual environment"
if (!(Test-Path ".\.venv\\Scripts\\python.exe")) {
  python -m venv .venv
}

& $Python -m pip install --upgrade pip
& $Python -m pip install pyinstaller PyQt6 Pillow pyperclip customtkinter pywin32 requests packaging

Write-Host "==> Building $BuildName.exe with PyInstaller"
$Entry = "src\\meritscalc\\main.py"

& $Python -m PyInstaller `
  --noconfirm `
  --clean `
  --name $BuildName `
  --onefile `
  --windowed `
  --icon assets\app-logo.ico `
  --add-data "assets\app-logo.png;assets" `
  --add-data "assets\app-logo.ico;assets" `
  --paths src `
  --hidden-import PyQt6.QtCore `
  --hidden-import PyQt6.QtGui `
  --hidden-import PyQt6.QtWidgets `
  --hidden-import PIL `
  --hidden-import pyperclip `
  --hidden-import meritscalc.settings `
  --hidden-import meritscalc.logic `
  --hidden-import meritscalc.qt_ui `
  --hidden-import meritscalc.components `
  --hidden-import meritscalc.updater `
  --hidden-import meritscalc.version `
  --hidden-import requests `
  --hidden-import packaging `
  --hidden-import packaging.version `
  $Entry

Write-Host "==> Build complete. Output: $DistDir\\$BuildName.exe"
