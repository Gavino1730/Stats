from flask import Flask, render_template, jsonify, request
from functools import lru_cache
import json
import os
from datetime import datetime
import requests
from dotenv import load_dotenv
from src.advanced_stats import AdvancedStatsCalculator
import logging

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the project root directory (parent of src/)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, 
            template_folder=os.path.join(project_root, 'templates'),
            static_folder=os.path.join(project_root, 'static'))
app.config['JSON_SORT_KEYS'] = False
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 year cache for static files
app.config['COMPRESS_LEVEL'] = 6  # Gzip compression

# Security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'"
    return response

# Constants
EXCLUDED_PLAYERS = {'Matthew Gunther', 'Liam Plep', 'Gavin Galan', 'Kye Fixter'}
FREE_THROW_POSSESSION_FACTOR = 0.44
MIN_GAMES_FOR_VARIANCE = 2

# OpenAI API configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_API_URL = 'https://api.openai.com/v1/chat/completions'

# Analysis cache file
ANALYSIS_CACHE_FILE = os.path.join(project_root, 'data/season_analysis.json')
PLAYER_ANALYSIS_CACHE_FILE = os.path.join(project_root, 'data/player_analysis_cache.json')

# Load stats data
STATS_FILE = os.path.join(project_root, 'data/vc_stats_output.json')
ROSTER_FILE = os.path.join(project_root, 'data/roster.json')

try:
    with open(STATS_FILE) as f:
        stats_data = json.load(f)
    logger.info(f"Loaded stats data: {len(stats_data.get('games', []))} games")
except FileNotFoundError:
    logger.error(f"Stats file not found: {STATS_FILE}")
    stats_data = {'games': [], 'season_team_stats': {}, 'season_player_stats': {}, 'player_game_logs': {}}
except json.JSONDecodeError as e:
    logger.error(f"Invalid JSON in stats file: {e}")
    stats_data = {'games': [], 'season_team_stats': {}, 'season_player_stats': {}, 'player_game_logs': {}}

try:
    with open(ROSTER_FILE) as f:
        roster_data = json.load(f)
except FileNotFoundError:
    logger.warning(f"Roster file not found: {ROSTER_FILE}")
    roster_data = {'roster': []}
except json.JSONDecodeError as e:
    logger.error(f"Invalid JSON in roster file: {e}")
    roster_data = {'roster': []}

# Initialize advanced stats calculator
advanced_calc = AdvancedStatsCalculator(stats_data)

@app.route('/')
def dashboard():
    """Main dashboard with season overview"""
    return render_template('dashboard.html')

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'games_loaded': len(stats_data.get('games', [])),
        'players_loaded': len(stats_data.get('season_player_stats', {})),
        'openai_configured': bool(OPENAI_API_KEY)
    })

@app.route('/games')
def games():
    """Games list and box scores"""
    return render_template('games.html')

@app.route('/players')
def players():
    """Player stats and profiles"""
    return render_template('players.html')

@app.route('/trends')
def trends():
    """Player and team trends"""
    return render_template('trends.html')

@app.route('/ai-insights')
def ai_insights():
    """AI Coach analysis and insights"""
    return render_template('ai-insights.html')

@app.route('/analysis')
def analysis():
    """Comprehensive season analysis page"""
    return render_template('analysis.html')

# API Endpoints
@app.route('/api/season-stats')
@lru_cache(maxsize=1)
def api_season_stats():
    """Get season team stats - cached for performance"""
    return jsonify(stats_data['season_team_stats'])

@app.route('/api/games')
def api_games():
    """Get all games"""
    games = stats_data['games']
    # Sort by gameId
    games = sorted(games, key=lambda x: x['gameId'])
    return jsonify(games)

@app.route('/api/game/<int:game_id>')
def api_game(game_id):
    """Get specific game details"""
    for game in stats_data['games']:
        if game['gameId'] == game_id:
            return jsonify(game)
    return jsonify({'error': 'Game not found'}), 404

@app.route('/api/players')
def api_players():
    """Get all player season stats with enhanced metrics"""
    players = list(stats_data['season_player_stats'].values())
    
    # Merge in roster information (number, grade)
    roster_dict = {p['name']: p for p in roster_data['roster']}
    
    enhanced_players = []
    for player in players:
        enhanced_player = player.copy()
        
        # Add roster info
        if player['name'] in roster_dict:
            enhanced_player['number'] = roster_dict[player['name']].get('number')
            enhanced_player['grade'] = roster_dict[player['name']].get('grade')
        
        # Add calculated per-game stats
        games = player.get('games', 1)
        enhanced_player['spg'] = player.get('stl', 0) / games
        enhanced_player['bpg'] = player.get('blk', 0) / games
        enhanced_player['tpg'] = player.get('to', 0) / games
        enhanced_player['fpg'] = player.get('fouls', 0) / games
        
        # Add some advanced metrics directly
        advanced_stats = advanced_calc.calculate_player_advanced_stats(player['name'])
        if advanced_stats:
            enhanced_player['efg_pct'] = advanced_stats['scoring_efficiency']['efg_pct']
            enhanced_player['ts_pct'] = advanced_stats['scoring_efficiency']['ts_pct']
            enhanced_player['per'] = advanced_stats['scoring_efficiency']['per']
            enhanced_player['usage_rate'] = advanced_stats['usage_role']['usage_proxy']
            enhanced_player['ast_to_ratio'] = advanced_stats['ball_handling']['ast_to_ratio']
            enhanced_player['defensive_rating'] = advanced_stats['defense_activity']['defensive_rating']
            enhanced_player['pm_per_game'] = advanced_stats['impact']['pm_per_game']
            enhanced_player['role'] = advanced_stats['usage_role']['role']
            enhanced_player['consistency_score'] = advanced_stats['consistency']['consistency_score']
            enhanced_player['clutch_factor'] = advanced_stats['clutch_performance']['clutch_factor']
        
        enhanced_players.append(enhanced_player)
    
    # Sort by PPG
    enhanced_players = sorted(enhanced_players, key=lambda x: x['ppg'], reverse=True)
    return jsonify(enhanced_players)

@app.route('/api/player/<player_name>')
def api_player(player_name):
    """Get specific player details and game logs"""
    # Sanitize player name
    player_name = player_name.strip()
    if not player_name or len(player_name) > 100:
        return jsonify({'error': 'Invalid player name'}), 400
    
    if player_name in stats_data['season_player_stats']:
        season_stats = stats_data['season_player_stats'][player_name]
        game_logs = []
        if player_name in stats_data['player_game_logs']:
            game_logs = stats_data['player_game_logs'][player_name]
        
        # Get roster info
        roster_info = None
        for player in roster_data['roster']:
            if player['name'] == player_name:
                roster_info = player
                break
        
        return jsonify({
            'season_stats': season_stats,
            'game_logs': game_logs,
            'roster_info': roster_info
        })
    return jsonify({'error': 'Player not found'}), 404

