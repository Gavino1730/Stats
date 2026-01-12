"""
Valley Catholic Basketball Stats - Flask Application
Clean, refactored version with organized routes and services.
"""

from flask import Flask, render_template, jsonify, request
from functools import lru_cache
import json
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

from src.config import Config, EXCLUDED_PLAYERS, MAX_TOKENS
from src.data_manager import get_data_manager
from src.ai_service import get_ai_service, build_stats_context, ANALYSIS_PROMPTS, APIError
from src.advanced_stats import AdvancedStatsCalculator

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__,
            template_folder=os.path.join(Config.PROJECT_ROOT, 'templates'),
            static_folder=os.path.join(Config.PROJECT_ROOT, 'static'))

app.config['JSON_SORT_KEYS'] = False
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000

# Initialize services
data = get_data_manager()
advanced_calc = AdvancedStatsCalculator(data.stats_data)


# =============================================================================
# Middleware
# =============================================================================

@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response


# =============================================================================
# Page Routes
# =============================================================================

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/games')
def games():
    return render_template('games.html')

@app.route('/players')
def players():
    return render_template('players.html')

@app.route('/trends')
def trends():
    return render_template('trends.html')

@app.route('/ai-insights')
def ai_insights():
    return render_template('ai-insights.html')

@app.route('/analysis')
def analysis():
    return render_template('analysis.html')

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'games_loaded': len(data.games),
        'players_loaded': len(data.season_player_stats),
        'openai_configured': get_ai_service().is_configured
    })


# =============================================================================
# Data API Routes
# =============================================================================

@app.route('/api/season-stats')
@lru_cache(maxsize=1)
def api_season_stats():
    return jsonify(data.season_team_stats)


@app.route('/api/games')
def api_games():
    games_list = sorted(data.games, key=lambda x: x['gameId'])
    return jsonify(games_list)


@app.route('/api/game/<int:game_id>')
def api_game(game_id):
    game = data.get_game_by_id(game_id)
    if game:
        return jsonify(game)
    return jsonify({'error': 'Game not found'}), 404


@app.route('/api/players')
def api_players():
    """Get all player stats with enhanced metrics"""
    players = list(data.season_player_stats.values())
    roster_dict = data.get_roster_dict()
    
    enhanced = []
    for player in players:
        p = player.copy()
        games = player.get('games', 1)
        
        # Add roster info
        if player['name'] in roster_dict:
            p['number'] = roster_dict[player['name']].get('number')
            p['grade'] = roster_dict[player['name']].get('grade')
        
        # Add per-game stats
        p['spg'] = player.get('stl', 0) / games
        p['bpg'] = player.get('blk', 0) / games
        p['tpg'] = player.get('to', 0) / games
        p['fpg'] = player.get('fouls', 0) / games
        p['plus_minus'] = player.get('plus_minus', 0)
        
        # Add advanced metrics
        advanced = advanced_calc.calculate_player_advanced_stats(player['name'])
        if advanced:
            p['efg_pct'] = advanced['scoring_efficiency']['efg_pct']
            p['ts_pct'] = advanced['scoring_efficiency']['ts_pct']
            p['per'] = advanced['scoring_efficiency']['per']
            p['usage_rate'] = advanced['usage_role']['usage_proxy']
            p['ast_to_ratio'] = advanced['ball_handling']['ast_to_ratio']
            p['defensive_rating'] = advanced['defense_activity']['defensive_rating']
            p['pm_per_game'] = advanced['impact']['pm_per_game']
            p['role'] = advanced['usage_role']['role']
            p['consistency_score'] = advanced['consistency']['consistency_score']
            p['clutch_factor'] = advanced['clutch_performance']['clutch_factor']
        
        enhanced.append(p)
    
    return jsonify(sorted(enhanced, key=lambda x: x['ppg'], reverse=True))


