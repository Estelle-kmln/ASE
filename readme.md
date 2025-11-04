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

The project includes comprehensive tests for game functionality.

### Run All Tests

```bash
# Run game tests
python3 test_game.py

# Run hand functionality tests
python3 test_hand.py

# Run both test suites
python3 test_game.py && python3 test_hand.py
```

### Test Coverage

**`test_game.py`** tests:

- Card collection (39 cards, 13 per suit)
- Deck creation and shuffling
- Random deck generation
- Deck validation
- Game initialization with 2 players

**`test_hand.py`** tests:

- Drawing 3 cards for a turn
- Playing a card and discarding the other 2
- Multiple turns
- Deck exhaustion handling

## Requirements

- Python 3.7+
- No external dependencies (uses only Python standard library)

## Database

Games are automatically saved to `game.db` (SQLite database) in the project root. The database stores:

- Game state (turn, active status)
- Both players' decks
- Current hands and played cards
- Game history

## Development

### Running the Game

```bash
python3 main.py
```

### Running Tests

```bash
# Individual test files
python3 test_game.py
python3 test_hand.py

# All tests
python3 test_game.py && python3 test_hand.py
```
