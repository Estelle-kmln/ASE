#!/bin/bash

# Performance Test Runner Script for Battle Cards Microservices
# This script helps you run Locust performance tests easily

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
USERS=50
SPAWN_RATE=5
RUN_TIME="2m"
MODE="web"
USER_CLASS="CombinedUser"
HOST="http://localhost:5001"

# Function to print usage
print_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -u, --users NUM          Number of concurrent users (default: 50)"
    echo "  -r, --spawn-rate NUM     Users to spawn per second (default: 5)"
    echo "  -t, --time TIME          Test duration (e.g., 2m, 5m, 1h) (default: 2m)"
    echo "  -m, --mode MODE          Test mode: web, headless (default: web)"
    echo "  -c, --class CLASS        User class to test (default: CombinedUser)"
    echo "                            Options: AuthServiceUser, CardServiceUser,"
    echo "                                     GameServiceUser, LeaderboardServiceUser,"
    echo "                                     CombinedUser"
    echo "  -h, --host HOST          Base host URL (default: http://localhost:5001)"
    echo "  --help                   Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Run with defaults (web UI)"
    echo "  $0 -u 100 -r 10 -t 5m -m headless    # Headless test with 100 users"
    echo "  $0 -c AuthServiceUser                 # Test only auth service"
    echo "  $0 -c CardServiceUser -h http://localhost:5002  # Test card service"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--users)
            USERS="$2"
            shift 2
            ;;
        -r|--spawn-rate)
            SPAWN_RATE="$2"
            shift 2
            ;;
        -t|--time)
            RUN_TIME="$2"
            shift 2
            ;;
        -m|--mode)
            MODE="$2"
            shift 2
            ;;
        -c|--class)
            USER_CLASS="$2"
            shift 2
            ;;
        -h|--host)
            HOST="$2"
            shift 2
            ;;
        --help)
            print_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            print_usage
            exit 1
            ;;
    esac
done

# Check if locust is installed
if ! command -v locust &> /dev/null; then
    echo -e "${RED}Error: Locust is not installed.${NC}"
    echo "Install it with: pip install locust"
    exit 1
fi

# Check if services are running
echo -e "${YELLOW}Checking if services are running...${NC}"
if ! curl -s http://localhost:5001/health > /dev/null 2>&1; then
    echo -e "${RED}Warning: Auth service (port 5001) is not responding${NC}"
fi
if ! curl -s http://localhost:5002/health > /dev/null 2>&1; then
    echo -e "${RED}Warning: Card service (port 5002) is not responding${NC}"
fi
if ! curl -s http://localhost:5003/health > /dev/null 2>&1; then
    echo -e "${RED}Warning: Game service (port 5003) is not responding${NC}"
fi
if ! curl -s http://localhost:5004/health > /dev/null 2>&1; then
    echo -e "${RED}Warning: Leaderboard service (port 5004) is not responding${NC}"
fi

# Set host based on user class if not explicitly set
case $USER_CLASS in
    AuthServiceUser)
        HOST="http://localhost:5001"
        ;;
    CardServiceUser)
        HOST="http://localhost:5002"
        ;;
    GameServiceUser)
        HOST="http://localhost:5003"
        ;;
    LeaderboardServiceUser)
        HOST="http://localhost:5004"
        ;;
esac

# Print test configuration
echo ""
echo -e "${GREEN}=== Performance Test Configuration ===${NC}"
echo "User Class: $USER_CLASS"
echo "Users: $USERS"
echo "Spawn Rate: $SPAWN_RATE users/second"
echo "Duration: $RUN_TIME"
echo "Mode: $MODE"
echo "Host: $HOST"
echo ""

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Build locust command
LOCUST_CMD="locust -f $SCRIPT_DIR/locustfile.py --host=$HOST $USER_CLASS"

if [ "$MODE" = "headless" ]; then
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    REPORT_FILE="$SCRIPT_DIR/report_${USER_CLASS}_${TIMESTAMP}.html"
    CSV_PREFIX="$SCRIPT_DIR/results_${USER_CLASS}_${TIMESTAMP}"
    
    LOCUST_CMD="$LOCUST_CMD --headless --users $USERS --spawn-rate $SPAWN_RATE --run-time $RUN_TIME --html=$REPORT_FILE --csv=$CSV_PREFIX"
    
    echo -e "${GREEN}Starting headless test...${NC}"
    echo "Results will be saved to:"
    echo "  - HTML Report: $REPORT_FILE"
    echo "  - CSV Files: ${CSV_PREFIX}_*.csv"
    echo ""
else
    echo -e "${GREEN}Starting Locust web UI...${NC}"
    echo "Open your browser to: http://localhost:8089"
    echo "Configure users and spawn rate in the web interface"
    echo ""
fi

# Run locust
eval $LOCUST_CMD

if [ "$MODE" = "headless" ]; then
    echo ""
    echo -e "${GREEN}Test completed!${NC}"
    echo "Check the report: $REPORT_FILE"
fi

