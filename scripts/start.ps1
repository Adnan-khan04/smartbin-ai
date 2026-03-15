# Start both backend and frontend (Windows PowerShell)
# - Opens two new PowerShell windows so you can see logs
# - Assumes backend venv exists at backend\venv and npm is available in PATH

param()

$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
$backendDir = Join-Path $root '..\backend' | Resolve-Path
$frontendDir = Join-Path $root '..\frontend' | Resolve-Path
$pythonExe = Join-Path $backendDir 'venv\Scripts\python.exe'

Write-Host "Starting backend -> $backendDir"
Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$backendDir'; & '$pythonExe' main.py`"" -WindowStyle Normal

Start-Sleep -Seconds 1
Write-Host "Starting frontend -> $frontendDir"
Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$frontendDir'; npm run dev`"" -WindowStyle Normal

Write-Host "Started backend and frontend (check the new windows for logs)."