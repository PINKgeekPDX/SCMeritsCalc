param(
  [string]$ISCC = "C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe",
  [string]$IssFile = "installer\\MeritsCalc.iss"
)

Write-Host "==> Building Windows installer"
if (!(Test-Path $ISCC)) {
  Write-Warning "Inno Setup compiler not found at '$ISCC'. Install Inno Setup 6 and rerun."
  Write-Host "Download: https://jrsoftware.org/isdl.php"
  exit 1
}

& $ISCC $IssFile

Write-Host "==> Installer build complete"

