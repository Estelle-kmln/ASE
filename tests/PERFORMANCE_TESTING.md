# Performance Testing with Locust

This document describes how to run performance tests for the Battle Cards microservices application using Locust.

## Prerequisites

1. **Python 3.8+** installed
2. **All microservices running** (via Docker Compose or individually)
3. **Locust installed** (see Installation below)

## Installation

### Option 1: Install Locust globally
```bash
pip install locust
```

### Option 2: Install in a virtual environment (recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r locust_requirements.txt
```

## Running the Tests

### Basic Usage

Start Locust with the default configuration:
```bash
cd tests
locust -f locustfile.py
```

Then open your browser to `http://localhost:8089` to access the Locust web UI.

### Running Specific User Classes

You can test individual services by specifying the user class:

**Test Auth Service only:**
```bash
cd tests
locust -f locustfile.py --host=http://localhost:5001 AuthServiceUser
```

**Test Card Service only:**
```bash
cd tests
locust -f locustfile.py --host=http://localhost:5002 CardServiceUser
```

**Test Game Service only:**
```bash
cd tests
locust -f locustfile.py --host=http://localhost:5003 GameServiceUser
```

**Test Leaderboard Service only:**
```bash
cd tests
locust -f locustfile.py --host=http://localhost:5004 LeaderboardServiceUser
```

**Test Combined Workflow (all services):**
```bash
cd tests
locust -f locustfile.py --host=http://localhost:5001 CombinedUser
```

### Headless Mode (No Web UI)

Run tests without the web interface:

```bash
# Run with specific number of users and spawn rate
cd tests
locust -f locustfile.py --headless --users 100 --spawn-rate 10 --run-time 5m --host=http://localhost:5001

# Test all services in headless mode
locust -f locustfile.py --headless --users 50 --spawn-rate 5 --run-time 3m --host=http://localhost:5001 CombinedUser
```

### Command Line Options

- `--users` or `-u`: Total number of concurrent users
- `--spawn-rate` or `-r`: Number of users to spawn per second
- `--run-time` or `-t`: Test duration (e.g., `5m`, `1h`, `30s`)
- `--host`: Base host URL (required if not in locustfile)
- `--headless`: Run without web UI
- `--html`: Generate HTML report
- `--csv`: Generate CSV reports

### Example: Full Performance Test

```bash
cd tests
# Test with 100 users, spawn 10 per second, run for 5 minutes
locust -f locustfile.py \
  --headless \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m \
  --html=report.html \
  --csv=results \
  --host=http://localhost:5001
```

## Test Scenarios

### AuthServiceUser
- Tests authentication endpoints (register, login, profile, validate)
- Simulates user authentication workflows
- Weight: Login (3x), Profile (2x), Validate (1x)

### CardServiceUser
- Tests card retrieval and deck creation
- Simulates browsing card collection
- Weight: Get all cards (5x), Get by type (3x), Random deck (4x)

### GameServiceUser
- Tests game creation and gameplay
- Simulates game sessions
- Weight: Get game state (3x), Draw hand (2x), Play card (2x)

### LeaderboardServiceUser
- Tests leaderboard and statistics endpoints
- Simulates viewing rankings
- Weight: Leaderboard (5x), Recent games (3x), Statistics (2x)

### CombinedUser
- Tests complete user workflows across all services
- Simulates realistic user behavior
- Weight: Complete workflow (10x), View leaderboard (5x), Profile (3x)

## Understanding Results

### Key Metrics

1. **Response Time (ms)**: Time taken for requests to complete
   - Median: Middle value (50th percentile)
   - 95th percentile: 95% of requests completed within this time
   - 99th percentile: 99% of requests completed within this time

2. **Requests per Second (RPS)**: Throughput of your system

3. **Failure Rate**: Percentage of failed requests

### Interpreting Results

- **Response times < 200ms**: Excellent
- **Response times 200-500ms**: Good
- **Response times 500-1000ms**: Acceptable
- **Response times > 1000ms**: Needs optimization

- **Failure rate < 1%**: Good
- **Failure rate 1-5%**: Acceptable under load
- **Failure rate > 5%**: System may be overloaded

## Tips for Performance Testing

1. **Start Small**: Begin with low user counts (10-20) and gradually increase
2. **Monitor Services**: Watch Docker logs and system resources during tests
3. **Test Incrementally**: Test each service individually before combined tests
4. **Database State**: Ensure database has test data for realistic scenarios
5. **Network**: Test on the same network as services for accurate results

## Troubleshooting

### Connection Refused
- Ensure all microservices are running
- Check that services are accessible on expected ports (5001-5004)

### Authentication Errors
- Some test users may need to be pre-created
- Check that JWT_SECRET_KEY is consistent across services

### High Failure Rates
- Reduce number of concurrent users
- Check database connection limits
- Monitor service logs for errors

### Slow Response Times
- Check database query performance
- Monitor database connection pool
- Verify network latency

## Generating Reports

### HTML Report
```bash
cd tests
locust -f locustfile.py --headless --users 50 --spawn-rate 5 --run-time 2m --html=report.html
```

### CSV Reports
```bash
cd tests
locust -f locustfile.py --headless --users 50 --spawn-rate 5 --run-time 2m --csv=results
```

This generates:
- `results_stats.csv`: Request statistics
- `results_failures.csv`: Failed requests
- `results_exceptions.csv`: Exceptions

## Example Test Scenarios

### Light Load Test
```bash
cd tests
locust -f locustfile.py --users 10 --spawn-rate 2 --run-time 2m
```

### Medium Load Test
```bash
cd tests
locust -f locustfile.py --users 50 --spawn-rate 5 --run-time 5m
```

### Heavy Load Test
```bash
cd tests
locust -f locustfile.py --users 200 --spawn-rate 20 --run-time 10m
```

### Stress Test
```bash
cd tests
locust -f locustfile.py --users 500 --spawn-rate 50 --run-time 15m
```

## Resources

- [Locust Documentation](https://docs.locust.io/)
- [Locust Best Practices](https://docs.locust.io/en/stable/writing-a-locustfile.html)
- [Performance Testing Guide](https://docs.locust.io/en/stable/quickstart.html)

