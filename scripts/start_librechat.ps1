# ==============================================================================
# Educore Enterprise RAG - LibreChat Production Launcher
# ==============================================================================

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$PythonExe = Join-Path $ProjectRoot "framework_control\Scripts\python.exe"
$LibreChatDir = Join-Path $ProjectRoot "prototypes\librechat"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Starting Educore Enterprise RAG - LibreChat UI             " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Check if Educore Backend is running on port 8000
$BackendPortCheck = Test-NetConnection -ComputerName 127.0.0.1 -Port 8000 -InformationLevel Quiet
if (-not $BackendPortCheck) {
    Write-Host "[1/4] Starting Educore Pure-HTTP Backend on port 8000..." -ForegroundColor Yellow
    Start-Process -FilePath $PythonExe -ArgumentList "$ProjectRoot\src\backend\educore_enterprise_backend.py" -WorkingDirectory $ProjectRoot -WindowStyle Minimized
    Start-Sleep -Seconds 3
} else {
    Write-Host "[1/4] Educore Pure-HTTP Backend is already active on port 8000." -ForegroundColor Green
}

# 2. Check if Standalone MongoDB is running on port 27017
$MongoPortCheck = Test-NetConnection -ComputerName 127.0.0.1 -Port 27017 -InformationLevel Quiet
if (-not $MongoPortCheck) {
    Write-Host "[2/4] Starting Standalone MongoDB on port 27017..." -ForegroundColor Yellow
    Start-Process -FilePath "node" -ArgumentList "$LibreChatDir\run_mongo.js" -WorkingDirectory $LibreChatDir -WindowStyle Minimized
    Start-Sleep -Seconds 3
} else {
    Write-Host "[2/4] Standalone MongoDB is already active on port 27017." -ForegroundColor Green
}

# 3. Check and build workspace packages if needed
$DataProviderDist = Join-Path $LibreChatDir "packages\data-provider\dist"
$DataSchemasDist = Join-Path $LibreChatDir "packages\data-schemas\dist"
if ((-not (Test-Path $DataProviderDist)) -or (-not (Test-Path $DataSchemasDist))) {
    Write-Host "[3/4] Building required LibreChat workspace packages..." -ForegroundColor Yellow
    Push-Location $LibreChatDir
    npm run build:packages
    Pop-Location
} else {
    Write-Host "[3/4] LibreChat workspace packages verified." -ForegroundColor Green
}

# 4. Start LibreChat Backend on port 3080
Write-Host "[4/4] Starting LibreChat Server on port 3080..." -ForegroundColor Yellow
Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host "Access LibreChat at: http://localhost:3080" -ForegroundColor Cyan
Write-Host "Educore Backend at:  http://127.0.0.1:8000/v1" -ForegroundColor Green
Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray

Set-Location $LibreChatDir
$env:PORT = "3080"
npm run backend
