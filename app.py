from flask import Flask, render_template, jsonify, request
from functools import lru_cache
import json
import os
from datetime import datetime
import requests
from dotenv import load_dotenv
from advanced_stats import AdvancedStatsCalculator

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 year cache for static files
app.config['COMPRESS_LEVEL'] = 6  # Gzip compression

# OpenAI API configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_API_URL = 'https://api.openai.com/v1/chat/completions'

# Analysis cache file
ANALYSIS_CACHE_FILE = 'season_analysis.json'

# Load stats data
STATS_FILE = 'vc_stats_output.json'
ROSTER_FILE = 'roster.json'
with open(STATS_FILE) as f:
    stats_data = json.load(f)
with open(ROSTER_FILE) as f:
    roster_data = json.load(f)

# Initialize advanced stats calculator
advanced_calc = AdvancedStatsCalculator(stats_data)

@app.route('/')
def dashboard():
    """Main dashboard with season overview"""
    return render_template('dashboard.html')

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
    """Get all player season stats"""
    players = list(stats_data['season_player_stats'].values())
    
    # Merge in roster information (number, grade)
    roster_dict = {p['name']: p for p in roster_data['roster']}
    for player in players:
        if player['name'] in roster_dict:
            player['number'] = roster_dict[player['name']].get('number')
            player['grade'] = roster_dict[player['name']].get('grade')
    
    # Sort by PPG
    players = sorted(players, key=lambda x: x['ppg'], reverse=True)
    return jsonify(players)

@app.route('/api/player/<player_name>')
def api_player(player_name):
    """Get specific player details and game logs"""
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
    games = sorted(stats_data['games'], key=lambda x: x['gameId'])
    season_stats = stats_data['season_team_stats']
    
    context = f"""
Valley Catholic Varsity Basketball - 2025-2026 Season Stats

TEAM RECORD: {season_stats['win']}-{season_stats['loss']}
Win Percentage: {season_stats['win']/(season_stats['win']+season_stats['loss'])*100:.1f}%

TEAM STATISTICS:
- Points Per Game: {season_stats['ppg']:.1f}
- Rebounds Per Game: {season_stats['rpg']:.1f}
- Assists Per Game: {season_stats['apg']:.1f}
- Field Goal %: {season_stats['fg_pct']:.1f}%
- Three Point %: {season_stats['fg3_pct']:.1f}%
- Free Throw %: {season_stats['ft_pct']:.1f}%

GAMES PLAYED: {len(games)}
Game Details (by date):
"""
    
    for game in games:
        context += f"\n- vs {game['opponent']} ({game['date']}): VC {game['vc_score']}-{game['opp_score']} ({game['result']})"
    
    context += "\n\nPLAYER STATISTICS:\n"
    for player_name, stats in sorted(stats_data['season_player_stats'].items(), 
                                     key=lambda x: x[1]['ppg'], reverse=True):
        context += f"\n{player_name}: {stats['ppg']:.1f} PPG, {stats['rpg']:.1f} RPG, {stats['apg']:.1f} APG, {stats['fg_pct']:.1f}% FG"
    
    return context

def call_openai_api(system_prompt, user_message, max_tokens=1500, temperature=0.7):
    """Make API call to OpenAI using requests library"""
    try:
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4o",
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
    
    except Exception as e:
        raise Exception(f"OpenAI API error: {str(e)}")

@app.route('/api/ai/analyze', methods=['POST'])
def ai_analyze():
    """General AI analysis endpoint"""
    try:
        data = request.json
        query = data.get('query', '')
        analysis_type = data.get('type', 'general')  # general, player, team, game, trends
        
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        
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
        
        analysis = call_openai_api(system_prompt, query, max_tokens=1500)
        
        return jsonify({
            'analysis': analysis,
            'type': analysis_type,
            'query': query
        })
    
    except Exception as e:
        return jsonify({'error': f'AI analysis failed: {str(e)}'}), 500