@lru_cache(maxsize=1)
def get_leaderboards_data():
    """Get leaderboards for various stats - cached"""
    players = list(stats_data['season_player_stats'].values())
    
    leaderboards = {
        'pts': sorted(players, key=lambda x: x['pts'], reverse=True)[:10],
        'reb': sorted(players, key=lambda x: x['reb'], reverse=True)[:10],
        'asst': sorted(players, key=lambda x: x['asst'], reverse=True)[:10],
        'fg_pct': sorted([p for p in players if p['fga'] > 0], key=lambda x: x['fg_pct'], reverse=True)[:10],
        'fg3_pct': sorted([p for p in players if p['fg3a'] > 0], key=lambda x: x['fg3_pct'], reverse=True)[:10],
        'ft_pct': sorted([p for p in players if p['fta'] > 0], key=lambda x: x['ft_pct'], reverse=True)[:10],
        'stl': sorted(players, key=lambda x: x.get('stl', 0), reverse=True)[:10],
        'blk': sorted(players, key=lambda x: x.get('blk', 0), reverse=True)[:10],
    }
    
    return leaderboards

@app.route('/api/leaderboards')
def api_leaderboards():
    """Get leaderboards endpoint"""
    return jsonify(get_leaderboards_data())

@app.route('/api/player-trends/<player_name>')
def api_player_trends(player_name):
    """Get player performance trends across games"""
    # Sanitize player name
    player_name = player_name.strip()
    if not player_name or len(player_name) > 100:
        return jsonify({'error': 'Invalid player name'}), 400
    
    if player_name in stats_data['player_game_logs']:
        games = stats_data['player_game_logs'][player_name]
        # Sort by gameId
        games = sorted(games, key=lambda x: x['gameId'])
        
        trends = {
            'games': [g['gameId'] for g in games],
            'opponents': [g['opponent'] for g in games],
            'dates': [g['date'] for g in games],
            'pts': [g['stats']['pts'] for g in games],
            'fg': [g['stats']['fg_made'] for g in games],
            'fg_att': [g['stats']['fg_att'] for g in games],
            'fg3': [g['stats']['fg3_made'] for g in games],
            'asst': [g['stats']['asst'] for g in games],
            'reb': [g['stats']['oreb'] + g['stats']['dreb'] for g in games],
            'stl': [g['stats']['stl'] for g in games],
        }
        return jsonify(trends)
    return jsonify({'error': 'Player not found'}), 404

@app.route('/api/team-trends')
@lru_cache(maxsize=1)
def api_team_trends():
    """Get team performance trends across games - cached"""
    games = sorted(stats_data['games'], key=lambda x: x['gameId'])
    
    trends = {
        'games': [g['gameId'] for g in games],
        'opponents': [g['opponent'] for g in games],
        'dates': [g['date'] for g in games],
        'vc_score': [g['vc_score'] for g in games],
        'opp_score': [g['opp_score'] for g in games],
        'fg_pct': [g['team_stats']['fg']/g['team_stats']['fga']*100 if g['team_stats']['fga'] > 0 else 0 for g in games],
        'fg3_pct': [g['team_stats']['fg3']/g['team_stats']['fg3a']*100 if g['team_stats']['fg3a'] > 0 else 0 for g in games],
        'asst': [g['team_stats']['asst'] for g in games],
        'to': [g['team_stats']['to'] for g in games],
    }
    return jsonify(trends)

# ==============================================================================
# ADVANCED STATS API ENDPOINTS
# ==============================================================================

# Advanced stats cached functions
@lru_cache(maxsize=1)
def get_team_advanced():
    return advanced_calc.calculate_team_advanced_stats()

@lru_cache(maxsize=1)
def get_patterns():
    return advanced_calc.calculate_win_loss_patterns()

@lru_cache(maxsize=1)
def get_volatility():
    return advanced_calc.calculate_volatility_metrics()

@lru_cache(maxsize=1)
def get_auto_insights():
    return advanced_calc.generate_auto_insights()

# Advanced stats routes
@app.route('/api/advanced/team')
def api_team_advanced():
    """Get comprehensive advanced team statistics"""
    return jsonify(get_team_advanced())

@app.route('/api/advanced/player/<player_name>')
def api_player_advanced(player_name):
    """Get advanced statistics for a specific player"""
    # Sanitize player name
    player_name = player_name.strip()
    if not player_name or len(player_name) > 100:
        return jsonify({'error': 'Invalid player name'}), 400
    
    stats = advanced_calc.calculate_player_advanced_stats(player_name)
    if not stats:
        return jsonify({'error': 'Player not found'}), 404
    return jsonify(stats)

@app.route('/api/advanced/game/<int:game_id>')
def api_game_advanced(game_id):
    """Get advanced statistics for a specific game"""
    stats = advanced_calc.calculate_game_advanced_stats(game_id)
    if not stats:
        return jsonify({'error': 'Game not found'}), 404
    return jsonify(stats)

@app.route('/api/advanced/patterns')
def api_patterns():
    """Get win/loss patterns and conditions"""
    return jsonify(get_patterns())

@app.route('/api/advanced/volatility')
def api_volatility():
    """Get volatility and consistency metrics"""
    return jsonify(get_volatility())

@app.route('/api/advanced/insights')
def api_auto_insights():
    """Get auto-generated insights"""
    return jsonify({'insights': get_auto_insights()})

@app.route('/api/advanced/all')
def api_all_advanced():
    """Get all advanced statistics in one call"""
    return jsonify({
        'team': get_team_advanced(),
        'patterns': get_patterns(),
        'volatility': get_volatility(),
        'insights': get_auto_insights()
    })

# ==============================================================================
# AI ANALYSIS HELPER FUNCTIONS
# ==============================================================================

