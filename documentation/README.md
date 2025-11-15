# Battle Card Game

A 2-player battle card game built with Python, featuring rock-paper-scissors mechanics with a numerical tie-breaker system.

## Features

- **2-Player Gameplay**: Two players compete in rounds of card battles
- **Card Collection**: 39 cards total (13 values × 3 suits: rock, paper, scissors)
- **Deck Building**: Each player builds a deck of 22 cards (random or manual selection)
- **Turn-Based Battles**: Players draw 3 cards, choose 1 to play, discard the other 2
- **Battle System**:
  - Suit comparison: rock beats scissors, scissors beats paper, paper beats rock
  - Number comparison: higher number wins (except 1 beats 13)
- **Game Persistence**: Games are saved to SQLite database

## How to Play

### Starting a New Game

Run the main script:

```bash
python3 main.py
```

The game will guide you through:

1. **Enter Player Names**:
   - Player 1 (default: "alex")
   - Player 2 (default: "katrine")

2. **Build Decks** (for each player):
   - Choose option 1: Random deck (quick start)
   - Choose option 2: Build deck manually (select 22 cards from the collection)

3. **Start Playing**:
   - Answer 'y' when prompted to start playing
   - Each round:
     - Both players draw 3 cards
     - Each player selects 1 card to play
     - The other 2 cards are automatically discarded
     - Cards are compared and winner is announced
   - Continue rounds until a player runs out of cards

### Game Rules

**Battle Resolution:**

1. **Suit Comparison First**: If suits differ, apply rock-paper-scissors rules
   - Rock beats Scissors
   - Scissors beats Paper
   - Paper beats Rock

2. **Number Comparison (if same suit)**: Higher number wins
   - **Special Rule**: 1 beats 13

**Game End:**

- Game ends when either player has less than 3 cards remaining
- The player with cards remaining wins

## Running Tests

The project includes comprehensive unit tests for game functionality. See [TESTING_README.md](TESTING_README.md) for detailed testing documentation.

### Prerequisites

1. **Python Virtual Environment**: Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Docker (for database-dependent tests)**:
   - Ensure Docker is running
   - Start the PostgreSQL database: `docker-compose up -d postgresql`
   - Database will be available at `localhost:5432`

### Run All Tests

Use the master test runner to execute all Python unit tests:

```bash
# Activate virtual environment first
source venv/bin/activate

# Run all tests
python3 tests/run_all_tests.py
```

### Test Coverage

The test suite includes:

- **Game Tests** (`test_game.py`): Card collection, deck creation, random deck generation, deck validation, game initialization
- **Hand Tests** (`test_hand.py`): Hand drawing, playing cards, multiple rounds, deck exhaustion
- **Score Tests** (`test_score.py`): Battle scoring, score tracking
- **Profile Tests** (`test_profile.py`): User account creation, profile retrieval, password updates (requires Docker)
- **View Tests**: Card collection display, old matches viewing

**Total: 21 tests** covering all core game functionality.

## Requirements

- Python 3.7+
- PostgreSQL (via Docker) for database functionality
- Dependencies listed in `requirements.txt`:
  - `psycopg2-binary` - PostgreSQL adapter for Python

## Database

The project uses two databases:

1. **PostgreSQL** (via Docker): Stores user accounts, authentication, and card collection data
   - Connection: `postgresql://gameuser:gamepassword@localhost:5432/battlecards`
   - Start with: `docker-compose up -d postgresql`

2. **SQLite** (`game.db`): Stores game state and history
   - File: `game.db` in project root
   - Stores: Game state (turn, active status), player decks, hands, played cards, game history

## Development

### Running the Game

```bash
python3 main.py
```

### Running Tests (Development)

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests (recommended)
python3 tests/run_all_tests.py

# Run individual test modules
python3 -m unittest tests.test_game -v
python3 -m unittest tests.test_hand -v
python3 -m unittest tests.test_score -v
python3 -m unittest tests.test_profile -v
```
