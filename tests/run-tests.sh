#!/bin/bash

# Battle Cards Microservices Test Runner
# This script runs the complete test suite for all microservices

set -e

WAIT_TIME=120

echo "Battle Cards Microservices Test Runner"
echo "======================================"

# Check if Docker is running
echo "Checking Docker status..."
if ! docker info >/dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker."
    exit 1
fi
echo "✓ Docker is running"

# Check if services are running
echo "Checking if microservices are running..."
RUNNING_SERVICES=$(docker ps --format "table {{.Names}}" | grep -E "(auth-service|card-service|game-service|leaderboard-service|nginx)" | wc -l)

if [ "$RUNNING_SERVICES" -lt 5 ]; then
    echo "Warning: Not all microservices are running. Starting services..."
    
    # Navigate to project directory
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
    PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
    cd "$PROJECT_DIR"
    
    # Start services
    echo "Starting microservices with Docker Compose..."
    docker-compose up -d
    
    # Wait for services to be ready
    echo "Waiting $WAIT_TIME seconds for services to be ready..."
    sleep $WAIT_TIME
else
    echo "✓ All microservices are running"
fi

# Install Python dependencies for testing
echo "Installing test dependencies..."
pip3 install requests urllib3 --quiet || {
    echo "Warning: Failed to install test dependencies. Tests may fail."
}

# Run the test suite
echo "Running microservices test suite..."
echo ""

python3 "$(dirname "$0")/test_microservices.py"
TEST_EXIT_CODE=$?

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✓ All tests completed successfully!"
else
    echo "✗ Some tests failed. Check the output above for details."
fi

echo ""
echo "Additional testing options:"
echo "- API Gateway: https://localhost:8443"
echo "- Direct service access:"
echo "  - Auth Service: http://localhost:5001"
echo "  - Card Service: http://localhost:5002"
echo "  - Game Service: http://localhost:5003"
echo "  - Leaderboard Service: http://localhost:5004"
echo "  - PostgreSQL: localhost:5432"

exit $TEST_EXIT_CODE