def get_stats_context():
    """Generate comprehensive stats context for AI analysis"""
    try:
        games = sorted(stats_data['games'], key=lambda x: x['gameId'])
        season_stats = stats_data['season_team_stats']
        
        # Validate required data
        if not season_stats:
            logger.warning("Missing season stats in get_stats_context")
            return "No season statistics available"
        
        # Calculate win percentage safely
        total_games = season_stats.get('win', 0) + season_stats.get('loss', 0)
        win_pct = (season_stats.get('win', 0) / total_games * 100) if total_games > 0 else 0
        
        context = f"""
Valley Catholic Varsity Basketball - 2025-2026 Season Stats

TEAM RECORD: {season_stats.get('win', 0)}-{season_stats.get('loss', 0)}
Win Percentage: {win_pct:.1f}%

TEAM SEASON AVERAGES:
- Points Per Game: {season_stats.get('ppg', 0):.1f}
- Rebounds Per Game: {season_stats.get('rpg', 0):.1f} (ORB: {season_stats.get('oreb_pg', 0):.1f}, DRB: {season_stats.get('dreb_pg', 0):.1f})
- Assists Per Game: {season_stats.get('apg', 0):.1f}
- Turnovers Per Game: {season_stats.get('to_pg', 0):.1f}
- Steals Per Game: {season_stats.get('stl_pg', 0):.1f}
- Blocks Per Game: {season_stats.get('blk_pg', 0):.1f}
- Fouls Per Game: {season_stats.get('fouls_pg', 0):.1f}
- Field Goal %: {season_stats.get('fg_pct', 0):.1f}%
- Three Point %: {season_stats.get('fg3_pct', 0):.1f}%
- Free Throw %: {season_stats.get('ft_pct', 0):.1f}%

GAME-BY-GAME RESULTS ({len(games)} games):
"""
        
        for game in games:
            try:
                team_stats = game.get('team_stats', {})
                fg_pct = (team_stats.get('fg', 0)/team_stats.get('fga', 1)*100) if team_stats.get('fga', 0) > 0 else 0
                fg3_pct = (team_stats.get('fg3', 0)/team_stats.get('fg3a', 1)*100) if team_stats.get('fg3a', 0) > 0 else 0
                
                # Get top scorers safely
                player_stats = game.get('player_stats', [])
                top_scorers = []
                if player_stats:
                    filtered_players = [p for p in player_stats if p.get('name') not in EXCLUDED_PLAYERS and 'pts' in p]
                    sorted_players = sorted(filtered_players, key=lambda x: x.get('pts', 0), reverse=True)[:3]
                    top_scorers = [f"{p.get('name', 'Unknown')} {p.get('pts', 0)}pts" for p in sorted_players]
                
                context += f"""
Game {game.get('gameId', 'N/A')} - {game.get('date', 'N/A')} vs {game.get('opponent', 'Unknown')} ({game.get('location', 'home')}): {game.get('result', '?')} {game.get('vc_score', 0)}-{game.get('opp_score', 0)}
  Team Stats: {team_stats.get('fg', 0)}/{team_stats.get('fga', 0)} FG ({fg_pct:.1f}%), {team_stats.get('fg3', 0)}/{team_stats.get('fg3a', 0)} 3P ({fg3_pct:.1f}%), {team_stats.get('ft', 0)}/{team_stats.get('fta', 0)} FT ({ft_pct:.1f}%), {team_stats.get('reb', 0)} REB ({team_stats.get('oreb', 0)}+{team_stats.get('dreb', 0)}), {team_stats.get('asst', 0)} AST, {team_stats.get('to', 0)} TO, {team_stats.get('stl', 0)} STL, {team_stats.get('blk', 0)} BLK, {team_stats.get('fouls', 0)} PF
  Top Scorers: {', '.join(top_scorers) if top_scorers else 'No scorers data'}"""
            except Exception as e:
                logger.warning(f"Error processing game {game.get('gameId', 'unknown')}: {e}")
                continue
        
        context += "\n\nPLAYER SEASON STATISTICS (sorted by PPG):\n"
        try:
            player_stats_items = stats_data.get('season_player_stats', {}).items()
            for player_name, stats in sorted(player_stats_items, 
                                             key=lambda x: x[1].get('ppg', 0), reverse=True):
                if player_name in EXCLUDED_PLAYERS or not isinstance(stats, dict):
                    continue
                # Calculate TPG if missing
                tpg = stats.get('to_pg', stats.get('to', 0) / max(stats.get('games', 1), 1))
                context += f"""
{player_name}: {stats.get('games', 0)} GP, {stats.get('ppg', 0):.1f} PPG, {stats.get('rpg', 0):.1f} RPG, {stats.get('apg', 0):.1f} APG, {tpg:.1f} TPG, {stats.get('stl_pg', 0):.1f} SPG, {stats.get('blk_pg', 0):.1f} BPG
  Shooting: {stats.get('fg_pct', 0):.1f}% FG, {stats.get('fg3_pct', 0):.1f}% 3P, {stats.get('ft_pct', 0):.1f}% FT
  Total Season Stats: {stats.get('pts', 0)} PTS, {stats.get('reb', 0)} REB ({stats.get('oreb', 0)}+{stats.get('dreb', 0)}), {stats.get('asst', 0)} AST, {stats.get('to', 0)} TO, {stats.get('stl', 0)} STL, {stats.get('blk', 0)} BLK, {stats.get('fouls', 0)} PF, +/- {stats.get('plus_minus', 0)}"""
        except Exception as e:
            logger.warning(f"Error processing player season stats: {e}")
            context += "\nError loading player statistics"
        
        # Add player game logs for ALL players to enable specific game-by-game queries
        context += "\n\nCOMPLETE PLAYER GAME-BY-GAME LOGS:\n"
        try:
            player_game_logs = stats_data.get('player_game_logs', {})
            for player_name in sorted(player_game_logs.keys()):
                if player_name in EXCLUDED_PLAYERS:
                    continue
                    
                game_logs = sorted(player_game_logs[player_name], key=lambda x: x.get('gameId', 0))
                context += f"\n{player_name} - All Games:\n"
                for log in game_logs:
                    log_stats = log.get('stats', {})
                    context += f"  Game {log.get('gameId', 'N/A')} vs {log.get('opponent', 'Unknown')} ({log.get('date', 'N/A')}): "
                    context += f"{log_stats.get('pts', 0)} PTS, {log_stats.get('oreb', 0)+log_stats.get('dreb', 0)} REB, {log_stats.get('asst', 0)} AST, "
                    context += f"{log_stats.get('to', 0)} TO, {log_stats.get('stl', 0)} STL, {log_stats.get('blk', 0)} BLK, {log_stats.get('fouls', 0)} PF, "
                    context += f"{log_stats.get('fg_made', 0)}-{log_stats.get('fg_att', 0)} FG, {log_stats.get('fg3_made', 0)}-{log_stats.get('fg3_att', 0)} 3P, "
                    context += f"{log_stats.get('ft_made', 0)}-{log_stats.get('ft_att', 0)} FT\n"
        except Exception as e:
            logger.warning(f"Error processing player game logs: {e}")
            context += "\nError loading player trends"
        
        return context
    
    except Exception as e:
        logger.error(f"Error in get_stats_context: {e}")
        return "Error loading comprehensive stats context"

