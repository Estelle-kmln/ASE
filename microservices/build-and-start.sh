#!/bin/bash

# Build and Start Script for Battle Cards Microservices
# Automatically generates GAME_HISTORY_KEY if not present

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"

# Function to generate a secure GAME_HISTORY_KEY (32-byte urlsafe base64)
generate_history_key() {
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
    
    echo "Error: Could not generate GAME_HISTORY_KEY. Please install python3 or openssl." >&2
    exit 1
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
        echo "GAME_HISTORY_KEY=${GENERATED_KEY}" >> "$ENV_FILE"
        export GAME_HISTORY_KEY="$GENERATED_KEY"
        echo "✓ Generated and saved GAME_HISTORY_KEY to .env file"
    fi
else
    # Check if GAME_HISTORY_KEY is already in environment
    if [ -z "$GAME_HISTORY_KEY" ]; then
        echo "Generating new GAME_HISTORY_KEY..."
        GENERATED_KEY=$(generate_history_key)
        echo "GAME_HISTORY_KEY=${GENERATED_KEY}" > "$ENV_FILE"
        export GAME_HISTORY_KEY="$GENERATED_KEY"
        echo "✓ Generated and saved GAME_HISTORY_KEY to .env file"
    else
        echo "✓ Using GAME_HISTORY_KEY from environment"
        # Save it to .env for persistence
        echo "GAME_HISTORY_KEY=${GAME_HISTORY_KEY}" > "$ENV_FILE"
    fi
fi

# Load all variables from .env file for docker-compose
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
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

