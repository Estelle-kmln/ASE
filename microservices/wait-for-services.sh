#!/bin/bash

# Wait for services to be healthy
# This script waits for all microservices to be ready before proceeding

set -e

MAX_ATTEMPTS=60
ATTEMPT=0
SLEEP_TIME=2

echo "Waiting for services to be ready..."

# Wait for PostgreSQL to be healthy
echo "Waiting for PostgreSQL..."
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if docker compose ps postgresql | grep -q "healthy"; then
        echo "✓ PostgreSQL is healthy"
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    sleep $SLEEP_TIME
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "✗ PostgreSQL failed to become healthy"
    docker compose ps
    docker compose logs postgresql
    exit 1
fi

# Wait for Auth Service
echo "Waiting for Auth Service..."
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if docker compose ps auth-service | grep -q "healthy"; then
        echo "✓ Auth Service is healthy"
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    sleep $SLEEP_TIME
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "✗ Auth Service failed to become healthy"
    docker compose logs auth-service
    exit 1
fi

# Wait for Card Service
echo "Waiting for Card Service..."
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if docker compose ps card-service | grep -q "healthy"; then
        echo "✓ Card Service is healthy"
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    sleep $SLEEP_TIME
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "✗ Card Service failed to become healthy"
    docker compose logs card-service
    exit 1
fi

# Wait for Game Service
echo "Waiting for Game Service..."
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if docker compose ps game-service | grep -q "healthy"; then
        echo "✓ Game Service is healthy"
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    sleep $SLEEP_TIME
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "✗ Game Service failed to become healthy"
    docker compose logs game-service
    exit 1
fi

# Wait for Leaderboard Service
echo "Waiting for Leaderboard Service..."
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if docker compose ps leaderboard-service | grep -q "healthy"; then
        echo "✓ Leaderboard Service is healthy"
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    sleep $SLEEP_TIME
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "✗ Leaderboard Service failed to become healthy"
    docker compose logs leaderboard-service
    exit 1
fi

# Wait for Nginx/API Gateway to be accessible (check if it's running)
echo "Waiting for Nginx API Gateway..."
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if docker compose ps api-gateway | grep -q "Up"; then
        echo "✓ Nginx API Gateway container is running"
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    sleep $SLEEP_TIME
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "✗ Nginx API Gateway failed to start"
    docker compose logs api-gateway
    exit 1
fi

# Final verification - test auth endpoint through nginx
echo "Verifying API endpoints through Nginx..."
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -f -k -s https://localhost:8443/api/auth/health > /dev/null 2>&1; then
        echo "✓ Auth API endpoint is accessible through Nginx"
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    sleep $SLEEP_TIME
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "✗ Auth API endpoint failed to become accessible"
    echo "Nginx logs:"
    docker compose logs api-gateway | tail -20
    echo "Auth service logs:"
    docker compose logs auth-service | tail -20
    exit 1
fi

echo ""
echo "✓ All services are ready!"
echo ""