def call_openai_api(system_prompt, user_message, max_tokens=1500, temperature=0.7, model="gpt-4o-mini"):
    """Make API call to OpenAI using requests library"""
    try:
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        response = requests.post(OPENAI_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return data['choices'][0]['message']['content']
    
    except requests.exceptions.Timeout:
        logger.error("OpenAI API timeout")
        raise Exception("AI service timeout - please try again")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            logger.error("OpenAI API rate limit exceeded")
            raise Exception("AI service rate limit - please wait a moment")
        elif e.response.status_code == 401:
            logger.error("OpenAI API authentication failed")
            raise Exception("AI service authentication error")
        else:
            logger.error(f"OpenAI API HTTP error: {e}")
            raise Exception("AI service error - please try again")
    except requests.exceptions.RequestException as e:
        logger.error(f"OpenAI API request failed: {e}")
        raise Exception("AI service connection error")
    except (KeyError, IndexError) as e:
        logger.error(f"OpenAI API response format error: {e}")
        raise Exception("AI service response error")
    except Exception as e:
        logger.error(f"Unexpected OpenAI API error: {e}")
        raise Exception("AI service error")

@app.route('/api/ai/analyze', methods=['POST'])
def ai_analyze():
    """General AI analysis endpoint"""
    try:
        if not request.json:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        data = request.json
        query = data.get('query', '').strip()
        analysis_type = data.get('type', 'general').strip().lower()
        
        # Input validation
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        
        if len(query) > 1000:  # Prevent extremely long queries
            return jsonify({'error': 'Query too long (max 1000 characters)'}), 400
            
        # Validate analysis type
        valid_types = {'general', 'player', 'team', 'game', 'trends', 'coaching'}
        if analysis_type not in valid_types:
            analysis_type = 'general'
        
        if not OPENAI_API_KEY:
            return jsonify({'error': 'OpenAI API key not configured'}), 500
        
        stats_context = get_stats_context()
        
        # Build system prompt based on analysis type
        system_prompts = {
            'general': f"""You are a diagnostic basketball analyst. Your task is to translate raw box score data into cause-effect insights.

Identify:
- MEASURABLE GAPS vs season averages or internal benchmarks
- ROOT CAUSES expressed only through measurable conditions
- ACTIONABLE TACTICAL ADJUSTMENTS limited to rotations, usage, or lineup logic

Do NOT:
- Speculate beyond data
- Offer practice or skill drills
- Use narrative filler

BANNED WORDS: likely, may, might, suggests, chemistry, refined, momentum, run, collapse

TEAM DATA: {stats_context}

REQUIRED OUTPUT STRUCTURE:
A. KEY DEVIATIONS (3–5 bullets)
B. ROOT CAUSE CONDITIONS (linked numerically to A)
C. TACTICAL ADJUSTMENTS (ranked by estimated impact)""",
            'player': f"""Perform a diagnostic evaluation of a single player using box score data only.

Identify:
- PERFORMANCE DELTA vs season baseline
- EFFICIENCY vs usage relationship
- ROLE ALIGNMENT (is output consistent with how player is used)

Do NOT infer effort, confidence, or intent.

TEAM DATA: {stats_context}

REQUIRED OUTPUT STRUCTURE:
- PERFORMANCE GAP
- EFFICIENCY PROFILE
- USAGE VS OUTPUT
- ROLE FIT CONCLUSION""",
            'team': f"""Analyze team-level tactics using season and game box score data.

Identify:
- STAT-DRIVEN WIN / LOSS CONDITIONS
- OFFENSIVE DEPENDENCIES (efficiency vs volume)
- DEFENSIVE FAILURE SIGNALS using available metrics only
- TOP 3 TACTICAL ADJUSTMENTS ranked by impact

DO NOT reference individual opponent players or positions.

TEAM DATA: {stats_context}

REQUIRED OUTPUT STRUCTURE:
1. PRIMARY WIN CONDITION
2. SECONDARY SUPPORT CONDITION
3. FAILURE THRESHOLDS
4. TACTICAL FIXES (ranked)""",
            'trends': f"""Identify patterns across games using only numeric trends.

Analyze:
- VOLATILITY (players or stats with highest variance)
- DIRECTIONAL SHIFTS (efficiency, usage, scoring concentration)
- RISK SIGNALS (conditions correlated with losses or narrow margins)

NO play-by-play assumptions.

TEAM DATA: {stats_context}

REQUIRED OUTPUT STRUCTURE:
- MOST VOLATILE VARIABLES
- STABLE VARIABLES
- LOSS-ASSOCIATED CONDITIONS
- PREDICTIVE RISK FLAGS""",
            'coaching': f"""Evaluate game management strictly from box score outcomes.

Analyze:
- ROTATION IMPACT using +/- only
- LINEUP DEPENDENCE (scoring concentration)
- GAME CONTROL METRICS (turnovers, fouls, rebounds)

Do NOT suggest practices or skill development.

TEAM DATA: {stats_context}

REQUIRED OUTPUT STRUCTURE:
- ROTATION EFFECTIVENESS
- DEPTH RELIANCE
- MANAGEMENT FAILURE POINTS"""
        }
        
        system_prompt = system_prompts.get(analysis_type, system_prompts['general'])
        
        analysis = call_openai_api(system_prompt, query, max_tokens=1500, model="gpt-4o-mini")
        
        return jsonify({
            'analysis': analysis,
            'type': analysis_type,
            'query': query
        })
    
    except Exception as e:
        return jsonify({'error': f'AI analysis failed: {str(e)}'}), 500

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    """Chatbot endpoint with conversation history support"""
    try:
        if not request.json:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        data = request.json
        message = data.get('message', '').strip()
        history = data.get('history', [])
        
        # Input validation
        if not message:
            return jsonify({'error': 'No message provided'}), 400
            
        if len(message) > 1000:  # Prevent extremely long messages
            return jsonify({'error': 'Message too long (max 1000 characters)'}), 400
        
        # Validate history is a list and limit its size
        if not isinstance(history, list):
            history = []
        history = history[-20:]  # Keep only last 20 messages to prevent context overflow
        
        # Sanitize history messages
        cleaned_history = []
        for msg in history:
            if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                if msg['role'] in ['user', 'assistant'] and len(str(msg['content'])) <= 2000:
                    cleaned_history.append({
                        'role': msg['role'],
                        'content': str(msg['content']).strip()
                    })
        
        if not OPENAI_API_KEY:
            return jsonify({'error': 'OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.'}), 500
        
        # Get comprehensive stats context
        stats_context = get_stats_context()
        
        # Build system prompt with stats context
        system_prompt = f"""You are an expert basketball statistics analyst. You must use ONLY the provided stats data to answer questions.

CRITICAL INSTRUCTIONS:
- You MUST reference the exact numbers from the data provided below
- Never make up or estimate statistics
- If asked about a specific player's stats, find that player in the data and quote their exact numbers
- For player stats, look in the "PLAYER SEASON STATISTICS" section
- Always cite the specific stat you're referencing (e.g., "Cooper Bonnett has 24 TO total turnovers")

TEAM STATS DATA:
{stats_context}

Answer the user's question using ONLY the stats shown above. Be direct and specific."""
        
        # Prepare messages for API call
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent conversation history (last 10 messages for context)
        for msg in history[-10:]:
            messages.append({
                "role": msg.get('role', 'user'),
                "content": msg.get('content', '')
            })
        
        # Make API call with conversation context
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4o-mini",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        response = requests.post(OPENAI_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        response_data = response.json()
        ai_response = response_data['choices'][0]['message']['content']
        
        return jsonify({
            'response': ai_response,
            'message': message
        })
    
    except requests.exceptions.Timeout:
        logger.error("OpenAI API timeout")
        return jsonify({'error': 'AI service timeout - please try again'}), 504
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            logger.error("OpenAI API rate limit exceeded")
            return jsonify({'error': 'AI service rate limit - please wait a moment'}), 429
        elif e.response.status_code == 401:
            logger.error("OpenAI API authentication failed")
            return jsonify({'error': 'AI service authentication error - check API key'}), 401
        else:
            logger.error(f"OpenAI API HTTP error: {e}")
            return jsonify({'error': 'AI service error - please try again'}), 500
    except requests.exceptions.RequestException as e:
        logger.error(f"OpenAI API request failed: {e}")
        return jsonify({'error': 'AI service connection error'}), 503
    except (KeyError, IndexError) as e:
        logger.error(f"OpenAI API response format error: {e}")
        return jsonify({'error': 'AI service response error'}), 500
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}")
        return jsonify({'error': f'Chat failed: {str(e)}'}), 500

