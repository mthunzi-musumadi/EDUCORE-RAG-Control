# ==============================================================================
# Educore Enterprise RAG - LibreChat Production Launcher
# Cross-Machine Ready: Windows / Linux / macOS compatible
# ==============================================================================

$ProjectRoot = Split-Path -Parent $PSScriptRoot

# 1. Resolve Python executable (virtualenv or system fallback)
$PythonCandidates = @(
    (Join-Path $ProjectRoot "framework_control\Scripts\python.exe"),
    (Join-Path $ProjectRoot ".venv\Scripts\python.exe"),
    (Join-Path $ProjectRoot "venv\Scripts\python.exe")
)
$PythonExe = $null
foreach ($cand in $PythonCandidates) {
    if (Test-Path $cand) {
        $PythonExe = $cand
        break
    }
}
if (-not $PythonExe) {
    $SysPython = Get-Command python -ErrorAction SilentlyContinue
    $PythonExe = if ($SysPython) { $SysPython.Source } else { "python" }
}

$LibreChatDir = Join-Path $ProjectRoot "prototypes\librechat"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Starting Educore Enterprise RAG - LibreChat UI             " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 2. Check if LibreChat node_modules exists (First-time clone check)
$LibreChatNodeModules = Join-Path $LibreChatDir "node_modules"
if (-not (Test-Path $LibreChatNodeModules)) {
    Write-Host "[SETUP] First run detected: Installing LibreChat dependencies (npm install)..." -ForegroundColor Yellow
    Push-Location $LibreChatDir
    npm install
    Pop-Location
}

# 3. Check if Educore Backend is running on port 8000
$BackendPortCheck = Test-NetConnection -ComputerName 127.0.0.1 -Port 8000 -InformationLevel Quiet
if (-not $BackendPortCheck) {
    Write-Host "[1/4] Starting Educore Pure-HTTP Backend on port 8000..." -ForegroundColor Yellow
    Start-Process -FilePath $PythonExe -ArgumentList "$ProjectRoot\src\backend\educore_enterprise_backend.py" -WorkingDirectory $ProjectRoot -WindowStyle Minimized
    Start-Sleep -Seconds 3
} else {
    Write-Host "[1/4] Educore Pure-HTTP Backend is active on port 8000." -ForegroundColor Green
}

# 4. Check if Standalone MongoDB is running on port 27017
$MongoPortCheck = Test-NetConnection -ComputerName 127.0.0.1 -Port 27017 -InformationLevel Quiet
if (-not $MongoPortCheck) {
    Write-Host "[2/4] Starting Standalone MongoDB on port 27017..." -ForegroundColor Yellow
    Start-Process -FilePath "node" -ArgumentList "$LibreChatDir\run_mongo.js" -WorkingDirectory $LibreChatDir -WindowStyle Minimized
    
    # Wait for MongoDB to bind port 27017 (handles initial download if needed)
    $MongoReady = $false
    for ($i = 0; $i -lt 15; $i++) {
        Start-Sleep -Seconds 1
        if (Test-NetConnection -ComputerName 127.0.0.1 -Port 27017 -InformationLevel Quiet) {
            $MongoReady = $true
            break
        }
    }
    if ($MongoReady) {
        Write-Host "      MongoDB is now listening on port 27017." -ForegroundColor Green
    } else {
        Write-Host "      MongoDB starting in background (first run may download binary)..." -ForegroundColor Yellow
    }
} else {
    Write-Host "[2/4] Standalone MongoDB is already active on port 27017." -ForegroundColor Green
}

# 5. Check and build workspace packages if needed
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

# 6. Start LibreChat Backend on port 3080
Write-Host "[4/4] Starting LibreChat Server on port 3080..." -ForegroundColor Yellow
Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host "Access LibreChat at: http://localhost:3080" -ForegroundColor Cyan
Write-Host "Educore Backend at:  http://127.0.0.1:8000/v1" -ForegroundColor Green
Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray

Set-Location $LibreChatDir
$env:PORT = "3080"
npm run backend
