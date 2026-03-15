param(
    [string]$dataDir = "..\ai-model\data",
    [int]$epochs = 5,
    [string]$savePath = "..\backend\models\waste_classifier.pth"
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonExe = Join-Path $root '..\backend\venv\Scripts\python.exe'
$script = Join-Path $root '..\ai-model\waste_classifier.py'

Write-Host "Running training: dataDir=$dataDir epochs=$epochs savePath=$savePath"
Push-Location (Join-Path $root '..')
& $pythonExe $script train --data-dir $dataDir --epochs $epochs --model-save-path $savePath
Pop-Location