@app.route('/api/ai/player-insights/<player_name>', methods=['GET'])
def ai_player_insights(player_name):
    """Get AI-generated insights for a specific player"""
    try:
        # Sanitize player name
        player_name = player_name.strip()
        if not player_name or len(player_name) > 100:
            return jsonify({'error': 'Invalid player name'}), 400
        
        if player_name not in stats_data['season_player_stats']:
            return jsonify({'error': 'Player not found'}), 404
        
        if not OPENAI_API_KEY:
            return jsonify({'error': 'OpenAI API key not configured'}), 500
        
        if player_name in EXCLUDED_PLAYERS:
            return jsonify({'error': 'Analysis not available for this player'}), 404
        
        player_stats = stats_data['season_player_stats'][player_name]
        
        # Get lightweight context - just team averages and top players for comparison
        season_stats = stats_data['season_team_stats']
        top_players_context = "\n\nTEAM LEADING SCORERS FOR COMPARISON:\n"
        for pname, pstats in sorted(stats_data['season_player_stats'].items(), 
                                    key=lambda x: x[1]['ppg'], reverse=True)[:5]:
            if pname not in EXCLUDED_PLAYERS:
                top_players_context += f"{pname}: {pstats['ppg']:.1f} PPG, {pstats['rpg']:.1f} RPG, {pstats['apg']:.1f} APG, {pstats['fg_pct']:.1f}% FG\n"
        
        # Get player game logs for trend analysis (last 5 games only)
        game_logs_text = ""
        if player_name in stats_data.get('player_game_logs', {}):
            game_logs = sorted(stats_data['player_game_logs'][player_name], key=lambda x: x['gameId'])[-5:]
            game_logs_text = f"\n\nLAST {len(game_logs)} GAMES:\n"
            for log in game_logs:
                fg_pct = (log['stats']['fg_made']/log['stats']['fg_att']*100) if log['stats']['fg_att'] > 0 else 0
                game_logs_text += f"G{log['gameId']} vs {log['opponent']}: {log['stats']['pts']}pts, {log['stats']['oreb']+log['stats']['dreb']}reb, {log['stats']['asst']}ast, {log['stats']['fg_made']}/{log['stats']['fg_att']}FG ({fg_pct:.1f}%)\n"
        
        prompt = f"""Analyze {player_name}

SEASON STATS ({player_stats['games']} games):
{player_stats['ppg']:.1f} PPG | {player_stats['rpg']:.1f} RPG | {player_stats['apg']:.1f} APG
Shooting: {player_stats['fg_pct']:.1f}% FG | {player_stats['fg3_pct']:.1f}% 3PT | {player_stats['ft_pct']:.1f}% FT{game_logs_text}{top_players_context}
TEAM RECORD: {season_stats['win']}-{season_stats['loss']}

REQUIRED ANALYSIS:
1. SCORING OUTPUT - Is {player_name} meeting expectations? Compare to team needs
2. EFFICIENCY - Are shooting percentages good/bad? Which shots are working?
3. CONSISTENCY - Look at recent games - stable or volatile performance?
4. ROLE & CONTRIBUTION - What does this player do well? Where can they improve?
5. TREND - Based on recent games, improving or declining?

Be specific and data-driven. Reference actual numbers from the stats above."""
        
        system_prompt = "You are analyzing an individual player's performance. Focus on their stats, recent trends, and how they compare to teammates. Be honest about strengths and weaknesses using the data provided."
        
        insights = call_openai_api(system_prompt, prompt, max_tokens=800, model="gpt-4o-mini")
        
        return jsonify({
            'player': player_name,
            'insights': insights
        })
    
    except Exception as e:
        logger.error(f"Player insights error for {player_name}: {str(e)}")
        return jsonify({'error': f'Failed to generate insights: {str(e)}'}), 500

@app.route('/api/ai/game-analysis/<int:game_id>', methods=['GET'])
def ai_game_analysis(game_id):
    """Get AI analysis of a specific game"""
    try:
        game = None
        for g in stats_data['games']:
            if g['gameId'] == game_id:
                game = g
                break
        
        if not game:
            return jsonify({'error': 'Game not found'}), 404
        
        if not OPENAI_API_KEY:
            return jsonify({'error': 'OpenAI API key not configured'}), 500
        
        # Build lightweight context for game analysis (not full stats context)
        season_stats = stats_data['season_team_stats']
        games = sorted(stats_data['games'], key=lambda x: x['gameId'])
        
        # Get all games summary for comparison
        games_summary = f"\n\nALL GAMES THIS SEASON ({season_stats['win']}-{season_stats['loss']}):\n"
        for g in games:
            games_summary += f"G{g['gameId']} vs {g['opponent']}: {g['result']} {g['vc_score']}-{g['opp_score']}\n"
        
        # Build detailed game stats
        team_stats = game['team_stats']
        fg_pct_game = (team_stats['fg']/team_stats['fga']*100) if team_stats['fga'] > 0 else 0
        fg3_pct_game = (team_stats['fg3']/team_stats['fg3a']*100) if team_stats['fg3a'] > 0 else 0
        ft_pct_game = (team_stats['ft']/team_stats['fta']*100) if team_stats['fta'] > 0 else 0
        
        # Player performances in this game with season averages
        player_performances = "\n\nPLAYER PERFORMANCES (with season averages):\n"
        if 'player_stats' in game:
            sorted_players = sorted([p for p in game['player_stats'] if p['name'] not in EXCLUDED_PLAYERS], 
                                   key=lambda x: x['pts'], reverse=True)
            for p in sorted_players:
                player_season = stats_data['season_player_stats'].get(p['name'], {})
                season_ppg = player_season.get('ppg', 0)
                player_performances += f"{p['name']}: {p['pts']}pts (avg {season_ppg:.1f}), {p.get('reb', 0)}reb, {p.get('asst', 0)}ast, {p.get('fg_made', 0)}/{p.get('fg_att', 0)}FG, {p.get('fg3_made', 0)}/{p.get('fg3_att', 0)}3P, {p.get('to', 0)}TO\n"
        
        prompt = f"""VC vs {game['opponent']} | {game['date']} ({game.get('location', 'home')})
Final Score: {game['vc_score']}-{game['opp_score']} ({game['result']})

GAME STATS:
FG: {team_stats['fg']}/{team_stats['fga']} ({fg_pct_game:.1f}%) [Season Avg: {season_stats['fg_pct']:.1f}%]
3PT: {team_stats['fg3']}/{team_stats['fg3a']} ({fg3_pct_game:.1f}%) [Season Avg: {season_stats['fg3_pct']:.1f}%]
FT: {team_stats['ft']}/{team_stats['fta']} ({ft_pct_game:.1f}%) [Season Avg: {season_stats['ft_pct']:.1f}%]
REB: {team_stats['reb']} [Season Avg: {season_stats['rpg']:.1f}]
AST: {team_stats['asst']} [Season Avg: {season_stats['apg']:.1f}]
TO: {team_stats['to']} [Season Avg: {season_stats.get('to_pg', 0):.1f}]
STL: {team_stats.get('stl', 0)} [Season Avg: {season_stats.get('stl_pg', 0):.1f}]
BLK: {team_stats.get('blk', 0)} [Season Avg: {season_stats.get('blk_pg', 0):.1f}]{player_performances}{games_summary}

REQUIRED OUTPUT:
- SHOOTING DEVIATION vs season (by shot type - explain the difference)
- POSSESSION CONTROL (TO, REB compared to season avg - better or worse?)
- SCORING DISTRIBUTION (was scoring balanced or did we rely on 1-2 players?)
- KEY PLAYER PERFORMANCES (who exceeded their average? who underperformed?)
- PRIMARY WIN/LOSS DRIVER (what single stat or factor most explains the outcome?)
- COMPARISON TO OTHER GAMES (reference similar results or opponents)"""
        
        system_prompt = """You are analyzing a single basketball game. Focus on what made this game different from the team's season averages. Compare player performances to their typical output. Be specific about which numbers deviated from normal and what that meant for the outcome."""
        
        analysis = call_openai_api(system_prompt, prompt, max_tokens=1000, model="gpt-4o-mini")
        
        return jsonify({
            'game': f"{game['opponent']} ({game['date']})",
            'analysis': analysis
        })
    
    except Exception as e:
        logger.error(f"Game analysis error for game {game_id}: {str(e)}")
        return jsonify({'error': f'Failed to analyze game: {str(e)}'}), 500

