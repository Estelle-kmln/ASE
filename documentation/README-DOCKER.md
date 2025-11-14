# Battle Card Game - Docker Setup

This project includes Docker configurations for running the battle card game with a PostgreSQL database.

## Architecture

- **PostgreSQL Container**: Stores card data and user information
- **Python Game Container**: Runs the CLI-based battle card game
- **Docker Compose**: Orchestrates both containers with proper networking

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Git (to clone the repository)

### Running the Application

1. **Build and start all services:**
   ```bash
   docker-compose up --build
   ```

2. **Run in detached mode (background):**
   ```bash
   docker-compose up -d --build
   ```

3. **Interactive game session:**
   ```bash
   # After starting with docker-compose up -d
   docker-compose exec game-app python main.py
   ```

### Database Access

- **PostgreSQL Connection**: `postgresql://gameuser:gamepassword@localhost:5432/battlecards`
- **Database Name**: `battlecards`
- **Tables**: `users`, `cards`

### Useful Commands

```bash
# View logs
docker-compose logs -f game-app
docker-compose logs -f postgresql

# Stop all services
docker-compose down

# Stop and remove volumes (deletes data)
docker-compose down -v

# Rebuild containers
docker-compose build --no-cache

# Access PostgreSQL shell
docker-compose exec postgresql psql -U gameuser -d battlecards

# Access game container bash
docker-compose exec game-app bash
```

## Card Data

The Postgres container is pre-populated with sample cards including:
- Fire Dragon (Rare Creature)
- Lightning Bolt (Common Spell) 
- Healing Potion (Common Spell)
- Ice Giant (Epic Creature)
- Shadow Assassin (Uncommon Creature)
- Shield Wall (Uncommon Spell)
- Ancient Wizard (Rare Creature)
- Fireball (Common Spell)

## Development

### Local Development Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Start only PostgreSQL
docker-compose up -d postgresql

# Run game locally (connects to containerized PostgreSQL)
export DATABASE_URL="postgresql://gameuser:gamepassword@localhost:5432/battlecards"
python main.py
```

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `POSTGRES_USER`: PostgreSQL username
- `POSTGRES_PASSWORD`: PostgreSQL password
- `POSTGRES_DB`: Initial database name

## Troubleshooting

### Container Issues
- Check container status: `docker-compose ps`
- View container logs: `docker-compose logs [service-name]`
- Restart services: `docker-compose restart`

### Database Connection Issues
- Ensure PostgreSQL container is healthy: `docker-compose ps`
- Check network connectivity: `docker-compose exec game-app ping postgresql`
- Verify PostgreSQL is accepting connections: `docker-compose exec postgresql pg_isready -U gameuser -d battlecards`

### Data Persistence
- PostgreSQL data persists in Docker volume `postgresql_data`
- To reset database: `docker-compose down -v` (removes all data)