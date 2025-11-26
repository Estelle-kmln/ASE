# Advanced Software Engineering Project

## Project Documentation

"The Battle Cards microservices project uses an Nginx API Gateway on port 8080 for all service access. All services (auth, card, game, leaderboard) are accessed through the gateway at <http://localhost:8080/api/>*. The project includes comprehensive testing with pytest (45+ unit tests), Postman/Newman (50 API endpoint tests), and Locust performance tests. All tests are automated via GitHub Actions with 3 parallel test jobs. Complete documentation is available in the documentation/ folder."

## Quick Start

**To build and start all microservices:**

```bash
cd microservices
./build-and-start.sh
```

The build script automatically:

- Generates a secure `GAME_HISTORY_KEY` if one doesn't exist
- Saves the key to `.env` (gitignored for security)
- Builds and starts all Docker containers

**Note**: The `GAME_HISTORY_KEY` is generated once and persists across sessions in the `.env` file. This key is required for game history encryption and tamper detection.

For more documentation, please refer to the directory "documentation".
