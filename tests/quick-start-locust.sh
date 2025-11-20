#!/bin/bash

# Quick start script for Locust performance tests
# This script checks if services are running and starts Locust

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}Checking if microservices are running...${NC}"

# Check each service
SERVICES_OK=true
for port in 5001 5002 5003 5004; do
    if ! curl -s http://localhost:$port/health > /dev/null 2>&1; then
        echo -e "${RED}✗ Service on port $port is not responding${NC}"
        SERVICES_OK=false
    else
        echo -e "${GREEN}✓ Service on port $port is running${NC}"
    fi
done

if [ "$SERVICES_OK" = false ]; then
    echo ""
    echo -e "${RED}Some services are not running!${NC}"
    echo "Please start the microservices first:"
    echo "  cd ../microservices"
    echo "  docker-compose up -d"
    echo ""
    echo "Then wait for services to be healthy and run this script again."
    exit 1
fi

echo ""
echo -e "${GREEN}All services are running!${NC}"
echo ""
echo "Starting Locust web UI..."
echo "Open your browser to: http://localhost:8089"
echo ""

cd "$(dirname "$0")"
locust -f locustfile.py