@app.route('/api/ai/player-insights/<player_name>', methods=['GET'])
def ai_player_insights(player_name):
    """Get AI-generated insights for a specific player"""
    try:
        if player_name not in stats_data['season_player_stats']:
            return jsonify({'error': 'Player not found'}), 404
        
        if not OPENAI_API_KEY:
            return jsonify({'error': 'OpenAI API key not configured'}), 500
        
        excluded_players = ['Matthew Gunther', 'Liam Plep', 'Gavin Galan', 'Kye Fixter']
        if player_name in excluded_players:
            return jsonify({'error': 'Analysis not available for this player'}), 404
        
        player_stats = stats_data['season_player_stats'][player_name]
        stats_context = get_stats_context()
        
        prompt = f"""Diagnose {player_name}

Season Baseline:
{player_stats['ppg']:.1f} PPG | {player_stats['fg_pct']:.1f}% FG | {player_stats['fg3_pct']:.1f}% 3PT | {player_stats['ft_pct']:.1f}% FT | {player_stats['games']} games

REQUIRED ANALYSIS:
1. PERFORMANCE GAP - Game output vs season baseline
2. CONSISTENCY PROFILE - Variance indicator using point or efficiency spread
3. SKILL LIMITATION - Specific efficiency weakness by shot type or usage
4. ROLE REALITY - Is current usage aligned with efficiency?

OUTPUT RULES:
- Numbers required in every section
- No praise
- No inferred intent"""
        
        system_prompt = f"""Diagnose player performance strictly through measurable outputs. TEAM DATA: {stats_context}"""
        
        insights = call_openai_api(system_prompt, prompt, max_tokens=1000)
        
        return jsonify({
            'player': player_name,
            'insights': insights
        })
    
    except Exception as e:
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
        
        stats_context = get_stats_context()
        
        fg_pct_game = (game['team_stats']['fg']/game['team_stats']['fga']*100) if game['team_stats']['fga'] > 0 else 0
        prompt = f"""VC vs {game['opponent']} | {game['date']}
Score: {game['vc_score']}-{game['opp_score']}

Team Line:
FG {game['team_stats']['fg']}/{game['team_stats']['fga']} ({fg_pct_game:.1f}%)
3PT {game['team_stats']['fg3']}/{game['team_stats']['fg3a']}
FT {game['team_stats']['ft']}/{game['team_stats']['fta']}
REB {game['team_stats']['reb']}
AST {game['team_stats']['asst']}
TO {game['team_stats']['to']}

REQUIRED OUTPUT:
- SHOOTING DEVIATION vs season
- POSSESSION CONTROL (TO, REB)
- SCORING CONCENTRATION
- FAILURE OR SUCCESS DRIVER"""
        
        system_prompt = f"""Diagnose what failed or succeeded in this game using measurable deltas only. TEAM DATA: {stats_context}"""
        
        analysis = call_openai_api(system_prompt, prompt, max_tokens=1000)
        
        return jsonify({
            'game': f"{game['opponent']} ({game['date']})",
            'analysis': analysis
        })
    
    except Exception as e:
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
        
        summary = call_openai_api(system_prompt, prompt, max_tokens=2000, temperature=0)
        
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
        # Check if analysis is cached
        if os.path.exists(ANALYSIS_CACHE_FILE):
            with open(ANALYSIS_CACHE_FILE) as f:
                return jsonify(json.load(f))
        
        # Generate analysis if not cached
        if not OPENAI_API_KEY:
            return jsonify({'error': 'OpenAI API key not configured'}), 500
        
        games = sorted(stats_data['games'], key=lambda x: x['gameId'])
        season_stats = stats_data['season_team_stats']
        
        # Generate per-game analysis
        per_game_analysis = []
        
        # First, calculate player season averages for comparison
        player_season_stats = stats_data['season_player_stats']
        
        for i, game in enumerate(games, 1):
            team_stats = game['team_stats']
            fg_pct = (team_stats['fg']/team_stats['fga']*100) if team_stats['fga'] > 0 else 0
            
            # Exclude specified players from analysis
            excluded_players = {'Matthew Gunther', 'Liam Plep', 'Gavin Galan', 'Kye Fixter'}
            
            # Get top performers and their stats (excluding specified players)
            player_stats_game = [p for p in game['player_stats'] if p['name'] not in excluded_players]
            player_stats_game = sorted(player_stats_game, key=lambda x: x['pts'], reverse=True)
            
            # Top 3 performers
            top_performers = []
            for j, player in enumerate(player_stats_game[:3]):
                fg_pct_p = float(player['fg_pct'].rstrip('%')) if '%' in player['fg_pct'] else 0
                fg3_pct_p = float(player['fg3_pct'].rstrip('%')) if '%' in player['fg3_pct'] else 0
                ft_pct_p = float(player['ft_pct'].rstrip('%')) if '%' in player['ft_pct'] else 0
                
                season_avg = player_season_stats.get(player['name'], {})
                season_ppg = season_avg.get('ppg', 0)
                
                perf_vs_avg = player['pts'] - season_ppg
                status = "Above Average" if perf_vs_avg > 0 else "Below Average"
                
                top_performers.append({
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
                    'status': status
                })
            
            # Underperformers (players with low points)
            underperformers = []
            for player in player_stats_game[-3:]:
                if player['pts'] > 0:
                    season_avg = player_season_stats.get(player['name'], {})
                    season_ppg = season_avg.get('ppg', 0)
                    underperformers.append({
                        'name': player['name'],
                        'pts': player['pts'],
                        'season_ppg': season_ppg,
                        'diff': player['pts'] - season_ppg
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

TOP PERFORMERS:
"""
            for perf in top_performers:
                game_prompt += f"- {perf['rank']}. {perf['name']}: {perf['pts']}pts ({perf['fg_pct']:.0f}% FG, {perf['fg3_pct']:.0f}% 3P, {perf['ft_pct']:.0f}% FT) | {perf['reb']}reb {perf['asst']}ast | Season Avg: {perf['season_ppg']:.1f}ppg | {perf['status']} by {abs(perf['diff']):.1f}pts\n"
            
            game_prompt += f"""
UNDERPERFORMERS:
"""
            for under in underperformers:
                game_prompt += f"- {under['name']}: {under['pts']}pts (Season Avg: {under['season_ppg']:.1f}ppg) - {under['diff']:+.1f}pts vs avg\n"
            
            game_prompt += f"""
REQUIRED OUTPUT:
- PRIMARY GAME DRIVER
- SECONDARY DRIVER
- RISK EXPOSED"""
            
            system_prompt = "Generate compact, UI-safe game diagnostics using measurable deltas only."
            
            try:
                analysis_text = call_openai_api(system_prompt, game_prompt, max_tokens=800)
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
                    'top_performers': top_performers,
                    'underperformers': underperformers,
                    'analysis': analysis_text
                })
            except Exception as e:
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
        season_summary = call_openai_api(system_prompt, season_prompt, max_tokens=2000)
        
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'production') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)
