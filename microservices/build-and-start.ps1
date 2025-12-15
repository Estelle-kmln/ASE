# Build and Start Script for Battle Cards Microservices (Windows PowerShell)
# Automatically generates GAME_HISTORY_KEY and SSL certificates if not present

$ErrorActionPreference = "Stop"

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$ENV_FILE = Join-Path $SCRIPT_DIR ".env"
$SSL_DIR = Join-Path $SCRIPT_DIR "nginx\ssl"
$SSL_CERT = Join-Path $SSL_DIR "battlecards.crt"
$SSL_KEY = Join-Path $SSL_DIR "battlecards.key"

# Function to generate a secure key (32-byte base64)
function Generate-SecureKey {
    $bytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $rng.GetBytes($bytes)
    $base64 = [Convert]::ToBase64String($bytes)
    # Convert to URL-safe base64
    $urlSafe = $base64.Replace('+', '-').Replace('/', '_').TrimEnd('=')
    return $urlSafe
}

# Function to ensure key exists in .env file
function Ensure-KeyInEnv {
    param(
        [string]$KeyName,
        [string]$KeyValue
    )
    
    if (Test-Path $ENV_FILE) {
        $content = Get-Content $ENV_FILE -Raw
        if ($content -notmatch "^$KeyName=") {
            Add-Content -Path $ENV_FILE -Value "$KeyName=$KeyValue"
            Write-Host "✓ Generated and saved $KeyName to .env file" -ForegroundColor Green
        } else {
            Write-Host "✓ Found existing $KeyName in .env file" -ForegroundColor Green
        }
    } else {
        Set-Content -Path $ENV_FILE -Value "$KeyName=$KeyValue"
        Write-Host "✓ Generated and saved $KeyName to .env file" -ForegroundColor Green
    }
}

# Check if .env file exists and has GAME_HISTORY_KEY
if (Test-Path $ENV_FILE) {
    $envContent = Get-Content $ENV_FILE -Raw
    if ($envContent -match "^GAME_HISTORY_KEY=(.+)$") {
        Write-Host "✓ Found existing GAME_HISTORY_KEY in .env file" -ForegroundColor Green
        $env:GAME_HISTORY_KEY = $Matches[1]
    } else {
        Write-Host "Generating new GAME_HISTORY_KEY..." -ForegroundColor Yellow
        $generatedKey = Generate-SecureKey
        Ensure-KeyInEnv "GAME_HISTORY_KEY" $generatedKey
        $env:GAME_HISTORY_KEY = $generatedKey
    }
} else {
    if (-not $env:GAME_HISTORY_KEY) {
        Write-Host "Generating new GAME_HISTORY_KEY..." -ForegroundColor Yellow
        $generatedKey = Generate-SecureKey
        Ensure-KeyInEnv "GAME_HISTORY_KEY" $generatedKey
        $env:GAME_HISTORY_KEY = $generatedKey
    } else {
        Write-Host "✓ Using GAME_HISTORY_KEY from environment" -ForegroundColor Green
        Ensure-KeyInEnv "GAME_HISTORY_KEY" $env:GAME_HISTORY_KEY
    }
}

# Generate service API keys for zero-trust networking
Write-Host "Generating service API keys for zero-trust authentication..." -ForegroundColor Cyan

$serviceKeys = @(
    "AUTH_SERVICE_API_KEY",
    "CARD_SERVICE_API_KEY",
    "GAME_SERVICE_API_KEY",
    "LEADERBOARD_SERVICE_API_KEY",
    "LOGS_SERVICE_API_KEY"
)

foreach ($keyName in $serviceKeys) {
    if ((Test-Path $ENV_FILE) -and ((Get-Content $ENV_FILE -Raw) -match "^$keyName=(.+)$")) {
        Write-Host "✓ Found existing $keyName in .env file" -ForegroundColor Green
        Set-Item -Path "env:$keyName" -Value $Matches[1]
    } else {
        $generatedKey = Generate-SecureKey
        Ensure-KeyInEnv $keyName $generatedKey
        Set-Item -Path "env:$keyName" -Value $generatedKey
    }
}

# Load all variables from .env file
if (Test-Path $ENV_FILE) {
    Get-Content $ENV_FILE | ForEach-Object {
        if ($_ -match "^([^#][^=]+)=(.+)$") {
            Set-Item -Path "env:$($Matches[1])" -Value $Matches[2]
        }
    }
}

# Generate SSL certificates if they don't exist
if (-not (Test-Path $SSL_CERT) -or -not (Test-Path $SSL_KEY)) {
    Write-Host "Generating SSL certificates..." -ForegroundColor Yellow
    
    if (-not (Test-Path $SSL_DIR)) {
        New-Item -ItemType Directory -Path $SSL_DIR | Out-Null
    }
    
    # Check if openssl is available
    $opensslPath = Get-Command openssl -ErrorAction SilentlyContinue
    if (-not $opensslPath) {
        Write-Host "Error: openssl not found. Please install OpenSSL." -ForegroundColor Red
        Write-Host "Download from: https://slproweb.com/products/Win32OpenSSL.html" -ForegroundColor Yellow
        Write-Host "Or use: winget install -e --id ShiningLight.OpenSSL" -ForegroundColor Yellow
        exit 1
    }
    
    & openssl req -x509 -newkey rsa:4096 -keyout $SSL_KEY `
        -out $SSL_CERT -days 365 -nodes `
        -subj "/CN=localhost" 2>$null
    
    Write-Host "✓ Generated SSL certificates at $SSL_DIR" -ForegroundColor Green
} else {
    Write-Host "✓ Found existing SSL certificates at $SSL_DIR" -ForegroundColor Green
}

Write-Host ""
Write-Host "Building and starting microservices..." -ForegroundColor Cyan
Write-Host ""

# Check if docker compose is available
$dockerCompose = $null
try {
    docker compose version | Out-Null
    $dockerCompose = "docker compose"
} catch {
    try {
        docker-compose --version | Out-Null
        $dockerCompose = "docker-compose"
    } catch {
        Write-Host "Error: Docker Compose not found. Please install Docker Desktop." -ForegroundColor Red
        exit 1
    }
}

# Change to script directory
Set-Location $SCRIPT_DIR

# Verify docker-compose.yml exists
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "Error: docker-compose.yml not found in $(Get-Location)" -ForegroundColor Red
    exit 1
}

# Build and start services
Write-Host "Running: $dockerCompose up -d --build" -ForegroundColor Cyan
& $dockerCompose.Split() up -d --build

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✓ Services started successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Access the application at:" -ForegroundColor Cyan
    Write-Host "  HTTPS: https://localhost:8443" -ForegroundColor Yellow
    Write-Host "  HTTP:  http://localhost:8080 (redirects to HTTPS)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To view logs: $dockerCompose logs -f" -ForegroundColor Gray
    Write-Host "To stop:      $dockerCompose down" -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "✗ Failed to start services. Check the logs above." -ForegroundColor Red
    exit 1
}
