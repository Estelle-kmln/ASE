"""
Game Service - Game logic and state management microservice
"""

import os
import json
import uuid
import random
from datetime import datetime
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')

# Initialize extensions
jwt = JWTManager(app)
CORS(app)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://gameuser:gamepassword@localhost:5432/battlecards')
CARD_SERVICE_URL = os.getenv('CARD_SERVICE_URL', 'http://localhost:5002')

def get_db_connection():
    """Create and return a PostgreSQL database connection."""
    return psycopg2.connect(DATABASE_URL)

class Card:
    """Card class for game logic."""
    def __init__(self, card_type, power):
        self.type = card_type
        self.power = power
    
    def to_dict(self):
        return {'type': self.type, 'power': self.power}
    
    def beats(self, other):
        """Check if this card beats another card."""
        winning_combinations = {
            'Rock': 'Scissors',
            'Paper': 'Rock',
            'Scissors': 'Paper'
        }
        return winning_combinations.get(self.type) == other.type

def get_cards_from_service(token):
    """Get cards from card service."""
    try:
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.post(f'{CARD_SERVICE_URL}/api/cards/random-deck', 
                               headers=headers, 
                               json={'size': 22})
        if response.status_code == 200:
            return response.json()['deck']
        return None
    except:
        return None

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'game-service'}), 200

