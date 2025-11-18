# Battle Cards Microservices Test Runner
# This script runs the complete test suite for all microservices

param(
    [switch]$Wait = $false,
    [int]$Timeout = 120
)

Write-Host "Battle Cards Microservices Test Runner" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# Check if Docker is running
Write-Host "Checking Docker status..." -ForegroundColor Yellow
try {
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Docker is not running. Please start Docker Desktop." -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "Error: Docker command not found. Please install Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check if services are running
Write-Host "Checking if microservices are running..." -ForegroundColor Yellow
$containers = docker ps --format "table {{.Names}}" | Select-String -Pattern "(auth-service|card-service|game-service|leaderboard-service|nginx)"

if ($containers.Count -lt 5) {
    Write-Host "Warning: Not all microservices are running. Starting services..." -ForegroundColor Yellow
    
    # Navigate to project directory
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
    $projectDir = Split-Path -Parent $scriptDir
    Set-Location $projectDir
    
    # Start services
    Write-Host "Starting microservices with Docker Compose..." -ForegroundColor Yellow
    docker-compose up -d
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to start microservices" -ForegroundColor Red
        exit 1
    }
    
    # Wait for services to be ready
    if ($Wait) {
        Write-Host "Waiting $Timeout seconds for services to be ready..." -ForegroundColor Yellow
        Start-Sleep -Seconds $Timeout
    }
} else {
    Write-Host "✓ All microservices are running" -ForegroundColor Green
}

# Install Python dependencies for testing
Write-Host "Installing test dependencies..." -ForegroundColor Yellow
pip install requests urllib3 --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "Warning: Failed to install test dependencies. Tests may fail." -ForegroundColor Yellow
}

# Run the test suite
Write-Host "Running microservices test suite..." -ForegroundColor Yellow
Write-Host ""

$testScript = Join-Path $PSScriptRoot "test_microservices.py"
python $testScript

$testExitCode = $LASTEXITCODE

Write-Host ""
if ($testExitCode -eq 0) {
    Write-Host "✓ All tests completed successfully!" -ForegroundColor Green
} else {
    Write-Host "✗ Some tests failed. Check the output above for details." -ForegroundColor Red
}

Write-Host ""
Write-Host "Additional testing options:" -ForegroundColor Cyan
Write-Host "- API Gateway: https://localhost:8443" -ForegroundColor White
Write-Host "- Direct service access:" -ForegroundColor White
Write-Host "  - Auth Service: http://localhost:5001" -ForegroundColor Gray
Write-Host "  - Card Service: http://localhost:5002" -ForegroundColor Gray
Write-Host "  - Game Service: http://localhost:5003" -ForegroundColor Gray
Write-Host "  - Leaderboard Service: http://localhost:5004" -ForegroundColor Gray
Write-Host "  - PostgreSQL: localhost:5432" -ForegroundColor Gray

exit $testExitCode