param(
  [string]$Python = ".\.venv\\Scripts\\python.exe",
  [string]$DistDir = "dist",
  [string]$BuildName = "SCMC",
  [switch]$Sign
)

$ErrorActionPreference = "Stop"

function Test-SigningConfiguration {
  $thumb = $env:SCMC_SIGN_THUMBPRINT
  $pfx = $env:SCMC_SIGN_PFX_PATH
  
  if (!$thumb -and !$pfx) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "ERROR: Signing certificate not configured!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "MANDATORY: Code signing is required for Defender/SmartScreen reputation." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Configure ONE of the following environment variables:" -ForegroundColor Yellow
    Write-Host "  - SCMC_SIGN_THUMBPRINT = Certificate thumbprint from Windows Certificate Store" -ForegroundColor Cyan
    Write-Host "  - SCMC_SIGN_PFX_PATH = Full path to .pfx code signing certificate file" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Optional:" -ForegroundColor Yellow
    Write-Host "  - SCMC_SIGN_PFX_PASSWORD = Password for .pfx file (if required)" -ForegroundColor Cyan
    Write-Host "  - SCMC_SIGN_TIMESTAMP_URL = Timestamp server URL (default: DigiCert)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Example (PowerShell):" -ForegroundColor Yellow
    Write-Host '  $env:SCMC_SIGN_THUMBPRINT = "YOUR_CERT_THUMBPRINT_HERE"' -ForegroundColor Green
    Write-Host '  $env:SCMC_SIGN_PFX_PATH = "C:\path\to\your\certificate.pfx"' -ForegroundColor Green
    Write-Host ""
    throw "Build aborted: Signing certificate required"
  }
  
  if ($pfx -and !(Test-Path $pfx)) {
    throw "PFX file not found: $pfx"
  }
  
  $signtool = Get-SignToolPath
  if (!$signtool) {
    throw "signtool.exe not found. Install Windows SDK (SignTool) or add signtool.exe to PATH."
  }
  
  Write-Host "==> Signing configuration validated" -ForegroundColor Green
  if ($thumb) {
    Write-Host "    Using certificate thumbprint: $thumb" -ForegroundColor Gray
  }
  else {
    Write-Host "    Using PFX file: $pfx" -ForegroundColor Gray
  }
  Write-Host "    SignTool: $signtool" -ForegroundColor Gray
}

function Get-SignToolPath {
  $cmd = Get-Command "signtool.exe" -ErrorAction SilentlyContinue
  if ($cmd) {
    return $cmd.Source
  }

  $kitsRoot = "C:\Program Files (x86)\Windows Kits\10\bin"
  if (!(Test-Path $kitsRoot)) {
    return $null
  }

  # Prefer the newest Windows SDK version folder (filter out architecture folders like x86, x64, arm64)
  $sdkVer = Get-ChildItem -Path $kitsRoot -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match '^\d+\.\d+' } |
    Sort-Object -Property Name -Descending |
    Select-Object -First 1
  if (!$sdkVer) {
    return $null
  }

  $candidate = Join-Path $sdkVer.FullName "x64\signtool.exe"
  if (Test-Path $candidate) {
    return $candidate
  }
  $candidate = Join-Path $sdkVer.FullName "x86\signtool.exe"
  if (Test-Path $candidate) {
    return $candidate
  }

  return $null
}