@app.route('/api/player/<player_name>')
def api_player(player_name):
    player_name = player_name.strip()
    if not player_name or len(player_name) > 100:
        return jsonify({'error': 'Invalid player name'}), 400
    
    stats = data.get_player_stats(player_name)
    if stats:
        # Enrich stats with per-game averages (same as /api/players endpoint)
        enhanced_stats = stats.copy()
        games = stats.get('games', 1)
        
        # Add per-game stats if not present
        enhanced_stats['spg'] = stats.get('stl', 0) / games
        enhanced_stats['bpg'] = stats.get('blk', 0) / games
        enhanced_stats['tpg'] = stats.get('to', 0) / games
        enhanced_stats['fpg'] = stats.get('fouls', 0) / games
        enhanced_stats['plus_minus'] = stats.get('plus_minus', 0)
        
        # Add roster info
        roster_info = next((p for p in data.roster if p['name'] == player_name), None)
        if roster_info:
            enhanced_stats['number'] = roster_info.get('number')
            enhanced_stats['grade'] = roster_info.get('grade')
        
        return jsonify({
            'season_stats': enhanced_stats,
            'game_logs': data.get_player_game_logs(player_name),
            'roster_info': roster_info
        })
    return jsonify({'error': 'Player not found'}), 404


@app.route('/api/leaderboards')
@lru_cache(maxsize=1)
def api_leaderboards():
    players = list(data.season_player_stats.values())
    return jsonify({
        'pts': sorted(players, key=lambda x: x['pts'], reverse=True)[:10],
        'reb': sorted(players, key=lambda x: x['reb'], reverse=True)[:10],
        'asst': sorted(players, key=lambda x: x['asst'], reverse=True)[:10],
        'fg_pct': sorted([p for p in players if p['fga'] > 0], key=lambda x: x['fg_pct'], reverse=True)[:10],
        'fg3_pct': sorted([p for p in players if p['fg3a'] > 0], key=lambda x: x['fg3_pct'], reverse=True)[:10],
        'ft_pct': sorted([p for p in players if p['fta'] > 0], key=lambda x: x['ft_pct'], reverse=True)[:10],
        'stl': sorted(players, key=lambda x: x.get('stl', 0), reverse=True)[:10],
        'blk': sorted(players, key=lambda x: x.get('blk', 0), reverse=True)[:10],
    })


@app.route('/api/player-trends/<player_name>')
def api_player_trends(player_name):
    player_name = player_name.strip()
    if not player_name or len(player_name) > 100:
        return jsonify({'error': 'Invalid player name'}), 400
    
    logs = data.get_player_game_logs(player_name)
    if not logs:
        return jsonify({'error': 'Player not found'}), 404
    
    logs = sorted(logs, key=lambda x: x['gameId'])
    return jsonify({
        'games': [g['gameId'] for g in logs],
        'opponents': [g['opponent'] for g in logs],
        'dates': [g['date'] for g in logs],
        'pts': [g['stats']['pts'] for g in logs],
        'fg': [g['stats']['fg_made'] for g in logs],
        'fg_att': [g['stats']['fg_att'] for g in logs],
        'fg3': [g['stats']['fg3_made'] for g in logs],
        'asst': [g['stats']['asst'] for g in logs],
        'reb': [g['stats']['oreb'] + g['stats']['dreb'] for g in logs],
        'stl': [g['stats']['stl'] for g in logs],
    })


@app.route('/api/team-trends')
@lru_cache(maxsize=1)
def api_team_trends():
    games = sorted(data.games, key=lambda x: x['gameId'])
    return jsonify({
        'games': [g['gameId'] for g in games],
        'opponents': [g['opponent'] for g in games],
        'dates': [g['date'] for g in games],
        'vc_score': [g['vc_score'] for g in games],
        'opp_score': [g['opp_score'] for g in games],
        'fg_pct': [g['team_stats']['fg']/g['team_stats']['fga']*100 if g['team_stats']['fga'] > 0 else 0 for g in games],
        'fg3_pct': [g['team_stats']['fg3']/g['team_stats']['fg3a']*100 if g['team_stats']['fg3a'] > 0 else 0 for g in games],
        'asst': [g['team_stats']['asst'] for g in games],
        'to': [g['team_stats']['to'] for g in games],
    })


# =============================================================================
# Advanced Stats API Routes
# =============================================================================

@app.route('/api/advanced/team')
@lru_cache(maxsize=1)
def api_team_advanced():
    return jsonify(advanced_calc.calculate_team_advanced_stats())


