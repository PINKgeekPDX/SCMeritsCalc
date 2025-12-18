param(
  [string]$Python = ".\\.venv\\Scripts\\python.exe",
  [string]$ISCC = "C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe",
  [string]$IssFile = "installer\SCMC.iss",
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
    $ts = "http://timestamp.digicert.com"
  }

  if (!$thumb -and !$pfx) {
    throw "MANDATORY: Signing certificate not configured. Set SCMC_SIGN_THUMBPRINT or SCMC_SIGN_PFX_PATH environment variable. Signing is required and cannot be skipped."
  }

  $signtool = Get-SignToolPath
  if (!$signtool) {
    throw "signtool.exe not found. Install the Windows SDK (SignTool) or add signtool.exe to PATH."
  }

  $signArgs = @(
    "sign",
    "/fd",
    "SHA256",
    "/tr",
    $ts,
    "/td",
    "SHA256",
    "/d",
    $Description,
    "/du",
    $Url
  )
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

function Get-AppVersion {
  # Prefer reading via Python so dev builds match runtime version.
  if ($Python -and (Test-Path $Python)) {
    try {
      $v = (& $Python -c "import sys; sys.path.insert(0, 'src'); from meritscalc.version import __version__; print(__version__)").Trim()
      if ($v) {
        return $v
      }
    }
    catch {
      # fall through
    }
  }

  $verFile = "src\\meritscalc\\version.py"
  if (!(Test-Path $verFile)) {
    throw "Unable to determine version; missing $verFile"
  }
  $content = Get-Content -Path $verFile -Raw
  $m = [regex]::Match($content, '__version__\s*=\s*\"([^\"]+)\"')
  if ($m.Success) {
    return $m.Groups[1].Value
  }
  throw "Unable to determine version from $verFile"
}

# Validate signing configuration BEFORE building
Test-SigningConfiguration

Write-Host "==> Building Windows installer"
if (!(Test-Path $ISCC)) {
  Write-Warning "Inno Setup compiler not found at '$ISCC'. Install Inno Setup 6 and rerun."
  Write-Host "Download: https://jrsoftware.org/isdl.php"
  exit 1
}

$AppVersion = Get-AppVersion
# Note: Static strings (AppName, AppNameLong, URLs) are defined in SCMC.iss.
# We only pass dynamic values here to avoid quoting issues with spaces in ISCC args.
$AppExeName = "$BuildName.exe"
$OutputBaseFilename = "SCMC_Installer"

$appExePath = Join-Path $DistDir $AppExeName
if (!(Test-Path $appExePath)) {
  throw "Missing '$appExePath'. Build the app first (scripts\\build_exe.ps1)."
}

# Pass only dynamic build metadata
$isccArgs = @(
  "/DAppVersion=$AppVersion",
  "/DAppExeName=$AppExeName",
  "/DOutputBaseFilename=$OutputBaseFilename",
  $IssFile
)

Write-Host "Running ISCC with args: $isccArgs"
& $ISCC @isccArgs
if ($LASTEXITCODE -ne 0) {
  throw "ISCC failed ($LASTEXITCODE)"
}

$installerPath = Join-Path $DistDir ($OutputBaseFilename + ".exe")
if (!(Test-Path $installerPath)) {
  # Fallback: pick newest exe in dist matching *Installer*.exe
  $fallback = Get-ChildItem -Path $DistDir -Filter "*Installer*.exe" -ErrorAction SilentlyContinue | Sort-Object -Property LastWriteTime -Descending | Select-Object -First 1
  if ($fallback) {
    $installerPath = $fallback.FullName
  }
}

Write-Host "==> Installer build complete: $installerPath"

# Sign the installer if configured
# We assume the .iss has the correct long name and URL defined
$AppNameLong = "SCMC (Star Citizen Merit Calculator)"
$AppUrl = "http://www.scmc.space"
Invoke-CodeSign -FilePath $installerPath -Description "$AppNameLong Installer" -Url $AppUrl
