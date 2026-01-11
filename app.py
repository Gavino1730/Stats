from flask import Flask, render_template, jsonify, request
from functools import lru_cache
import json
import os
from datetime import datetime
import requests

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

@app.route('/api/leaderboards')
@lru_cache(maxsize=1)
def api_leaderboards():
    """Get leaderboards for various stats - cached"""
    players = list(stats_data['season_player_stats'].values())
    
    leaderboards = {
        'ppg': sorted(players, key=lambda x: x['ppg'], reverse=True)[:10],
        'rpg': sorted(players, key=lambda x: x['rpg'], reverse=True)[:10],
        'apg': sorted(players, key=lambda x: x['apg'], reverse=True)[:10],
        'fg_pct': sorted([p for p in players if p['fga'] > 0], key=lambda x: x['fg_pct'], reverse=True)[:10],
        'fg3_pct': sorted([p for p in players if p['fg3a'] > 0], key=lambda x: x['fg3_pct'], reverse=True)[:10],
        'ft_pct': sorted([p for p in players if p['fta'] > 0], key=lambda x: x['ft_pct'], reverse=True)[:10],
        'stl': sorted(players, key=lambda x: x.get('stl', 0), reverse=True)[:10],
        'blk': sorted(players, key=lambda x: x.get('blk', 0), reverse=True)[:10],
    }
    
    return jsonify(leaderboards)

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

def call_openai_api(system_prompt, user_message, max_tokens=1500):
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
            "temperature": 0.7,
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
            'general': f"""You are an expert basketball coach and sports analyst specializing in player development, 
team strategy, and performance optimization. You have deep knowledge of basketball statistics and trends. 
Analyze the data and provide detailed, actionable insights.

TEAM DATA:
{stats_context}""",
            'player': f"""You are an expert basketball coach specializing in player analysis and development.
Provide detailed performance insights, strengths, areas for improvement, and specific coaching recommendations.

TEAM DATA:
{stats_context}""",
            'team': f"""You are a basketball strategy expert and performance analyst.
Analyze team dynamics, strengths, weaknesses, and provide strategic recommendations.

TEAM DATA:
{stats_context}""",
            'trends': f"""You are a basketball analytics expert specializing in identifying patterns and trends.
Look for performance patterns, consistency issues, and predictive insights.

TEAM DATA:
{stats_context}""",
            'coaching': f"""You are an elite basketball coach with championship experience.
Provide actionable coaching recommendations, practice focus areas, and game strategies.

TEAM DATA:
{stats_context}"""
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
        
        if not client.api_key:
            return jsonify({'error': 'OpenAI API key not configured'}), 500
        
        player_stats = stats_data['season_player_stats'][player_name]
        stats_context = get_stats_context()
        
        prompt = f"""Analyze {player_name}'s performance this season:
- PPG: {player_stats['ppg']:.1f}
- RPG: {player_stats['rpg']:.1f}
- APG: {player_stats['apg']:.1f}
- FG%: {player_stats['fg_pct']:.1f}%
- 3P%: {player_stats['fg3_pct']:.1f}%
- FT%: {player_stats['ft_pct']:.1f}%
- Games: {player_stats['games']}

Provide:
1. Performance summary (strengths and areas for improvement)
2. Comparison to team averages
3. Specific coaching recommendations
4. Development areas and potential
5. Role on the team"""
        
        system_prompt = f"""You are an expert basketball coach analyzing player performance.
{stats_context}"""
        
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
        
        if not client.api_key:
            return jsonify({'error': 'OpenAI API key not configured'}), 500
        
        stats_context = get_stats_context()
        
        prompt = f"""Analyze Valley Catholic's game vs {game['opponent']} on {game['date']}:
VC {game['vc_score']} - {game['opponent']} {game['opp_score']} ({game['result']})

Team Stats:
- FG: {game['team_stats']['fg']}-{game['team_stats']['fga']} ({game['team_stats']['fg']/game['team_stats']['fga']*100:.1f}%)
- 3P: {game['team_stats']['fg3']}-{game['team_stats']['fg3a']}
- Rebounds: {game['team_stats']['reb']}
- Assists: {game['team_stats']['asst']}
- Turnovers: {game['team_stats']['to']}

Provide:
1. Game summary and key moments
2. What went well
3. What needs improvement
4. Individual player performances (top performers)
5. Coaching adjustments for next game"""
        
        system_prompt = f"""You are an expert basketball coach analyzing game performance.
{stats_context}"""
        
        analysis = call_openai_api(system_prompt, prompt, max_tokens=1000)
        
        return jsonify({
            'game': f"{game['opponent']} ({game['date']})",
            'analysis': analysis
        })
    
    except Exception as e:
        return jsonify({'error': f'Failed to analyze game: {str(e)}'}), 500

@app.route('/api/ai/team-summary', methods=['GET'])
def ai_team_summary():
    """Get AI-generated team summary and recommendations"""
    try:
        if not client.api_key:
            return jsonify({'error': 'OpenAI API key not configured'}), 500
        
        stats_context = get_stats_context()
        
        prompt = """Provide a comprehensive team analysis including:
1. Season performance summary
2. Team strengths
3. Areas needing improvement
4. Key players and their roles
5. Trends and patterns (winning/losing patterns, momentum)
6. Coaching recommendations for rest of season
7. Potential for playoffs/championship run
8. Individual player development focus areas"""
        
        system_prompt = f"""You are an elite basketball coach providing strategic analysis.
{stats_context}"""
        
        summary = call_openai_api(system_prompt, prompt, max_tokens=2000)
        
        return jsonify({
            'summary': summary
        })
    
    except Exception as e:
        return jsonify({'error': f'Failed to generate summary: {str(e)}'}), 500

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
            
            # Get top performers and their stats
            player_stats_game = game['player_stats']
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
ANALYSIS REQUIRED:
1. TOP PERFORMERS - Why did they excel? What worked in their game?
2. UNDERPERFORMERS - Why the struggles? Defensive pressure? Off night?
3. SHOOTING EFFICIENCY - How did we shoot compared to season average? Cold/hot streaks evident?
4. KEY TURNING POINTS - What moments changed the game? When did momentum shift?
5. WHAT WORKED - Specific plays, strategies, lineups that were effective
6. WHAT NEEDS IMPROVEMENT - Defensive gaps, offensive struggles, turnover issues
7. COACHING ADJUSTMENTS - Specific drills, strategies, lineup changes for next game
8. PLAYER COMPARISONS - Who exceeded expectations? Who underperformed? Track patterns."""
            
            system_prompt = f"You are an elite basketball coach providing ultra-detailed game analysis. Be specific about player performances, shooting efficiency, and actionable coaching recommendations."
            
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
    app.run(debug=True, port=5000)