@app.route('/api/advanced/player/<player_name>')
def api_player_advanced(player_name):
    player_name = player_name.strip()
    if not player_name or len(player_name) > 100:
        return jsonify({'error': 'Invalid player name'}), 400
    
    stats = advanced_calc.calculate_player_advanced_stats(player_name)
    if not stats:
        return jsonify({'error': 'Player not found'}), 404
    return jsonify(stats)


@app.route('/api/advanced/game/<int:game_id>')
def api_game_advanced(game_id):
    stats = advanced_calc.calculate_game_advanced_stats(game_id)
    if not stats:
        return jsonify({'error': 'Game not found'}), 404
    return jsonify(stats)


@app.route('/api/advanced/patterns')
@lru_cache(maxsize=1)
def api_patterns():
    return jsonify(advanced_calc.calculate_win_loss_patterns())


@app.route('/api/advanced/volatility')
@lru_cache(maxsize=1)
def api_volatility():
    return jsonify(advanced_calc.calculate_volatility_metrics())


@app.route('/api/advanced/insights')
@lru_cache(maxsize=1)
def api_auto_insights():
    return jsonify({'insights': advanced_calc.generate_auto_insights()})


@app.route('/api/advanced/all')
def api_all_advanced():
    return jsonify({
        'team': advanced_calc.calculate_team_advanced_stats(),
        'patterns': advanced_calc.calculate_win_loss_patterns(),
        'volatility': advanced_calc.calculate_volatility_metrics(),
        'insights': advanced_calc.generate_auto_insights()
    })


# =============================================================================
# AI Analysis API Routes
# =============================================================================

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    """Chat endpoint with conversation history"""
    try:
        if not request.json:
            return jsonify({'error': 'Invalid JSON data'}), 400
        
        message = request.json.get('message', '').strip()
        history = request.json.get('history', [])
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        if len(message) > 1000:
            return jsonify({'error': 'Message too long'}), 400
        
        ai = get_ai_service()
        if not ai.is_configured:
            return jsonify({'error': 'OpenAI API key not configured'}), 500
        
        # Clean history
        clean_history = []
        for msg in (history or [])[-20:]:
            if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                if msg['role'] in ['user', 'assistant'] and len(str(msg['content'])) <= 2000:
                    clean_history.append({'role': msg['role'], 'content': str(msg['content']).strip()})
        
        context = build_stats_context(data)
        system_prompt = f"""You are an expert basketball statistics analyst. Use ONLY the provided stats data.
Always reference exact numbers from the data. Never make up statistics.

TEAM STATS DATA:
{context}"""
        
        response = ai.call_with_history(system_prompt, message, clean_history)
        return jsonify({'response': response, 'message': message})
    
    except APIError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/ai/analyze', methods=['POST'])
def ai_analyze():
    """General AI analysis endpoint"""
    try:
        if not request.json:
            return jsonify({'error': 'Invalid JSON data'}), 400
        
        query = request.json.get('query', '').strip()
        analysis_type = request.json.get('type', 'general').strip().lower()
        
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        if len(query) > 1000:
            return jsonify({'error': 'Query too long'}), 400
        
        ai = get_ai_service()
        if not ai.is_configured:
            return jsonify({'error': 'OpenAI API key not configured'}), 500
        
        valid_types = {'general', 'player', 'team', 'trends', 'coaching'}
        if analysis_type not in valid_types:
            analysis_type = 'general'
        
        context = build_stats_context(data)
        prompt = ANALYSIS_PROMPTS.get(analysis_type, ANALYSIS_PROMPTS['general'])
        system_prompt = f"{prompt}\n\nTEAM DATA:\n{context}"
        
        analysis = ai.call_api(system_prompt, query, max_tokens=1500)
        return jsonify({'analysis': analysis, 'type': analysis_type, 'query': query})
    
    except APIError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/ai/player-insights/<player_name>')
