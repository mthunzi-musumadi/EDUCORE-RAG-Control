# ==============================================================================
# Educore Enterprise RAG - LibreChat Prototype Launcher
# ==============================================================================

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$PythonExe = Join-Path $ProjectRoot "framework_control\Scripts\python.exe"
$LibreChatDir = Join-Path $ProjectRoot "prototypes\librechat"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Starting Educore Enterprise RAG  LibreChat Prototype      " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Check if Educore Backend is running on port 8000
$BackendPortCheck = Test-NetConnection -ComputerName 127.0.0.1 -Port 8000 -InformationLevel Quiet
if (-not $BackendPortCheck) {
    Write-Host "[1/3] Starting Educore Pure-HTTP Backend on port 8000..." -ForegroundColor Yellow
    Start-Process -FilePath $PythonExe -ArgumentList "$ProjectRoot\src\backend\educore_enterprise_backend.py" -WorkingDirectory $ProjectRoot -WindowStyle Minimized
    Start-Sleep -Seconds 3
} else {
    Write-Host "[1/3] Educore Pure-HTTP Backend is already active on port 8000." -ForegroundColor Green
}

# 2. Check if Standalone MongoDB is running on port 27017
$MongoPortCheck = Test-NetConnection -ComputerName 127.0.0.1 -Port 27017 -InformationLevel Quiet
if (-not $MongoPortCheck) {
    Write-Host "[2/3] Starting Standalone MongoDB on port 27017..." -ForegroundColor Yellow
    Start-Process -FilePath "node" -ArgumentList "$LibreChatDir\run_mongo.js" -WorkingDirectory $LibreChatDir -WindowStyle Minimized
    Start-Sleep -Seconds 3
} else {
    Write-Host "[2/3] Standalone MongoDB is already active on port 27017." -ForegroundColor Green
}

# 3. Start LibreChat Backend on port 3080
Write-Host "[3/3] Starting LibreChat Server on port 3080..." -ForegroundColor Yellow
Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host "Access LibreChat at: http://localhost:3080" -ForegroundColor Cyan
Write-Host "Access Custom UI at: http://localhost:3000" -ForegroundColor Magenta
Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray

Set-Location $LibreChatDir
$env:PORT = "3080"
npm run backend
