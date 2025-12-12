"""
Leaderboard Service - Game results and rankings microservice
"""

import os
import sys
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Add utils directory to path for input sanitizer
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'utils'))
from input_sanitizer import InputSanitizer, SecurityMiddleware, require_sanitized_input

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')

# Initialize extensions
jwt = JWTManager(app)
CORS(app)
security = SecurityMiddleware(app)

# JWT error handlers - convert 422 to 401 for invalid tokens
@jwt.invalid_token_loader
def invalid_token_callback(error_string):
    """Handle invalid token errors."""
    return jsonify({'error': 'Invalid token'}), 401

@jwt.unauthorized_loader
def unauthorized_callback(error_string):
    """Handle missing token errors."""
    return jsonify({'error': 'Missing authorization header'}), 401

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    """Handle expired token errors."""
    return jsonify({'error': 'Token has expired'}), 401

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://gameuser:gamepassword@localhost:5432/battlecards')

def get_db_connection():
    """Create and return a PostgreSQL database connection."""
    return psycopg2.connect(DATABASE_URL)

@app.route('/health', methods=['GET'])
@app.route('/api/leaderboard/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'leaderboard-service'}), 200

@app.route('/api/leaderboard', methods=['GET'])
@jwt_required()
def get_leaderboard():
    """Get the global leaderboard."""
    try:
        # Validate and sanitize limit parameter
        limit_param = request.args.get('limit', '10')
        try:
            limit = InputSanitizer.validate_integer(limit_param, min_val=1, max_val=100)
        except ValueError:
            limit = 10  # Default to 10 if invalid
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Calculate wins for each player
        cursor.execute("""
            WITH player_stats AS (
                -- Player 1 wins
                SELECT player1_name as player, COUNT(*) as wins
                FROM games 
                WHERE game_status IN ('completed', 'abandoned') AND winner = player1_name
                GROUP BY player1_name
                
                UNION ALL
                
                -- Player 2 wins
                SELECT player2_name as player, COUNT(*) as wins
                FROM games 
                WHERE game_status IN ('completed', 'abandoned') AND winner = player2_name
                GROUP BY player2_name
            ),
            total_games AS (
                -- Total games for each player
                SELECT player1_name as player, COUNT(*) as total_games
                FROM games
                WHERE game_status IN ('completed', 'abandoned')
                GROUP BY player1_name
                
                UNION ALL
                
                SELECT player2_name as player, COUNT(*) as total_games
                FROM games
                WHERE game_status IN ('completed', 'abandoned')
                GROUP BY player2_name
            ),
            aggregated_stats AS (
                SELECT 
                    COALESCE(p.player, t.player) as player,
                    SUM(p.wins) as total_wins,
                    SUM(t.total_games) as total_games
                FROM player_stats p
                FULL OUTER JOIN total_games t ON p.player = t.player
                GROUP BY COALESCE(p.player, t.player)
            )
            SELECT 
                player,
                COALESCE(total_wins, 0) as wins,
                COALESCE(total_games, 0) as games,
                CASE 
                    WHEN COALESCE(total_games, 0) = 0 THEN 0 
                    ELSE ROUND((COALESCE(total_wins, 0)::decimal / total_games) * 100, 2)
                END as win_percentage
            FROM aggregated_stats
            WHERE player IS NOT NULL
            ORDER BY wins DESC, win_percentage DESC, games DESC
            LIMIT %s
        """, (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        leaderboard = []
        for i, player in enumerate(results, 1):
            leaderboard.append({
                'rank': i,
                'player': player['player'],
                'wins': player['wins'],
                'games': player['games'],
                'losses': player['games'] - player['wins'],
                'win_percentage': float(player['win_percentage'])
            })
        
        return jsonify({
            'leaderboard': leaderboard,
            'total_players': len(leaderboard)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get leaderboard: {str(e)}'}), 500

@app.route('/api/leaderboard/my-matches', methods=['GET'])
@jwt_required()
def get_my_matches():
    """Get match history for the authenticated user."""
    try:
        # Get username from JWT token
        from flask_jwt_extended import get_jwt_identity
        username = get_jwt_identity()
        
        if not username:
            return jsonify({'error': 'Unable to identify user'}), 401
        
        # Validate and sanitize username
        try:
            username = InputSanitizer.validate_username(username)
        except ValueError as e:
            return jsonify({'error': f'Invalid username: {str(e)}'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get all matches for this player
        cursor.execute("""
            SELECT 
                game_id,
                player1_name,
                player2_name,
                player1_score,
                player2_score,
                winner,
                created_at
            FROM games 
            WHERE game_status IN ('completed', 'abandoned')
            AND game_status != 'ignored'
            AND (player1_name = %s OR player2_name = %s)
            ORDER BY created_at DESC
        """, (username, username))
        
        games = cursor.fetchall()
        conn.close()
        
        matches = []
        for game in games:
            opponent = game['player2_name'] if game['player1_name'] == username else game['player1_name']
            my_score = game['player1_score'] if game['player1_name'] == username else game['player2_score']
            opponent_score = game['player2_score'] if game['player1_name'] == username else game['player1_score']
            result = 'win' if game['winner'] == username else 'loss'
            
            matches.append({
                'game_id': game['game_id'],
                'opponent': opponent,
                'my_score': my_score,
                'opponent_score': opponent_score,
                'result': result,
                'date': game['created_at'].isoformat() if game['created_at'] else None
            })
        
        return jsonify({
            'matches': matches,
            'total': len(matches)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get matches: {str(e)}'}), 500

@app.route('/api/leaderboard/player/<player_name>', methods=['GET'])
@jwt_required()
def get_player_stats(player_name):
    """Get detailed statistics for a specific player."""
    try:
        # Validate and sanitize player name
        try:
            player_name = InputSanitizer.validate_username(player_name)
        except ValueError as e:
            return jsonify({'error': f'Invalid player name: {str(e)}'}), 400
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get player's overall stats
        cursor.execute("""
            WITH player_wins AS (
                SELECT COUNT(*) as wins
                FROM games 
                WHERE game_status IN ('completed', 'abandoned')
                AND (
                    (winner = player1_name AND player1_name = %s) OR 
                    (winner = player2_name AND player2_name = %s)
                )
            ),
            player_games AS (
                SELECT COUNT(*) as total_games
                FROM games 
                WHERE game_status IN ('completed', 'abandoned')
                AND (player1_name = %s OR player2_name = %s)
            )
            SELECT 
                p.wins,
                g.total_games,
                (g.total_games - p.wins) as losses,
                CASE 
                    WHEN g.total_games = 0 THEN 0 
                    ELSE ROUND((p.wins::decimal / g.total_games) * 100, 2)
                END as win_percentage
            FROM player_wins p, player_games g
        """, (player_name, player_name, player_name, player_name))
        
        stats = cursor.fetchone()
        
        if not stats or stats['total_games'] == 0:
            conn.close()
            return jsonify({
                'player': player_name,
                'wins': 0,
                'losses': 0,
                'total_games': 0,
                'win_percentage': 0,
                'recent_games': []
            }), 200
        
        # Get recent games
        cursor.execute("""
            SELECT 
                game_id,
                player1_name,
                player2_name,
                player1_score,
                player2_score,
                winner,
                created_at
            FROM games 
            WHERE game_status IN ('completed', 'abandoned')
            AND (player1_name = %s OR player2_name = %s)
            ORDER BY created_at DESC
            LIMIT 10
        """, (player_name, player_name))
        
        recent_games = cursor.fetchall()
        conn.close()
        
        games_list = []
        for game in recent_games:
            opponent = game['player2_name'] if game['player1_name'] == player_name else game['player1_name']
            player_score = game['player1_score'] if game['player1_name'] == player_name else game['player2_score']
            opponent_score = game['player2_score'] if game['player1_name'] == player_name else game['player1_score']
            result = 'win' if game['winner'] == player_name else ('loss' if game['winner'] else 'tie')
            
            games_list.append({
                'game_id': game['game_id'],
                'opponent': opponent,
                'player_score': player_score,
                'opponent_score': opponent_score,
                'result': result,
                'date': game['created_at'].isoformat() if game['created_at'] else None
            })
        
        return jsonify({
            'player': player_name,
            'wins': stats['wins'],
            'losses': stats['losses'],
            'total_games': stats['total_games'],
            'win_percentage': float(stats['win_percentage']),
            'recent_games': games_list
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get player stats: {str(e)}'}), 500

@app.route('/api/leaderboard/recent-games', methods=['GET'])
@jwt_required()
def get_recent_games():
    """Get recent completed games."""
    try:
        # Validate and sanitize limit parameter
        limit_param = request.args.get('limit', '10')
        try:
            limit = InputSanitizer.validate_integer(limit_param, min_val=1, max_val=50)
        except ValueError:
            limit = 10  # Default to 10 if invalid
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                game_id,
                player1_name,
                player2_name,
                player1_score,
                player2_score,
                winner,
                turn,
                created_at,
                updated_at
            FROM games 
            WHERE game_status IN ('completed', 'abandoned')
            ORDER BY updated_at DESC
            LIMIT %s
        """, (limit,))
        
        games = cursor.fetchall()
        conn.close()
        
        games_list = []
        for game in games:
            games_list.append({
                'game_id': game['game_id'],
                'player1_name': game['player1_name'],
                'player2_name': game['player2_name'],
                'player1_score': game['player1_score'],
                'player2_score': game['player2_score'],
                'winner': game['winner'],
                'duration_turns': game['turn'],
                'started_at': game['created_at'].isoformat() if game['created_at'] else None,
                'completed_at': game['updated_at'].isoformat() if game['updated_at'] else None
            })
        
        return jsonify({
            'recent_games': games_list,
            'total_games': len(games_list)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get recent games: {str(e)}'}), 500

@app.route('/api/leaderboard/top-players', methods=['GET'])
@jwt_required()
def get_top_players():
    """Get top players by different metrics."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Top players by wins (respecting show_on_leaderboard preference)
        cursor.execute("""
            WITH player_stats AS (
                SELECT g.player1_name as player, COUNT(*) as wins
                FROM games g
                INNER JOIN users u ON g.player1_name = u.username
                WHERE g.game_status IN ('completed', 'abandoned') 
                AND g.winner = g.player1_name
                AND u.show_on_leaderboard = TRUE
                GROUP BY g.player1_name
                
                UNION ALL
                
                SELECT g.player2_name as player, COUNT(*) as wins
                FROM games g
                INNER JOIN users u ON g.player2_name = u.username
                WHERE g.game_status IN ('completed', 'abandoned') 
                AND g.winner = g.player2_name
                AND u.show_on_leaderboard = TRUE
                GROUP BY g.player2_name
            )
            SELECT 
                player,
                SUM(wins) as total_wins
            FROM player_stats
            WHERE player IS NOT NULL
            GROUP BY player
            ORDER BY total_wins DESC
            LIMIT 5
        """)
        
        top_by_wins = cursor.fetchall()
        
        # Top players by win percentage (min 5 games, respecting show_on_leaderboard preference)
        cursor.execute("""
            WITH visible_players AS (
                -- Get all visible players first
                SELECT username 
                FROM users 
                WHERE show_on_leaderboard = TRUE
            ),
            player_wins AS (
                SELECT player, SUM(wins) as total_wins
                FROM (
                    SELECT player1_name as player, COUNT(*) as wins
                    FROM games 
                    WHERE game_status IN ('completed', 'abandoned') 
                    AND winner = player1_name
                    AND player1_name IN (SELECT username FROM visible_players)
                    GROUP BY player1_name
                    
                    UNION ALL
                    
                    SELECT player2_name as player, COUNT(*) as wins
                    FROM games 
                    WHERE game_status IN ('completed', 'abandoned') 
                    AND winner = player2_name
                    AND player2_name IN (SELECT username FROM visible_players)
                    GROUP BY player2_name
                ) wins_subquery
                GROUP BY player
            ),
            player_games AS (
                SELECT player, SUM(games) as total_games
                FROM (
                    SELECT player1_name as player, COUNT(*) as games
                    FROM games
                    WHERE game_status IN ('completed', 'abandoned')
                    AND player1_name IN (SELECT username FROM visible_players)
                    GROUP BY player1_name
                    
                    UNION ALL
                    
                    SELECT player2_name as player, COUNT(*) as games
                    FROM games
                    WHERE game_status IN ('completed', 'abandoned')
                    AND player2_name IN (SELECT username FROM visible_players)
                    GROUP BY player2_name
                ) games_subquery
                GROUP BY player
            )
            SELECT 
                pg.player,
                COALESCE(pw.total_wins, 0) as wins,
                pg.total_games as games,
                ROUND((COALESCE(pw.total_wins, 0)::decimal / pg.total_games) * 100, 2) as win_percentage
            FROM player_games pg
            LEFT JOIN player_wins pw ON pg.player = pw.player
            WHERE pg.total_games >= 1
            ORDER BY win_percentage DESC
            LIMIT 5
        """)
        
        top_by_percentage = cursor.fetchall()
        
        # Most active players (respecting show_on_leaderboard preference)
        cursor.execute("""
            WITH total_games AS (
                SELECT g.player1_name as player, COUNT(*) as total_games
                FROM games g
                INNER JOIN users u ON g.player1_name = u.username
                WHERE g.game_status IN ('completed', 'abandoned')
                AND u.show_on_leaderboard = TRUE
                GROUP BY g.player1_name
                
                UNION ALL
                
                SELECT g.player2_name as player, COUNT(*) as total_games
                FROM games g
                INNER JOIN users u ON g.player2_name = u.username
                WHERE g.game_status IN ('completed', 'abandoned')
                AND u.show_on_leaderboard = TRUE
                GROUP BY g.player2_name
            )
            SELECT 
                player,
                SUM(total_games) as total_games
            FROM total_games
            WHERE player IS NOT NULL
            GROUP BY player
            ORDER BY total_games DESC
            LIMIT 5
        """)
        
        most_active = cursor.fetchall()
        conn.close()
        
        return jsonify({
            'top_by_wins': [
                {
                    'player': row['player'], 
                    'wins': row['total_wins']
                } for row in top_by_wins
            ],
            'top_by_win_percentage': [
                {
                    'player': row['player'], 
                    'wins': row['wins'],
                    'games': row['games'],
                    'win_percentage': float(row['win_percentage'])
                } for row in top_by_percentage
            ],
            'most_active': [
                {
                    'player': row['player'], 
                    'total_games': row['total_games']
                } for row in most_active
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get top players: {str(e)}'}), 500

@app.route('/api/leaderboard/statistics', methods=['GET'])
@jwt_required()
def get_global_statistics():
    """Get global game statistics."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Total games and players
        cursor.execute("""
            SELECT 
                COUNT(*) as total_games,
                COUNT(DISTINCT player1_name) + COUNT(DISTINCT player2_name) as unique_players
            FROM games 
            WHERE game_status IN ('completed', 'abandoned')
        """)
        
        basic_stats = cursor.fetchone()
        
        # Games by outcome
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN winner IS NOT NULL THEN 1 END) as games_with_winner,
                COUNT(CASE WHEN winner IS NULL THEN 1 END) as tied_games
            FROM games 
            WHERE game_status IN ('completed', 'abandoned')
        """)
        
        outcome_stats = cursor.fetchone()
        
        # Average game duration
        cursor.execute("""
            SELECT 
                AVG(turn) as avg_game_turns,
                MIN(turn) as shortest_game,
                MAX(turn) as longest_game
            FROM games 
            WHERE game_status IN ('completed', 'abandoned')
        """)
        
        duration_stats = cursor.fetchone()
        
        # Recent activity (games in last 7 days)
        cursor.execute("""
            SELECT COUNT(*) as games_last_week
            FROM games 
            WHERE game_status IN ('completed', 'abandoned')
            AND created_at >= %s
        """, (datetime.now() - timedelta(days=7),))
        
        recent_activity = cursor.fetchone()
        conn.close()
        
        return jsonify({
            'total_completed_games': basic_stats['total_games'],
            'unique_players': basic_stats['unique_players'], 
            'games_with_winner': outcome_stats['games_with_winner'],
            'tied_games': outcome_stats['tied_games'],
            'average_game_turns': round(float(duration_stats['avg_game_turns']), 2) if duration_stats['avg_game_turns'] else 0,
            'shortest_game_turns': duration_stats['shortest_game'],
            'longest_game_turns': duration_stats['longest_game'],
            'games_last_week': recent_activity['games_last_week']
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get statistics: {str(e)}'}), 500

@app.route('/api/leaderboard/rankings', methods=['GET'])
@jwt_required()
def get_rankings():
    """Get the global leaderboard rankings based on number of wins."""
    try:
        # Validate and sanitize limit parameter
        limit_param = request.args.get('limit', '100')
        try:
            limit = InputSanitizer.validate_integer(limit_param, min_val=1, max_val=500)
        except ValueError:
            limit = 100  # Default to 100 if invalid
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Calculate wins, total score, and games played for each player
        # Only include users who have show_on_leaderboard = TRUE
        cursor.execute("""
            WITH player_stats AS (
                -- Player 1 stats
                SELECT 
                    g.player1_name as player,
                    SUM(CASE WHEN g.winner = g.player1_name THEN 1 ELSE 0 END) as wins,
                    SUM(g.player1_score) as total_score,
                    COUNT(*) as games_played
                FROM games g
                INNER JOIN users u ON g.player1_name = u.username
                WHERE g.game_status IN ('completed', 'abandoned')
                AND u.show_on_leaderboard = TRUE
                GROUP BY g.player1_name
                
                UNION ALL
                
                -- Player 2 stats
                SELECT 
                    g.player2_name as player,
                    SUM(CASE WHEN g.winner = g.player2_name THEN 1 ELSE 0 END) as wins,
                    SUM(g.player2_score) as total_score,
                    COUNT(*) as games_played
                FROM games g
                INNER JOIN users u ON g.player2_name = u.username
                WHERE g.game_status IN ('completed', 'abandoned')
                AND u.show_on_leaderboard = TRUE
                GROUP BY g.player2_name
            )
            SELECT 
                player,
                SUM(wins) as total_wins,
                SUM(total_score) as total_score,
                SUM(games_played) as total_games
            FROM player_stats
            WHERE player IS NOT NULL
            GROUP BY player
            ORDER BY total_wins DESC, total_score DESC, total_games DESC
            LIMIT %s
        """, (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        rankings = []
        for i, player in enumerate(results, 1):
            rankings.append({
                'rank': i,
                'username': player['player'],
                'wins': player['total_wins'],
                'total_score': player['total_score'],
                'games_played': player['total_games']
            })
        
        return jsonify({
            'rankings': rankings,
            'total_players': len(rankings)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get rankings: {str(e)}'}), 500

@app.route('/api/leaderboard/visibility', methods=['PUT'])
@jwt_required()
def update_visibility():
    """Update the authenticated user's leaderboard visibility preference."""
    try:
        # Get username from JWT token
        from flask_jwt_extended import get_jwt_identity
        username = get_jwt_identity()
        
        if not username:
            return jsonify({'error': 'Unable to identify user'}), 401
        
        # Validate and sanitize username
        try:
            username = InputSanitizer.validate_username(username)
        except ValueError as e:
            return jsonify({'error': f'Invalid username: {str(e)}'}), 400
        
        # Get the visibility preference from request body
        data = request.get_json()
        if data is None or 'show_on_leaderboard' not in data:
            return jsonify({'error': 'Missing show_on_leaderboard parameter'}), 400
        
        show_on_leaderboard = data.get('show_on_leaderboard')
        
        # Validate boolean value
        if not isinstance(show_on_leaderboard, bool):
            return jsonify({'error': 'show_on_leaderboard must be a boolean'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update user's visibility preference
        cursor.execute("""
            UPDATE users 
            SET show_on_leaderboard = %s 
            WHERE username = %s
        """, (show_on_leaderboard, username))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'User not found'}), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'Visibility preference updated successfully',
            'show_on_leaderboard': show_on_leaderboard
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to update visibility: {str(e)}'}), 500

@app.route('/api/leaderboard/visibility', methods=['GET'])
@jwt_required()
def get_visibility():
    """Get the authenticated user's leaderboard visibility preference."""
    try:
        # Get username from JWT token
        from flask_jwt_extended import get_jwt_identity
        username = get_jwt_identity()
        
        if not username:
            return jsonify({'error': 'Unable to identify user'}), 401
        
        # Validate and sanitize username
        try:
            username = InputSanitizer.validate_username(username)
        except ValueError as e:
            return jsonify({'error': f'Invalid username: {str(e)}'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get user's visibility preference
        cursor.execute("""
            SELECT show_on_leaderboard 
            FROM users 
            WHERE username = %s
        """, (username,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'show_on_leaderboard': result['show_on_leaderboard']
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get visibility: {str(e)}'}), 500

if __name__ == '__main__':
    # For development only - debug mode controlled by environment variable
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    app.run(host='0.0.0.0', port=5004, debug=debug_mode)