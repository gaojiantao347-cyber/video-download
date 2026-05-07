param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $TauriArgs = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = (Resolve-Path (Join-Path $ScriptDir "..")).Path
$UiDir = Join-Path $RootDir "apps\desktop-ui"
$BuildEngineScript = Join-Path $ScriptDir "build-python-engine.ps1"

function Resolve-NpmCommand {
    $npmCmd = Get-Command "npm.cmd" -ErrorAction SilentlyContinue
    if ($npmCmd) {
        return $npmCmd.Source
    }

    $npm = Get-Command "npm" -ErrorAction SilentlyContinue
    if ($npm) {
        return $npm.Source
    }

    throw "npm was not found. Install Node.js first."
}

if (-not (Test-Path $UiDir -PathType Container)) {
    throw "Desktop UI directory not found: $UiDir"
}

if (-not (Test-Path $BuildEngineScript -PathType Leaf)) {
    throw "Python engine build script not found: $BuildEngineScript"
}

& $BuildEngineScript

$Npm = Resolve-NpmCommand
Push-Location $UiDir
try {
    if (-not (Test-Path "node_modules" -PathType Container)) {
        Write-Host "Installing desktop UI dependencies"
        & $Npm ci
    }

    Write-Host "Building Tauri desktop bundle"
    if ($TauriArgs.Count -gt 0) {
        & $Npm run tauri:build -- @TauriArgs
    }
    else {
        & $Npm run tauri:build
    }
}
finally {
    Pop-Location
}
