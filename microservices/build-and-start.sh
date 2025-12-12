#!/bin/bash

# Build and Start Script for Battle Cards Microservices
# Automatically generates GAME_HISTORY_KEY and SSL certificates if not present

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"
SSL_DIR="${SCRIPT_DIR}/nginx/ssl"
SSL_CERT="${SSL_DIR}/battlecards.crt"
SSL_KEY="${SSL_DIR}/battlecards.key"

# Function to generate a secure key (32-byte urlsafe base64)
generate_secure_key() {
    # Try Python first (most reliable, produces urlsafe base64)
    if command -v python3 &> /dev/null; then
        python3 -c "import base64, os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())" 2>/dev/null && return
    fi
    
    # Fallback to openssl (convert standard base64 to urlsafe)
    if command -v openssl &> /dev/null; then
        openssl rand -base64 32 | tr -d '\n' | tr '+/' '-_' && return
    fi
    
    # Last resort: use /dev/urandom directly (convert to urlsafe)
    if [ -c /dev/urandom ]; then
        head -c 32 /dev/urandom | base64 | tr -d '\n' | tr '+/' '-_' && return
    fi
    
    echo "Error: Could not generate secure key. Please install python3 or openssl." >&2
    exit 1
}

# Function to generate a secure GAME_HISTORY_KEY (32-byte urlsafe base64)
generate_history_key() {
    generate_secure_key
}

# Function to ensure key exists in .env file
ensure_key_in_env() {
    local key_name=$1
    local key_value=$2
    
    if [ -f "$ENV_FILE" ]; then
        if ! grep -q "^${key_name}=" "$ENV_FILE"; then
            echo "${key_name}=${key_value}" >> "$ENV_FILE"
            echo "✓ Generated and saved ${key_name} to .env file"
        else
            echo "✓ Found existing ${key_name} in .env file"
        fi
    else
        echo "${key_name}=${key_value}" >> "$ENV_FILE"
        echo "✓ Generated and saved ${key_name} to .env file"
    fi
}

# Check if .env file exists and has GAME_HISTORY_KEY
if [ -f "$ENV_FILE" ]; then
    if grep -q "^GAME_HISTORY_KEY=" "$ENV_FILE"; then
        echo "✓ Found existing GAME_HISTORY_KEY in .env file"
        # Export it for docker-compose
        export $(grep "^GAME_HISTORY_KEY=" "$ENV_FILE" | xargs)
    else
        echo "Generating new GAME_HISTORY_KEY..."
        GENERATED_KEY=$(generate_history_key)
        ensure_key_in_env "GAME_HISTORY_KEY" "$GENERATED_KEY"
        export GAME_HISTORY_KEY="$GENERATED_KEY"
    fi
else
    # Check if GAME_HISTORY_KEY is already in environment
    if [ -z "$GAME_HISTORY_KEY" ]; then
        echo "Generating new GAME_HISTORY_KEY..."
        GENERATED_KEY=$(generate_history_key)
        ensure_key_in_env "GAME_HISTORY_KEY" "$GENERATED_KEY"
        export GAME_HISTORY_KEY="$GENERATED_KEY"
    else
        echo "✓ Using GAME_HISTORY_KEY from environment"
        # Save it to .env for persistence
        ensure_key_in_env "GAME_HISTORY_KEY" "$GAME_HISTORY_KEY"
    fi
fi

# Generate service API keys for zero-trust networking
echo "Generating service API keys for zero-trust authentication..."
SERVICE_KEYS=(
    "AUTH_SERVICE_API_KEY"
    "CARD_SERVICE_API_KEY"
    "GAME_SERVICE_API_KEY"
    "LEADERBOARD_SERVICE_API_KEY"
    "LOGS_SERVICE_API_KEY"
)

for key_name in "${SERVICE_KEYS[@]}"; do
    if [ -f "$ENV_FILE" ] && grep -q "^${key_name}=" "$ENV_FILE"; then
        echo "✓ Found existing ${key_name} in .env file"
        export $(grep "^${key_name}=" "$ENV_FILE" | xargs)
    else
        GENERATED_KEY=$(generate_secure_key)
        ensure_key_in_env "$key_name" "$GENERATED_KEY"
        export ${key_name}="$GENERATED_KEY"
    fi
done

# Load all variables from .env file for docker-compose
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
fi

# Generate SSL certificates if they don't exist
if [ ! -f "$SSL_CERT" ] || [ ! -f "$SSL_KEY" ]; then
    echo "Generating SSL certificates..."
    mkdir -p "$SSL_DIR"
    
    if ! command -v openssl &> /dev/null; then
        echo "Error: openssl not found. Please install openssl to generate SSL certificates." >&2
        exit 1
    fi
    
    openssl req -x509 -newkey rsa:4096 -keyout "$SSL_KEY" \
        -out "$SSL_CERT" -days 365 -nodes \
        -subj "/CN=localhost" 2>/dev/null
    
    echo "✓ Generated SSL certificates at ${SSL_DIR}/"
else
    echo "✓ Found existing SSL certificates at ${SSL_DIR}/"
fi

echo ""
echo "Building and starting microservices..."
echo ""

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Error: docker-compose not found. Please install Docker Compose." >&2
    exit 1
fi

# Build and start services
cd "$SCRIPT_DIR"

# Try docker-compose first, fallback to docker compose (v2)
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
    docker-compose up -d --build
else
    DOCKER_COMPOSE_CMD="docker compose"
    docker compose up -d --build
fi

echo ""
echo "✓ Services are starting. Check status with: ${DOCKER_COMPOSE_CMD} ps"
echo "✓ View logs with: ${DOCKER_COMPOSE_CMD} logs -f"
echo ""
echo "Note: GAME_HISTORY_KEY has been saved to ${ENV_FILE}"
echo "      This file is gitignored to keep your key secure."

