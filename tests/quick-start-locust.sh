#!/bin/bash

# Quick start script for Locust performance tests
# This script checks if services are running and starts Locust

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}Checking if microservices are running...${NC}"

# Check nginx gateway
if ! curl -s http://localhost:8080/api/auth/login -X POST -H "Content-Type: application/json" -d '{}' > /dev/null 2>&1; then
    echo -e "${RED}✗ Nginx gateway on port 8080 is not responding${NC}"
    echo ""
    echo -e "${RED}Services are not running!${NC}"
    echo "Please start the microservices first:"
    echo "  cd ../microservices"
    echo "  docker compose up -d"
    echo ""
    echo "Then wait for services to be healthy (about 60 seconds) and run this script again."
    exit 1
fi

echo -e "${GREEN}✓ Nginx gateway is running on port 8080${NC}"

echo ""
echo -e "${GREEN}✓ Nginx gateway is running on port 8080${NC}"
echo ""
echo "Starting Locust web UI..."
echo "Open your browser to: http://localhost:8089"
echo ""

cd "$(dirname "$0")"
locust -f locustfile.py --host=http://localhost:8080