@app.route('/api/ai/team-summary', methods=['GET'])
def ai_team_summary():
    """Get AI-generated team summary and recommendations - cached for consistency"""
    TEAM_SUMMARY_CACHE = 'team_summary.json'
    
    try:
        # Check if summary is cached
        if os.path.exists(TEAM_SUMMARY_CACHE):
            with open(TEAM_SUMMARY_CACHE) as f:
                return jsonify(json.load(f))
        
        if not OPENAI_API_KEY:
            return jsonify({'error': 'OpenAI API key not configured'}), 500
        
        stats_context = get_stats_context()
        
        prompt = """Diagnose this season's performance using only box score data. Your analysis must be mechanically provable—no speculation, no chemistry claims, no "momentum" or "confidence" inferences.

CORE PRINCIPLES:
• Every stat must answer: "What does this enable us to do?" or "What breaks if this drops?"
• All failure conditions must cite actual game records (e.g., "1-3 when TO > 15")
• No words like: likely, suggests, chemistry, mental, resilience, effort, momentum, psychological
• If you can't prove it from the numbers, don't say it

WHAT TO ANALYZE (focus on what's most revealing in the data):
1. **Primary Win Condition** - What stat pattern predicts wins? Prove it with splits
2. **Critical Thresholds** - What metric values separate wins from losses?
3. **Dependency Structure** - Does success require {X} AND {Y}, or can team win through either?
4. **Failure Modes** - What numeric breakdown causes losses? Be specific with thresholds
5. **Resource Tradeoffs** - What does high {X} cost us in terms of {Y}?
6. **Actionable Levers** - What could realistically change and by how much?

STYLE REQUIREMENTS:
• Write in direct cause-effect statements
• Use "IF/THEN/BECAUSE" for failure analysis
• Compare to league/historical benchmarks when relevant (you have them)
• Flag insufficient data explicitly ("Cannot determine X because we lack Y")
• Prioritize insights by win impact (don't waste words on 3rd-order effects)

ABSOLUTE PROHIBITIONS:
✗ Don't infer defensive schemes (only STL/BLK are measurable)
✗ Don't claim "improvement" without early vs late season splits
✗ Don't use adjectives without numbers ("strong" → "top 20%")
✗ Don't mention pace/tempo unless you calculate possessions
✗ Don't speculate on player psychology, effort, or chemistry

STRUCTURE: Use whatever format communicates the diagnosis most clearly. Bullets, paragraphs, tables—whatever works. Just make it scannable and fact-dense."""
        
        system_prompt = f"""You are a performance diagnostician analyzing basketball data. Focus on causal mechanisms: what enables wins, what causes losses, what could realistically change.

Write like you're briefing a coach who needs actionable intelligence, not surface-level observations. Be direct, specific, and prove every claim with numbers.

TEAM DATA: {stats_context}"""
        
        summary = call_openai_api(system_prompt, prompt, max_tokens=2000, temperature=0, model="gpt-4o-mini")
        
        # Cache the result
        result = {'summary': summary}
        with open(TEAM_SUMMARY_CACHE, 'w') as f:
            json.dump(result, f)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': f'Failed to generate summary: {str(e)}'}), 500

