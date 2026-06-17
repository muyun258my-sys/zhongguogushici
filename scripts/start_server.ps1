$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    throw "Virtual environment Python was not found at: $pythonExe"
}

$process = Start-Process `
    -FilePath $pythonExe `
    -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload") `
    -WorkingDirectory $projectRoot `
    -WindowStyle Hidden `
    -PassThru

Set-Content -Path (Join-Path $projectRoot "uvicorn.pid") -Value $process.Id
Write-Output "Started server PID $($process.Id)"
Write-Output "URL: http://127.0.0.1:8000"
