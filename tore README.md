[1mdiff --git a/README.md b/README.md[m
[1mindex c4986a0..be3be93 100644[m
[1m--- a/README.md[m
[1m+++ b/README.md[m
[36m@@ -1 +1,131 @@[m
[31m-# ASE[m
\ No newline at end of file[m
[32m+[m[32m# Battle Card Game[m
[32m+[m
[32m+[m[32mA 2-player battle card game built with Python, featuring rock-paper-scissors mechanics with a numerical tie-breaker system.[m
[32m+[m
[32m+[m[32m## Features[m
[32m+[m
[32m+[m[32m- **2-Player Gameplay**: Two players compete in rounds of card battles[m
[32m+[m[32m- **Card Collection**: 39 cards total (13 values × 3 suits: rock, paper, scissors)[m
[32m+[m[32m- **Deck Building**: Each player builds a deck of 22 cards (random or manual selection)[m
[32m+[m[32m- **Turn-Based Battles**: Players draw 3 cards, choose 1 to play, discard the other 2[m
[32m+[m[32m- **Battle System**:[m
[32m+[m[32m  - Suit comparison: rock beats scissors, scissors beats paper, paper beats rock[m
[32m+[m[32m  - Number comparison: higher number wins (except 1 beats 13)[m
[32m+[m[32m- **Game Persistence**: Games are saved to SQLite database[m
[32m+[m
[32m+[m[32m## How to Play[m
[32m+[m
[32m+[m[32m### Starting a New Game[m
[32m+[m
[32m+[m[32mRun the main script:[m
[32m+[m
[32m+[m[32m```bash[m
[32m+[m[32mpython3 main.py[m
[32m+[m[32m```[m
[32m+[m
[32m+[m[32mThe game will guide you through:[m
[32m+[m
[32m+[m[32m1. **Enter Player Names**:[m
[32m+[m[32m   - Player 1 (default: "alex")[m
[32m+[m[32m   - Player 2 (default: "katrine")[m
[32m+[m
[32m+[m[32m2. **Build Decks** (for each player):[m
[32m+[m[32m   - Choose option 1: Random deck (quick start)[m
[32m+[m[32m   - Choose option 2: Build deck manually (select 22 cards from the collection)[m
[32m+[m
[32m+[m[32m3. **Start Playing**:[m
[32m+[m[32m   - Answer 'y' when prompted to start playing[m
[32m+[m[32m   - Each round:[m
[32m+[m[32m     - Both players draw 3 cards[m
[32m+[m[32m     - Each player selects 1 card to play[m
[32m+[m[32m     - The other 2 cards are automatically discarded[m
[32m+[m[32m     - Cards are compared and winner is announced[m
[32m+[m[32m   - Continue rounds until a player runs out of cards[m
[32m+[m
[32m+[m[32m### Game Rules[m
[32m+[m
[32m+[m[32m**Battle Resolution:**[m
[32m+[m
[32m+[m[32m1. **Suit Comparison First**: If suits differ, apply rock-paper-scissors rules[m
[32m+[m[32m   - Rock beats Scissors[m
[32m+[m[32m   - Scissors beats Paper[m
[32m+[m[32m   - Paper beats Rock[m
[32m+[m
[32m+[m[32m2. **Number Comparison (if same suit)**: Higher number wins[m
[32m+[m[32m   - **Special Rule**: 1 beats 13[m
[32m+[m
[32m+[m[32m**Game End:**[m
[32m+[m
[32m+[m[32m- Game ends when either player has less than 3 cards remaining[m
[32m+[m[32m- The player with cards remaining wins[m
[32m+[m
[32m+[m[32m## Running Tests[m
[32m+[m
[32m+[m[32mThe project includes comprehensive tests for game functionality.[m
[32m+[m
[32m+[m[32m### Run All Tests[m
[32m+[m
[32m+[m[32m```bash[m
[32m+[m[32m# Run game tests[m
[32m+[m[32mpython3 test_game.py[m
[32m+[m
[32m+[m[32m# Run hand functionality tests[m
[32m+[m[32mpython3 test_hand.py[m
[32m+[m
[32m+[m[32m# Run both test suites[m
[32m+[m[32mpython3 test_game.py && python3 test_hand.py[m
[32m+[m[32m```[m
[32m+[m
[32m+[m[32m### Test Coverage[m
[32m+[m
[32m+[m[32m**`test_game.py`** tests:[m
[32m+[m
[32m+[m[32m- Card collection (39 cards, 13 per suit)[m
[32m+[m[32m- Deck creation and shuffling[m
[32m+[m[32m- Random deck generation[m
[32m+[m[32m- Deck validation[m
[32m+[m[32m- Game initialization with 2 players[m
[32m+[m
[32m+[m[32m**`test_hand.py`** tests:[m
[32m+[m
[32m+[m[32m- Drawing 3 cards for a turn[m
[32m+[m[32m- Playing a card and discarding the other 2[m
[32m+[m[32m- Multiple turns[m
[32m+[m[32m- Deck exhaustion handling[m
[32m+[m
[32m+[m[32m## Requirements[m
[32m+[m
[32m+[m[32m- Python 3.7+[m
[32m+[m[32m- No external dependencies (uses only Python standard library)[m
[32m+[m
[32m+[m[32m## Database[m
[32m+[m
[32m+[m[32mGames are automatically saved to `game.db` (SQLite database) in the project root. The database stores:[m
[32m+[m
[32m+[m[32m- Game state (turn, active status)[m
[32m+[m[32m- Both players' decks[m
[32m+[m[32m- Current hands and played cards[m
[32m+[m[32m- Game history[m
[32m+[m
[32m+[m[32m## Development[m
[32m+[m
[32m+[m[32m### Running the Game[m
[32m+[m
[32m+[m[32m```bash[m
[32m+[m[32mpython3 main.py[m
[32m+[m[32m```[m
[32m+[m
[32m+[m[32m### Running Tests[m
[32m+[m
[32m+[m[32m```bash[m
[32m+[m[32m# Individual test files[m
[32m+[m[32mpython3 test_game.py[m
[32m+[m[32mpython3 test_hand.py[m
[32m+[m
[32m+[m[32m# All tests[m
[32m+[m[32mpython3 test_game.py && python3 test_hand.py[m
[32m+[m[32m```[m
[32m+[m[32mRunning test_score[m
[32m+[m[32m```bash[m
[32m+[m[32mpython -m unittest discover -s tests -p "test_*.py" -v[m
[32m+[m[32m```[m
\ No newline at end of file[m