@app.route('/api/games', methods=['POST'])
@jwt_required()
def create_game():
    """Create a new game."""
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('player2_name'):
            return jsonify({'error': 'Player 2 name is required'}), 400
        
        player1_name = current_user
        player2_name = data['player2_name'].strip()
        
        # Get JWT token from request
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        # Get random decks from card service
        player1_deck = get_cards_from_service(token)
        player2_deck = get_cards_from_service(token)
        
        if not player1_deck or not player2_deck:
            return jsonify({'error': 'Failed to create decks'}), 500
        
        # Create game
        game_id = str(uuid.uuid4())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO games (
                game_id, turn, is_active, current_player,
                player1_name, player1_deck_cards, player1_hand_cards, 
                player1_score, player2_name, player2_deck_cards, 
                player2_hand_cards, player2_score
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            game_id, 1, True, 1,
            player1_name, json.dumps(player1_deck), json.dumps([]),
            0, player2_name, json.dumps(player2_deck),
            json.dumps([]), 0
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'game_id': game_id,
            'player1_name': player1_name,
            'player2_name': player2_name,
            'status': 'created',
            'turn': 1,
            'current_player': 1
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Failed to create game: {str(e)}'}), 500

@app.route('/api/games/<game_id>', methods=['GET'])
@jwt_required()
def get_game(game_id):
    """Get game state."""
    try:
        current_user = get_jwt_identity()
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT * FROM games WHERE game_id = %s", (game_id,))
        game = cursor.fetchone()
        conn.close()
        
        if not game:
            return jsonify({'error': 'Game not found'}), 404
        
        # Check if user is a player in this game
        if current_user not in [game['player1_name'], game['player2_name']]:
            return jsonify({'error': 'Unauthorized to view this game'}), 403
        
        # Parse JSON fields
        try:
            player1_deck = json.loads(game['player1_deck_cards'] or '[]')
            player1_hand = json.loads(game['player1_hand_cards'] or '[]')
            player2_deck = json.loads(game['player2_deck_cards'] or '[]')
            player2_hand = json.loads(game['player2_hand_cards'] or '[]')
        except:
            player1_deck = player1_hand = player2_deck = player2_hand = []
        
        return jsonify({
            'game_id': game['game_id'],
            'turn': game['turn'],
            'is_active': game['is_active'],
            'current_player': game['current_player'],
            'player1': {
                'name': game['player1_name'],
                'deck_size': len(player1_deck),
                'hand_size': len(player1_hand),
                'score': game['player1_score']
            },
            'player2': {
                'name': game['player2_name'],
                'deck_size': len(player2_deck),
                'hand_size': len(player2_hand),
                'score': game['player2_score']
            },
            'winner': game['winner'],
            'created_at': game['created_at'].isoformat() if game['created_at'] else None
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get game: {str(e)}'}), 500

@app.route('/api/games/<game_id>/hand', methods=['GET'])
@jwt_required()
def get_player_hand(game_id):
    """Get current player's hand."""
    try:
        current_user = get_jwt_identity()
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT * FROM games WHERE game_id = %s", (game_id,))
        game = cursor.fetchone()
        conn.close()
        
        if not game:
            return jsonify({'error': 'Game not found'}), 404
        
        # Check if user is a player in this game
        if current_user not in [game['player1_name'], game['player2_name']]:
            return jsonify({'error': 'Unauthorized to view this game'}), 403
        
        # Determine which player's hand to return
        if current_user == game['player1_name']:
            hand_data = game['player1_hand_cards']
        else:
            hand_data = game['player2_hand_cards']
        
        try:
            hand = json.loads(hand_data or '[]')
        except:
            hand = []
        
        return jsonify({
            'hand': hand,
            'player': current_user
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get hand: {str(e)}'}), 500

@app.route('/api/games/<game_id>/draw-hand', methods=['POST'])
@jwt_required()
def draw_hand(game_id):
    """Draw a new hand for the current player."""
    try:
        current_user = get_jwt_identity()
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT * FROM games WHERE game_id = %s", (game_id,))
        game = cursor.fetchone()
        
        if not game:
            conn.close()
            return jsonify({'error': 'Game not found'}), 404
        
        if not game['is_active']:
            conn.close()
            return jsonify({'error': 'Game is not active'}), 400
        
        # Determine player
        is_player1 = current_user == game['player1_name']
        if not is_player1 and current_user != game['player2_name']:
            conn.close()
            return jsonify({'error': 'Unauthorized to play this game'}), 403
        
        # Parse deck
        deck_field = 'player1_deck_cards' if is_player1 else 'player2_deck_cards'
        hand_field = 'player1_hand_cards' if is_player1 else 'player2_hand_cards'
        
        try:
            deck = json.loads(game[deck_field] or '[]')
        except:
            deck = []
        
        if len(deck) < 3:
            conn.close()
            return jsonify({'error': 'Not enough cards in deck'}), 400
        
        # Draw 3 cards
        hand = random.sample(deck, 3)
        remaining_deck = [card for card in deck if card not in hand]
        
        # Update database
        cursor = conn.cursor()
        cursor.execute(f"""
            UPDATE games 
            SET {deck_field} = %s, {hand_field} = %s 
            WHERE game_id = %s
        """, (json.dumps(remaining_deck), json.dumps(hand), game_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'hand': hand,
            'deck_size': len(remaining_deck)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to draw hand: {str(e)}'}), 500

@app.route('/api/games/<game_id>/play-card', methods=['POST'])
@jwt_required()
def play_card(game_id):
    """Play a card from hand."""
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'card_index' not in data:
            return jsonify({'error': 'Card index is required'}), 400
        
        card_index = data['card_index']
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT * FROM games WHERE game_id = %s", (game_id,))
        game = cursor.fetchone()
        
        if not game:
            conn.close()
            return jsonify({'error': 'Game not found'}), 404
        
        if not game['is_active']:
            conn.close()
            return jsonify({'error': 'Game is not active'}), 400
        
        # Determine player
        is_player1 = current_user == game['player1_name']
        if not is_player1 and current_user != game['player2_name']:
            conn.close()
            return jsonify({'error': 'Unauthorized to play this game'}), 403
        
        # Parse hand
        hand_field = 'player1_hand_cards' if is_player1 else 'player2_hand_cards'
        played_field = 'player1_played_card' if is_player1 else 'player2_played_card'
        
        try:
            hand = json.loads(game[hand_field] or '[]')
        except:
            hand = []
        
        if not hand or card_index < 0 or card_index >= len(hand):
            conn.close()
            return jsonify({'error': 'Invalid card index'}), 400
        
        # Play the card
        played_card = hand[card_index]
        remaining_hand = [card for i, card in enumerate(hand) if i != card_index]
        
        # Update database
        cursor = conn.cursor()
        cursor.execute(f"""
            UPDATE games 
            SET {hand_field} = %s, {played_field} = %s 
            WHERE game_id = %s
        """, (json.dumps(remaining_hand), json.dumps(played_card), game_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'played_card': played_card,
            'remaining_hand': remaining_hand
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to play card: {str(e)}'}), 500

@app.route('/api/games/<game_id>/resolve-round', methods=['POST'])
@jwt_required()
def resolve_round(game_id):
    """Resolve a round after both players have played cards."""
    try:
        current_user = get_jwt_identity()
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT * FROM games WHERE game_id = %s", (game_id,))
        game = cursor.fetchone()
        
        if not game:
            conn.close()
            return jsonify({'error': 'Game not found'}), 404
        
        if not game['is_active']:
            conn.close()
            return jsonify({'error': 'Game is not active'}), 400
        
        # Check if user is a player
        if current_user not in [game['player1_name'], game['player2_name']]:
            conn.close()
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Parse played cards
        try:
            player1_card_data = json.loads(game['player1_played_card'] or 'null')
            player2_card_data = json.loads(game['player2_played_card'] or 'null')
        except:
            player1_card_data = player2_card_data = None
        
        if not player1_card_data or not player2_card_data:
            conn.close()
            return jsonify({'error': 'Both players must play cards before resolving'}), 400
        
        # Create card objects
        player1_card = Card(player1_card_data['type'], player1_card_data['power'])
        player2_card = Card(player2_card_data['type'], player2_card_data['power'])
        
        # Determine round winner
        round_winner = None
        if player1_card.beats(player2_card):
            round_winner = 1
        elif player2_card.beats(player1_card):
            round_winner = 2
        else:
            # Tie, check power
            if player1_card.power > player2_card.power:
                round_winner = 1
            elif player2_card.power > player1_card.power:
                round_winner = 2
            # Otherwise it's a tie
        
        # Update scores
        new_p1_score = game['player1_score']
        new_p2_score = game['player2_score']
        
        if round_winner == 1:
            new_p1_score += 1
        elif round_winner == 2:
            new_p2_score += 1
        
        # Check if game should end (not enough cards)
        try:
            p1_deck = json.loads(game['player1_deck_cards'] or '[]')
            p2_deck = json.loads(game['player2_deck_cards'] or '[]')
        except:
            p1_deck = p2_deck = []
        
        game_over = len(p1_deck) < 3 or len(p2_deck) < 3
        winner = None
        
        if game_over:
            if new_p1_score > new_p2_score:
                winner = game['player1_name']
            elif new_p2_score > new_p1_score:
                winner = game['player2_name']
            # Otherwise tie
        
        # Update database
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE games 
            SET player1_score = %s, player2_score = %s, 
                player1_played_card = NULL, player2_played_card = NULL,
                player1_hand_cards = '[]', player2_hand_cards = '[]',
                is_active = %s, winner = %s, turn = turn + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE game_id = %s
        """, (new_p1_score, new_p2_score, not game_over, winner, game_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'round_winner': round_winner,
            'player1_card': player1_card_data,
            'player2_card': player2_card_data,
            'player1_score': new_p1_score,
            'player2_score': new_p2_score,
            'game_over': game_over,
            'winner': winner
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to resolve round: {str(e)}'}), 500

@app.route('/api/games/<game_id>/end', methods=['POST'])
@jwt_required()
def end_game(game_id):
    """End a game."""
    try:
        current_user = get_jwt_identity()
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT * FROM games WHERE game_id = %s", (game_id,))
        game = cursor.fetchone()
        
        if not game:
            conn.close()
            return jsonify({'error': 'Game not found'}), 404
        
        # Check if user is a player
        if current_user not in [game['player1_name'], game['player2_name']]:
            conn.close()
            return jsonify({'error': 'Unauthorized'}), 403
        
        # End the game
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE games 
            SET is_active = false, updated_at = CURRENT_TIMESTAMP 
            WHERE game_id = %s
        """, (game_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Game ended successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to end game: {str(e)}'}), 500

@app.route('/api/games/user/<username>', methods=['GET'])
@jwt_required()
def get_user_games(username):
    """Get all games for a user."""
    try:
        current_user = get_jwt_identity()
        
        # Users can only view their own games
        if current_user != username:
            return jsonify({'error': 'Unauthorized'}), 403
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT game_id, turn, is_active, player1_name, player2_name, 
                   player1_score, player2_score, winner, created_at
            FROM games 
            WHERE player1_name = %s OR player2_name = %s 
            ORDER BY created_at DESC
        """, (username, username))
        
        games = cursor.fetchall()
        conn.close()
        
        game_list = []
        for game in games:
            game_list.append({
                'game_id': game['game_id'],
                'turn': game['turn'],
                'is_active': game['is_active'],
                'player1_name': game['player1_name'],
                'player2_name': game['player2_name'],
                'player1_score': game['player1_score'],
                'player2_score': game['player2_score'],
                'winner': game['winner'],
                'created_at': game['created_at'].isoformat() if game['created_at'] else None
            })
        
        return jsonify({'games': game_list}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get user games: {str(e)}'}), 500

if __name__ == '__main__':
    # For development only
    app.run(host='0.0.0.0', port=5003, debug=True)