function Invoke-CodeSign {
  param(
    [Parameter(Mandatory = $true)][string]$FilePath,
    [Parameter(Mandatory = $true)][string]$Description,
    [Parameter(Mandatory = $true)][string]$Url
  )

  $thumb = $env:SCMC_SIGN_THUMBPRINT
  $pfx = $env:SCMC_SIGN_PFX_PATH
  $pfxPass = $env:SCMC_SIGN_PFX_PASSWORD
  $ts = $env:SCMC_SIGN_TIMESTAMP_URL

  if (!$ts) {
    # RFC3161 timestamp (works for Authenticode signatures via signtool /tr)
    $ts = "http://timestamp.digicert.com"
  }

  if (!$thumb -and !$pfx) {
    throw "MANDATORY: Signing certificate not configured. Set SCMC_SIGN_THUMBPRINT or SCMC_SIGN_PFX_PATH environment variable. Signing is required and cannot be skipped."
  }

  $signtool = Get-SignToolPath
  if (!$signtool) {
    throw "signtool.exe not found. Install the Windows SDK (SignTool) or add signtool.exe to PATH."
  }

  $signArgs = @("sign", "/fd", "SHA256", "/tr", $ts, "/td", "SHA256", "/d", $Description, "/du", $Url)
  if ($thumb) {
    $signArgs += @("/sha1", $thumb)
  }
  else {
    $signArgs += @("/f", $pfx)
    if ($pfxPass) {
      $signArgs += @("/p", $pfxPass)
    }
  }
  $signArgs += @($FilePath)

  Write-Host "==> Signing: $FilePath"
  & $signtool @signArgs
  if ($LASTEXITCODE -ne 0) {
    throw "signtool sign failed ($LASTEXITCODE) for $FilePath"
  }

  # Verify signature exists (don't require trusted cert - self-signed is OK for now)
  & $signtool "verify" "/pa" $FilePath
  if ($LASTEXITCODE -ne 0) {
    Write-Warning "Signature verification returned code $LASTEXITCODE (this is normal for self-signed certificates)"
    Write-Host "File is signed, but certificate is not from a trusted CA. For Defender/SmartScreen reputation, use a certificate from a trusted CA."
  } else {
    Write-Host "==> Signature verified successfully" -ForegroundColor Green
  }
}

# Validate signing configuration BEFORE building
Test-SigningConfiguration

Write-Host "==> Preparing virtual environment"
if (!(Test-Path ".\.venv\\Scripts\\python.exe")) {
  python -m venv .venv
}

& $Python -m pip install --upgrade pip
& $Python -m pip install --upgrade pyinstaller
& $Python -m pip install --upgrade -r requirements.txt

Write-Host "==> Building $BuildName.exe with PyInstaller"
$Entry = "src\\meritscalc\\main.py"

# Pull version from src/meritscalc/version.py without requiring install
$AppVersion = (& $Python -c "import sys; sys.path.insert(0, 'src'); from meritscalc.version import __version__; print(__version__)").Trim()
$verParts = $AppVersion.Split(".")
$major = [int]($verParts[0])
$minor = [int]($verParts[1])
$patch = [int]($verParts[2])

$CompanyName = if ($env:SCMC_COMPANY_NAME) { $env:SCMC_COMPANY_NAME } else { "PINKgeekPDX" }
$ProductName = if ($env:SCMC_PRODUCT_NAME) { $env:SCMC_PRODUCT_NAME } else { "SCMC" }
$FileDescription = if ($env:SCMC_FILE_DESCRIPTION) { $env:SCMC_FILE_DESCRIPTION } else { "Star Citizen Merit Calculator" }
$ProductUrl = if ($env:SCMC_PRODUCT_URL) { $env:SCMC_PRODUCT_URL } else { "http://www.scmc.space" }
$RepoUrl = if ($env:SCMC_REPO_URL) { $env:SCMC_REPO_URL } else { "https://github.com/PINKgeekPDX/SCMeritsCalc" }
$Copyright = if ($env:SCMC_COPYRIGHT) { $env:SCMC_COPYRIGHT } else { "Copyright (c) $CompanyName" }

# Generate a PyInstaller version resource file (Windows file properties)
$verFile = Join-Path $env:TEMP "$BuildName-version-info.txt"
$verText = @"
# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=($major, $minor, $patch, 0),
    prodvers=($major, $minor, $patch, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          '040904B0',
          [
            StringStruct('CompanyName', '$CompanyName'),
            StringStruct('FileDescription', '$FileDescription'),
            StringStruct('FileVersion', '$AppVersion'),
            StringStruct('InternalName', '$BuildName'),
            StringStruct('LegalCopyright', '$Copyright'),
            StringStruct('OriginalFilename', '$BuildName.exe'),
            StringStruct('Comments', 'Website: $ProductUrl | GitHub: $RepoUrl'),
            StringStruct('ProductName', '$ProductName'),
            StringStruct('ProductVersion', '$AppVersion')
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"@
Set-Content -Path $verFile -Value $verText -Encoding UTF8

& $Python -m PyInstaller `
  --noconfirm `
  --clean `
  --name $BuildName `
  --distpath $DistDir `
  --onefile `
  --windowed `
  --noupx `
  --icon assets\app-logo.ico `
  --version-file $verFile `
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

$outExe = Join-Path $DistDir "$BuildName.exe"
Write-Host "==> Build complete. Output: $outExe"

# Sign the EXE if configured
Invoke-CodeSign -FilePath $outExe -Description $FileDescription -Url $ProductUrl