def ai_player_insights(player_name):
    """Get AI insights for a specific player"""
    try:
        player_name = player_name.strip()
        if not player_name or len(player_name) > 100:
            return jsonify({'error': 'Invalid player name'}), 400
        
        if player_name not in data.season_player_stats:
            return jsonify({'error': 'Player not found'}), 404
        
        if player_name in EXCLUDED_PLAYERS:
            return jsonify({'error': 'Analysis not available'}), 404
        
        ai = get_ai_service()
        if not ai.is_configured:
            return jsonify({'error': 'OpenAI API key not configured'}), 500
        
        stats = data.season_player_stats[player_name]
        logs = sorted(data.get_player_game_logs(player_name), key=lambda x: x['gameId'])[-5:]
        
        # Build player context
        logs_text = "\n".join([
            f"G{g['gameId']} vs {g['opponent']}: {g['stats']['pts']}pts, {g['stats']['oreb']+g['stats']['dreb']}reb, {g['stats']['asst']}ast"
            for g in logs
        ])
        
        prompt = f"""Analyze {player_name}

SEASON ({stats['games']} games):
{stats['ppg']:.1f}PPG | {stats['rpg']:.1f}RPG | {stats['apg']:.1f}APG
{stats['fg_pct']:.1f}%FG | {stats['fg3_pct']:.1f}%3P | {stats['ft_pct']:.1f}%FT

RECENT GAMES:
{logs_text}

Analyze: 1) Scoring Output 2) Efficiency 3) Consistency 4) Role 5) Trend"""
        
        insights = ai.call_api(
            "Analyze player performance. Be specific with numbers.",
            prompt,
            max_tokens=800
        )
        
        return jsonify({'player': player_name, 'insights': insights})
    
    except APIError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Player insights error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/ai/game-analysis/<int:game_id>')
def ai_game_analysis(game_id):
    """Get AI analysis of a specific game"""
    try:
        game = data.get_game_by_id(game_id)
        if not game:
            return jsonify({'error': 'Game not found'}), 404
        
        ai = get_ai_service()
        if not ai.is_configured:
            return jsonify({'error': 'OpenAI API key not configured'}), 500
        
        ts = game['team_stats']
        season = data.season_team_stats
        
        fg_pct = (ts['fg']/ts['fga']*100) if ts['fga'] > 0 else 0
        fg3_pct = (ts['fg3']/ts['fg3a']*100) if ts['fg3a'] > 0 else 0
        
        # Player performances
        players_text = "\n".join([
            f"{p['name']}: {p['pts']}pts, {p.get('reb', 0)}reb, {p.get('asst', 0)}ast"
            for p in sorted(game.get('player_stats', []), key=lambda x: x['pts'], reverse=True)[:5]
            if p['name'] not in EXCLUDED_PLAYERS
        ])
        
        prompt = f"""VC vs {game['opponent']} ({game['date']})
Result: {game['vc_score']}-{game['opp_score']} ({game['result']})

GAME: {fg_pct:.1f}%FG (season {season['fg_pct']:.1f}%), {fg3_pct:.1f}%3P, {ts['asst']}AST, {ts['to']}TO

TOP PLAYERS:
{players_text}

Analyze: Shooting deviation, possession control, scoring distribution, key performances."""
        
        analysis = ai.call_api(
            "Analyze this basketball game. Compare to season averages.",
            prompt,
            max_tokens=1000
        )
        
        return jsonify({
            'game': f"{game['opponent']} ({game['date']})",
            'analysis': analysis
        })
    
    except APIError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Game analysis error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/ai/team-summary')
def ai_team_summary():
    """Get AI team summary with caching"""
    try:
        # Check cache
        if os.path.exists(Config.TEAM_CACHE):
            with open(Config.TEAM_CACHE) as f:
                return jsonify(json.load(f))
        
        ai = get_ai_service()
        if not ai.is_configured:
            return jsonify({'error': 'OpenAI API key not configured'}), 500
        
        context = build_stats_context(data)
        
        prompt = """Diagnose this season using only box score data.
1. Primary Win Condition - what stat pattern predicts wins?
2. Critical Thresholds - what values separate wins from losses?
3. Failure Modes - what breakdown causes losses?
4. Actionable Changes - what can realistically improve?

Be specific with numbers. No speculation."""
        
        summary = ai.call_api(
            f"Performance diagnostician analyzing basketball data.\n\nDATA:\n{context}",
            prompt,
            max_tokens=2000,
            temperature=0
        )
        
        result = {'summary': summary}
        with open(Config.TEAM_CACHE, 'w') as f:
            json.dump(result, f)
        
        return jsonify(result)
    
    except APIError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Team summary error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/ai/team-summary', methods=['DELETE'])
