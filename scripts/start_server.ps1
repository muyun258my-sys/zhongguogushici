$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    throw "Virtual environment Python was not found at: $pythonExe"
}

$stdoutLog = Join-Path $projectRoot "uvicorn.out.log"
$stderrLog = Join-Path $projectRoot "uvicorn.err.log"
$command = "cd /d `"$projectRoot`" && `"$pythonExe`" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > `"$stdoutLog`" 2> `"$stderrLog`""

$process = Start-Process `
    -FilePath "cmd.exe" `
    -ArgumentList @("/c", "start", "`"poetry-assistant`"", "/min", "cmd.exe", "/k", $command) `
    -PassThru

Write-Output "Started launcher PID $($process.Id)"
Write-Output "URL: http://127.0.0.1:8000"
