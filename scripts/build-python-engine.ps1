Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = (Resolve-Path (Join-Path $ScriptDir "..")).Path
$EngineDir = Join-Path $RootDir "engine-python"
$TauriBinDir = Join-Path $RootDir "apps\desktop-ui\src-tauri\binaries"
$VenvDir = Join-Path $EngineDir ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$OutputExe = Join-Path $EngineDir "dist\vd-engine.exe"
$TargetExe = Join-Path $TauriBinDir "vd-engine.exe"

function Resolve-PythonCommand {
    if ($env:PYTHON -and (Get-Command $env:PYTHON -ErrorAction SilentlyContinue)) {
        return $env:PYTHON
    }

    $python = Get-Command "python" -ErrorAction SilentlyContinue
    if ($python) {
        return $python.Source
    }

    throw "Python 3.11+ was not found. Install Python or set PYTHON to python.exe."
}

if (-not (Test-Path $EngineDir -PathType Container)) {
    throw "Python engine directory not found: $EngineDir"
}

if (-not (Test-Path $VenvPython -PathType Leaf)) {
    $Python = Resolve-PythonCommand
    Write-Host "Creating Python virtual environment: $VenvDir"
    & $Python -m venv $VenvDir
}

Write-Host "Installing Python engine and build dependencies"
$EngineWithBuildExtra = "$EngineDir[build]"
& $VenvPython -m pip install --disable-pip-version-check -e $EngineWithBuildExtra

Push-Location $EngineDir
try {
    Write-Host "Building vd-engine.exe"
    & $VenvPython -m PyInstaller `
        --noconfirm `
        --clean `
        --onefile `
        --console `
        --specpath "build" `
        --name "vd-engine" `
        --paths "src" `
        --collect-all "yt_dlp" `
        "src\video_download_engine\cli.py"
}
finally {
    Pop-Location
}

if (-not (Test-Path $OutputExe -PathType Leaf)) {
    throw "PyInstaller finished but output was not found: $OutputExe"
}

New-Item -ItemType Directory -Force -Path $TauriBinDir | Out-Null
Remove-Item -LiteralPath (Join-Path $TauriBinDir "vd-engine.exe") -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath (Join-Path $TauriBinDir "vd-engine") -Force -ErrorAction SilentlyContinue
Copy-Item -Force $OutputExe $TargetExe

if (-not (Test-Path $TargetExe -PathType Leaf)) {
    throw "Failed to copy sidecar: $TargetExe"
}

Write-Host "Python engine sidecar generated: $TargetExe"