def clear_team_summary():
    """Clear team summary cache"""
    try:
        if os.path.exists(Config.TEAM_CACHE):
            os.remove(Config.TEAM_CACHE)
        return jsonify({'message': 'Cache cleared'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =============================================================================
# Season Analysis API
# =============================================================================

@app.route('/api/season-analysis')
def get_season_analysis():
    """Get cached season analysis"""
    try:
        force = request.args.get('force', 'false').lower() == 'true'
        
        if not force and os.path.exists(Config.ANALYSIS_CACHE):
            with open(Config.ANALYSIS_CACHE) as f:
                return jsonify(json.load(f))
        
        ai = get_ai_service()
        if not ai.is_configured:
            return jsonify({'error': 'OpenAI API key not configured'}), 500
        
        games = sorted(data.games, key=lambda x: x['gameId'])
        season = data.season_team_stats
        
        # Generate per-game analysis
        per_game = []
        for game in games:
            ts = game['team_stats']
            fg_pct = (ts['fg']/ts['fga']*100) if ts['fga'] > 0 else 0
            
            # Get player performances
            players = []
            for p in sorted(game.get('player_stats', []), key=lambda x: x['pts'], reverse=True):
                if p['name'] in EXCLUDED_PLAYERS:
                    continue
                season_ppg = data.season_player_stats.get(p['name'], {}).get('ppg', 0)
                diff = p['pts'] - season_ppg
                players.append({
                    'name': p['name'],
                    'pts': p['pts'],
                    'season_ppg': season_ppg,
                    'diff': diff,
                    'indicator': '↑' if diff > 1 else ('↓' if diff < -1 else '→')
                })
            
            prompt = f"""Game {game['gameId']}: VC vs {game['opponent']} - {game['result']} {game['vc_score']}-{game['opp_score']}
FG: {fg_pct:.1f}%, AST: {ts['asst']}, TO: {ts['to']}
Top: {', '.join([f"{p['name']} {p['pts']}pts ({p['indicator']}{abs(p['diff']):.0f})" for p in players[:3]])}

Output: PRIMARY DRIVER, SECONDARY DRIVER, RISK EXPOSED"""
            
            try:
                analysis = ai.call_api(
                    "Generate compact game diagnostics.",
                    prompt,
                    max_tokens=400
                )
            except:
                analysis = "Analysis pending..."
            
            per_game.append({
                'game': game['gameId'],
                'opponent': game['opponent'],
                'date': game['date'],
                'score': f"{game['vc_score']}-{game['opp_score']}",
                'result': game['result'],
                'player_performances': players,
                'analysis': analysis
            })
        
        # Season summary
        summary_prompt = f"""Season: {season['win']}-{season['loss']} ({season['win']/(season['win']+season['loss'])*100:.0f}%)
{season['ppg']:.1f}PPG, {season['fg_pct']:.1f}%FG, {season['fg3_pct']:.1f}%3P

Comprehensive analysis: strengths, weaknesses, evolution, improvements needed."""
        
        summary = ai.call_api(
            "Expert basketball coach providing season analysis.",
            summary_prompt,
            max_tokens=2000
        )
        
        result = {
            'generated_at': datetime.now().isoformat(),
            'season_summary': summary,
            'per_game_analysis': per_game
        }
        
        with open(Config.ANALYSIS_CACHE, 'w') as f:
            json.dump(result, f, indent=2)
        
        return jsonify(result)
    
    except APIError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Season analysis error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/season-analysis', methods=['DELETE'])
def clear_analysis():
    """Clear season analysis cache"""
    try:
        if os.path.exists(Config.ANALYSIS_CACHE):
            os.remove(Config.ANALYSIS_CACHE)
        return jsonify({'message': 'Cache cleared'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =============================================================================
# Player Analysis API
# =============================================================================

def _load_player_cache():
    if os.path.exists(Config.PLAYER_CACHE):
        try:
            with open(Config.PLAYER_CACHE) as f:
                return json.load(f)
        except:
            return {}
    return {}


def _save_player_cache(cache):
    with open(Config.PLAYER_CACHE, 'w') as f:
        json.dump(cache, f, indent=2)


@app.route('/api/ai/player-analysis/<player_name>')
def get_player_analysis(player_name):
    """Get comprehensive player analysis with caching"""
    try:
        player_name = player_name.strip()
        if not player_name or len(player_name) > 100:
            return jsonify({'error': 'Invalid player name'}), 400
        
        if player_name not in data.season_player_stats:
            return jsonify({'error': 'Player not found'}), 404
        
        ai = get_ai_service()
        if not ai.is_configured:
            return jsonify({'error': 'OpenAI API key not configured'}), 500
        
        force = request.args.get('regenerate', 'false').lower() == 'true'
        cache = _load_player_cache()
        
        if not force and player_name in cache:
            cached = cache[player_name]
            cached['cached'] = True
            return jsonify(cached)
        
        stats = data.season_player_stats[player_name]
        advanced = advanced_calc.calculate_player_advanced_stats(player_name)
        logs = data.get_player_game_logs(player_name)
        
        # Build context
        context = f"""
PLAYER: {player_name}

SEASON ({stats['games']} Games):
- {stats['ppg']:.1f}PPG, {stats['rpg']:.1f}RPG, {stats['apg']:.1f}APG
- {stats['fg_pct']:.1f}%FG, {stats['fg3_pct']:.1f}%3P, {stats['ft_pct']:.1f}%FT
- {stats.get('stl', 0)/stats['games']:.1f}SPG, {stats.get('blk', 0)/stats['games']:.1f}BPG
"""
        
        if advanced:
            context += f"""
ADVANCED:
- eFG%: {advanced['scoring_efficiency']['efg_pct']:.1f}%
- TS%: {advanced['scoring_efficiency']['ts_pct']:.1f}%
- Usage: {advanced['usage_role']['usage_proxy']:.1f}%
- Role: {advanced['usage_role']['role']}
"""
        
        if logs:
            pts_list = [g['stats']['pts'] if 'stats' in g else g.get('pts', 0) for g in logs]
            if pts_list:
                context += f"""
CONSISTENCY:
- Range: {min(pts_list)}-{max(pts_list)} pts
- Recent (last 3): {sum(pts_list[-3:])/min(3, len(pts_list)):.1f}PPG
"""
        
        prompt = f"""{context}

COMPREHENSIVE ANALYSIS:
1. Performance Profile (strengths, weaknesses)
2. Scoring Analysis (efficiency, volume)
3. Role & Impact
4. Consistency & Trends
5. Development Areas
6. Key Insights (3-5 data-driven observations)"""
        
        analysis = ai.call_api(
            "Expert basketball analyst. Use specific statistics. Be thorough but concise.",
            prompt,
            max_tokens=2000
        )
        
        result = {
            'player': player_name,
            'analysis': analysis,
            'generated_at': datetime.now().isoformat(),
            'stats_summary': {
                'games': stats['games'],
                'ppg': round(stats['ppg'], 1),
                'rpg': round(stats['rpg'], 1),
                'apg': round(stats['apg'], 1),
                'fg_pct': round(stats['fg_pct'], 1),
                'fg3_pct': round(stats['fg3_pct'], 1),
                'ft_pct': round(stats['ft_pct'], 1)
            },
            'cached': False
        }
        
        cache[player_name] = result
        _save_player_cache(cache)
        
        return jsonify(result)
    
    except APIError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Player analysis error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/ai/player-analysis/<player_name>', methods=['DELETE'])
def clear_player_analysis(player_name):
    """Clear cached analysis for a player"""
    try:
        player_name = player_name.strip()
        cache = _load_player_cache()
        if player_name in cache:
            del cache[player_name]
            _save_player_cache(cache)
            return jsonify({'message': f'Cache cleared for {player_name}'})
        return jsonify({'message': 'No cached analysis found'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