@app.route('/api/ai/team-summary', methods=['DELETE'])
def clear_team_summary():
    """Clear team summary cache"""
    TEAM_SUMMARY_CACHE = 'team_summary.json'
    try:
        if os.path.exists(TEAM_SUMMARY_CACHE):
            os.remove(TEAM_SUMMARY_CACHE)
        return jsonify({'message': 'Team summary cache cleared'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/season-analysis', methods=['GET'])
def get_season_analysis():
    """Get cached season analysis or generate it"""
    try:
        # Always return cached version if it exists unless force=true
        force_regenerate = request.args.get('force', 'false').lower() == 'true'
        
        if not force_regenerate and os.path.exists(ANALYSIS_CACHE_FILE):
            logger.info("Returning cached season analysis")
            with open(ANALYSIS_CACHE_FILE) as f:
                return jsonify(json.load(f))
        
        # Warn about long generation time
        if force_regenerate:
            logger.warning("Force regenerating season analysis - this may take 5-10 minutes")
        
        # Generate analysis if not cached
        if not OPENAI_API_KEY:
            return jsonify({'error': 'OpenAI API key not configured'}), 500
        
        games = sorted(stats_data['games'], key=lambda x: x['gameId'])
        season_stats = stats_data['season_team_stats']
        
        # Limit number of games to analyze to prevent timeout
        max_games_to_analyze = int(request.args.get('max_games', len(games)))
        games_to_analyze = games[:max_games_to_analyze]
        
        logger.info(f"Generating analysis for {len(games_to_analyze)} games")
        
        # Generate per-game analysis
        per_game_analysis = []
        
        # First, calculate player season averages for comparison
        player_season_stats = stats_data['season_player_stats']
        
        for i, game in enumerate(games_to_analyze, 1):
            logger.info(f"Analyzing game {i}/{len(games_to_analyze)}: {game.get('opponent', 'Unknown')}")
            team_stats = game['team_stats']
            fg_pct = (team_stats['fg']/team_stats['fga']*100) if team_stats['fga'] > 0 else 0
            
            # Get all player performances (excluding specified players)
            player_stats_game = [p for p in game['player_stats'] if p['name'] not in EXCLUDED_PLAYERS]
            player_stats_game = sorted(player_stats_game, key=lambda x: x['pts'], reverse=True)
            
            # All player performances with performance indicators
            player_performances = []
            for j, player in enumerate(player_stats_game):
                fg_pct_p = float(player['fg_pct'].rstrip('%')) if '%' in player['fg_pct'] else 0
                fg3_pct_p = float(player['fg3_pct'].rstrip('%')) if '%' in player['fg3_pct'] else 0
                ft_pct_p = float(player['ft_pct'].rstrip('%')) if '%' in player['ft_pct'] else 0
                
                season_avg = player_season_stats.get(player['name'], {})
                season_ppg = season_avg.get('ppg', 0)
                
                perf_vs_avg = player['pts'] - season_ppg
                
                # Performance indicator: ↑ above, → at, ↓ below average
                if perf_vs_avg > 1:
                    indicator = "↑"
                    status = "Above Avg"
                elif perf_vs_avg < -1:
                    indicator = "↓"
                    status = "Below Avg"
                else:
                    indicator = "→"
                    status = "At Avg"
                
                player_performances.append({
                    'rank': j+1,
                    'name': player['name'],
                    'pts': player['pts'],
                    'fg': f"{player['fg_made']}/{player['fg_att']}",
                    'fg_pct': fg_pct_p,
                    'fg3': f"{player['fg3_made']}/{player['fg3_att']}",
                    'fg3_pct': fg3_pct_p,
                    'ft': f"{player['ft_made']}/{player['ft_att']}",
                    'ft_pct': ft_pct_p,
                    'reb': player.get('dreb', 0) + player.get('oreb', 0),
                    'asst': player['asst'],
                    'season_ppg': season_ppg,
                    'diff': perf_vs_avg,
                    'indicator': indicator,
                    'status': status
                })
            
            # Shooting analysis
            team_2pt_made = team_stats['fg'] - team_stats['fg3']
            team_2pt_att = team_stats['fga'] - team_stats['fg3a']
            team_2pt_pct = (team_2pt_made/team_2pt_att*100) if team_2pt_att > 0 else 0
            team_3pt_pct = (team_stats['fg3']/team_stats['fg3a']*100) if team_stats['fg3a'] > 0 else 0
            team_ft_pct = (team_stats['ft']/team_stats['fta']*100) if team_stats['fta'] > 0 else 0
            
            # Season shooting averages for comparison
            season_2pt_avg = ((season_stats['fg_pct']/100 * season_stats['ppg'] * 0.6) / 1.5)  # Approximation
            season_3pt_avg = season_stats['fg3_pct']
            season_ft_avg = season_stats['ft_pct']
            
            # Build detailed game prompt
            game_prompt = f"""COMPREHENSIVE GAME ANALYSIS:
Game {i}: Valley Catholic vs {game['opponent']} ({game['date']})
RESULT: VC {game['vc_score']}-{game['opp_score']} ({game['result'].upper()})

TEAM SHOOTING EFFICIENCY:
- 2-Point: {team_2pt_made}/{team_2pt_att} ({team_2pt_pct:.1f}%) vs Season Avg: {season_stats['fg_pct']:.1f}%
- 3-Point: {team_stats['fg3']}/{team_stats['fg3a']} ({team_3pt_pct:.1f}%) vs Season Avg: {season_stats['fg3_pct']:.1f}%
- Free Throw: {team_stats['ft']}/{team_stats['fta']} ({team_ft_pct:.1f}%) vs Season Avg: {season_stats['ft_pct']:.1f}%
- Overall FG%: {fg_pct:.1f}%

TEAM STATS:
- Rebounds: {team_stats['reb']} | Assists: {team_stats['asst']} | Turnovers: {team_stats['to']} | Steals: {team_stats['stl']} | Blocks: {team_stats['blk']}

PLAYER PERFORMANCES (ranked by points):
"""
            for perf in player_performances:
                game_prompt += f"{perf['indicator']} {perf['rank']}. {perf['name']}: {perf['pts']}pts ({perf['fg_pct']:.0f}% FG, {perf['fg3_pct']:.0f}% 3P, {perf['ft_pct']:.0f}% FT) | {perf['reb']}reb {perf['asst']}ast | Season Avg: {perf['season_ppg']:.1f}ppg ({perf['diff']:+.1f}pts vs avg)\n"
            
            game_prompt += f"""
REQUIRED OUTPUT:
- PRIMARY GAME DRIVER
- SECONDARY DRIVER
- RISK EXPOSED"""
            
            system_prompt = "Generate compact, UI-safe game diagnostics using measurable deltas only."
            
            try:
                logger.info(f"Calling OpenAI API for game {i}")
                analysis_text = call_openai_api(system_prompt, game_prompt, max_tokens=800, model="gpt-4o-mini")
                logger.info(f"Successfully analyzed game {i}")
                per_game_analysis.append({
                    'game': i,
                    'opponent': game['opponent'],
                    'date': game['date'],
                    'score': f"{game['vc_score']}-{game['opp_score']}",
                    'result': game['result'],
                    'shooting': {
                        '2pt': f"{team_2pt_made}/{team_2pt_att} ({team_2pt_pct:.1f}%)",
                        '3pt': f"{team_stats['fg3']}/{team_stats['fg3a']} ({team_3pt_pct:.1f}%)",
                        'ft': f"{team_stats['ft']}/{team_stats['fta']} ({team_ft_pct:.1f}%)"
                    },
                    'player_performances': player_performances,
                    'analysis': analysis_text
                })
            except Exception as e:
                logger.error(f"Failed to analyze game {i}: {e}")
                per_game_analysis.append({
                    'game': i,
                    'opponent': game['opponent'],
                    'date': game['date'],
                    'score': f"{game['vc_score']}-{game['opp_score']}",
                    'result': game['result'],
                    'analysis': f'Analysis pending... (Error: {str(e)})'
                })
        
        # Generate season summary
        season_prompt = f"""Season Summary Analysis:
Record: {season_stats['win']}-{season_stats['loss']} ({season_stats['win']/(season_stats['win']+season_stats['loss'])*100:.1f}%)
PPG: {season_stats['ppg']:.1f}, RPG: {season_stats['rpg']:.1f}, APG: {season_stats['apg']:.1f}
FG%: {season_stats['fg_pct']:.1f}%, 3P%: {season_stats['fg3_pct']:.1f}%, FT%: {season_stats['ft_pct']:.1f}%

Analyze comprehensively:
1. Overall season performance assessment
2. Team strengths that have been consistent
3. Main weaknesses and areas lacking
4. How the team has evolved/changed through the season
5. What needs to change for improvement
6. Season trajectory and momentum"""
        
        system_prompt = "You are an expert basketball coach providing detailed season analysis. Be thorough and specific."
        season_summary = call_openai_api(system_prompt, season_prompt, max_tokens=2000, model="gpt-4o-mini")
        
        # Cache the analysis
        analysis_data = {
            'generated_at': datetime.now().isoformat(),
            'season_summary': season_summary,
            'per_game_analysis': per_game_analysis
        }
        
        with open(ANALYSIS_CACHE_FILE, 'w') as f:
            json.dump(analysis_data, f, indent=2)
        
        return jsonify(analysis_data)
    
    except Exception as e:
        return jsonify({'error': f'Failed to generate analysis: {str(e)}'}), 500

@app.route('/api/season-analysis', methods=['DELETE'])
def clear_analysis():
    """Clear cached analysis to regenerate"""
    try:
        if os.path.exists(ANALYSIS_CACHE_FILE):
            os.remove(ANALYSIS_CACHE_FILE)
        return jsonify({'message': 'Analysis cache cleared'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==============================================================================
# PLAYER AI ANALYSIS ENDPOINTS
# ==============================================================================

def load_player_analysis_cache():
    """Load cached player analysis from file"""
    if os.path.exists(PLAYER_ANALYSIS_CACHE_FILE):
        try:
            with open(PLAYER_ANALYSIS_CACHE_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in cache file: {PLAYER_ANALYSIS_CACHE_FILE}")
            return {}
        except Exception as e:
            logger.error(f"Error loading player analysis cache: {e}")
            return {}
    return {}

def save_player_analysis_cache(cache_data):
    """Save player analysis cache to file"""
    try:
        with open(PLAYER_ANALYSIS_CACHE_FILE, 'w') as f:
            json.dump(cache_data, f, indent=2)
    except Exception as e:
        print(f"Error saving player analysis cache: {e}")

@app.route('/api/ai/player-analysis/<player_name>', methods=['GET'])
def get_player_analysis(player_name):
    """Get comprehensive AI analysis for a specific player with caching"""
    try:
        # Sanitize player name
        player_name = player_name.strip()
        if not player_name or len(player_name) > 100:
            return jsonify({'error': 'Invalid player name'}), 400
        
        if player_name not in stats_data['season_player_stats']:
            return jsonify({'error': 'Player not found'}), 404
        
        if not OPENAI_API_KEY:
            return jsonify({'error': 'OpenAI API key not configured'}), 500
        
        # Check if force regeneration is requested
        force_regenerate = request.args.get('regenerate', 'false').lower() == 'true'
        
        # Load cache
        cache = load_player_analysis_cache()
        
        # Check if cached analysis exists and is not being regenerated
        if not force_regenerate and player_name in cache:
            cached_data = cache[player_name]
            cached_data['cached'] = True
            return jsonify(cached_data)
        
        # Generate new analysis
        player_stats = stats_data['season_player_stats'][player_name]
        game_logs = stats_data.get('player_game_logs', {}).get(player_name, [])
        
        # Get advanced stats if available
        advanced_stats = advanced_calc.calculate_player_advanced_stats(player_name)
        
        # Build comprehensive player context
        player_context = f"""
PLAYER: {player_name}

SEASON STATISTICS ({player_stats['games']} Games):
- Points Per Game: {player_stats['ppg']:.1f}
- Rebounds Per Game: {player_stats['rpg']:.1f}
- Assists Per Game: {player_stats['apg']:.1f}
- Field Goal %: {player_stats['fg_pct']:.1f}% ({player_stats['fg']}/{player_stats['fga']})
- 3-Point %: {player_stats['fg3_pct']:.1f}% ({player_stats['fg3']}/{player_stats['fg3a']})
- Free Throw %: {player_stats['ft_pct']:.1f}% ({player_stats['ft']}/{player_stats['fta']})
- Steals Per Game: {player_stats.get('stl', 0) / player_stats['games']:.1f}
- Blocks Per Game: {player_stats.get('blk', 0) / player_stats['games']:.1f}
- Turnovers Per Game: {player_stats.get('to', 0) / player_stats['games']:.1f}
"""
        
        if advanced_stats:
            player_context += f"""

ADVANCED METRICS:
- Effective FG%: {advanced_stats['scoring_efficiency']['efg_pct']:.1f}%
- True Shooting %: {advanced_stats['scoring_efficiency']['ts_pct']:.1f}%
- Points Per Shot: {advanced_stats['scoring_efficiency']['pts_per_shot']:.2f}
- Usage Rate Proxy: {advanced_stats['usage_role']['usage_proxy']:.1f}%
- Scoring Share: {advanced_stats['usage_role']['scoring_share']:.1f}%
- Assist/Turnover Ratio: {advanced_stats['ball_handling']['ast_to_ratio']:.2f}
"""
        
        # Add game-by-game performance variance
        if game_logs:
            game_logs_sorted = sorted(game_logs, key=lambda x: x['gameId'])
            # Handle both data structures: direct stats or nested in 'stats' key
            pts_list = []
            fg_pct_list = []
            for g in game_logs_sorted:
                if 'stats' in g:
                    pts_list.append(g['stats']['pts'])
                    fg_att = g['stats'].get('fg_att', 0)
                    if fg_att > 0:
                        fg_pct_list.append(g['stats']['fg_made'] / fg_att * 100)
                    else:
                        fg_pct_list.append(0)
                else:
                    pts_list.append(g.get('pts', 0))
                    fg_att = g.get('fg_att', 0)
                    if fg_att > 0:
                        fg_pct_list.append(g.get('fg_made', 0) / fg_att * 100)
                    else:
                        fg_pct_list.append(0)
            
            if len(pts_list) > 1:
                pts_variance = sum((x - player_stats['ppg'])**2 for x in pts_list) / len(pts_list)
                pts_std = pts_variance ** 0.5
                player_context += f"""

PERFORMANCE CONSISTENCY:
- Point Standard Deviation: {pts_std:.1f} (Variance: {pts_variance:.1f})
- Highest Scoring Game: {max(pts_list)} pts
- Lowest Scoring Game: {min(pts_list)} pts
- Average FG% Range: {min(fg_pct_list):.1f}% to {max(fg_pct_list):.1f}%
"""
            
            # Recent trend (last 3 games)
            if len(game_logs_sorted) >= 3:
                recent_games = game_logs_sorted[-3:]
                recent_avg_pts = sum(g['stats']['pts'] for g in recent_games) / 3
                player_context += f"""

RECENT TREND (Last 3 Games):
- Recent PPG: {recent_avg_pts:.1f} vs Season Avg: {player_stats['ppg']:.1f} ({recent_avg_pts - player_stats['ppg']:+.1f})
"""
        
        # Create analysis prompt
        analysis_prompt = f"""{player_context}

PERFORM COMPREHENSIVE PLAYER ANALYSIS:

1. PERFORMANCE PROFILE
   - Overall season performance assessment
   - Statistical strengths (specific numbers)
   - Key weaknesses and limitations (with data)

2. SCORING ANALYSIS
   - Shot selection efficiency by type (2PT, 3PT, FT)
   - Scoring consistency and reliability
   - Volume vs efficiency balance

3. ROLE & IMPACT
   - Primary role on team (based on usage and stats)
   - Impact on team success (quantitative assessment)
   - Optimal usage patterns

4. CONSISTENCY & TRENDS
   - Game-to-game variance analysis
   - Recent performance trends
   - Reliability factors

5. DEVELOPMENT AREAS
   - Specific statistical improvements needed
   - Skills requiring attention (data-driven)
   - Tactical adjustments for optimization

6. KEY INSIGHTS
   - 3-5 data-driven observations
   - Performance patterns
   - Strategic recommendations

REQUIREMENTS:
- Use specific numbers and percentages
- Compare to season averages where relevant
- Be objective and analytical
- Focus on measurable metrics
- Provide actionable insights"""
        
        system_prompt = """You are an expert basketball analyst providing comprehensive, data-driven player analysis. 
Use specific statistics and metrics to support every observation. Be thorough but concise. 
Focus on measurable performance indicators and tactical insights. Format your response in clear sections with bullet points."""
        
        # Generate analysis
        analysis = call_openai_api(system_prompt, analysis_prompt, max_tokens=2000, temperature=0.7, model="gpt-4o-mini")
        
        # Prepare response
        response_data = {
            'player': player_name,
            'analysis': analysis,
            'generated_at': datetime.now().isoformat(),
            'stats_summary': {
                'games': player_stats['games'],
                'ppg': round(player_stats['ppg'], 1),
                'rpg': round(player_stats['rpg'], 1),
                'apg': round(player_stats['apg'], 1),
                'fg_pct': round(player_stats['fg_pct'], 1),
                'fg3_pct': round(player_stats['fg3_pct'], 1),
                'ft_pct': round(player_stats['ft_pct'], 1)
            },
            'cached': False
        }
        
        # Cache the result
        cache[player_name] = response_data
        save_player_analysis_cache(cache)
        
        return jsonify(response_data)
    
    except Exception as e:
        return jsonify({'error': f'Failed to generate player analysis: {str(e)}'}), 500

@app.route('/api/ai/player-analysis/<player_name>', methods=['DELETE'])
def clear_player_analysis(player_name):
    """Clear cached analysis for a specific player"""
    try:
        # Sanitize player name
        player_name = player_name.strip()
        if not player_name or len(player_name) > 100:
            return jsonify({'error': 'Invalid player name'}), 400
        
        cache = load_player_analysis_cache()
        if player_name in cache:
            del cache[player_name]
            save_player_analysis_cache(cache)
            return jsonify({'message': f'Analysis cache cleared for {player_name}'})
        return jsonify({'message': 'No cached analysis found'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'production') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)
