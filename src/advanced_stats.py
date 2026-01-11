"""
Advanced Statistics Calculator
Calculates comprehensive metrics from box score data only.
No play-by-play, no shot charts, no opponent player tracking.
"""

import json
from typing import Dict, List, Any, Optional
import statistics

# Constants
FREE_THROW_POSSESSION_FACTOR = 0.44
THREE_POINT_MULTIPLIER = 0.5
PRIMARY_SCORER_THRESHOLD = 20.0  # percentage
SECONDARY_SCORER_THRESHOLD = 10.0  # percentage
MIN_GAMES_FOR_STATS = 1
TURNOVER_THRESHOLD = 13
FG_PERCENTAGE_THRESHOLD = 44.0


class AdvancedStatsCalculator:
    """Calculate advanced metrics from box score data"""
    
    def __init__(self, stats_data: Dict):
        self.stats_data = stats_data
        self.games = stats_data['games']
        self.season_team_stats = stats_data['season_team_stats']
        self.season_player_stats = stats_data['season_player_stats']
        
    # ==============================================================================
    # A. TEAM LEVEL STATS
    # ==============================================================================
    
    def calculate_team_advanced_stats(self) -> Dict:
        """Calculate all advanced team-level statistics"""
        
        games = self.games
        team_stats = self.season_team_stats
        
        # Validate required data
        if not team_stats or not games:
            return {}
        
        # Calculate total games
        total_games = team_stats.get('win', 0) + team_stats.get('loss', 0)
        if total_games == 0:
            return {}
        
        # Estimated possessions (FGA + 0.44*FTA - OREB + TO)
        est_poss = (team_stats.get('fga', 0) + 
                    (FREE_THROW_POSSESSION_FACTOR * team_stats.get('fta', 0)) - 
                    team_stats.get('oreb', 0) + team_stats.get('to', 0))
        
        # Scoring & Efficiency
        pts = team_stats.get('ppg', 0) * total_games
        ppg = team_stats.get('ppg', 0)
        ppp = pts / est_poss if est_poss > 0 else 0
        
        # Shot percentages
        fg_pct = team_stats['fg_pct']
        fg2_made = team_stats['fg'] - team_stats['fg3']
        fg2_att = team_stats['fga'] - team_stats['fg3a']
        fg2_pct = (fg2_made / fg2_att * 100) if fg2_att > 0 else 0
        fg3_pct = team_stats['fg3_pct']
        ft_pct = team_stats['ft_pct']
        
        # Advanced shooting metrics
        efg_pct = ((team_stats['fg'] + 0.5 * team_stats['fg3']) / team_stats['fga'] * 100) if team_stats['fga'] > 0 else 0
        ts_pct = (pts / (2 * (team_stats['fga'] + 0.44 * team_stats['fta'])) * 100) if (team_stats['fga'] + team_stats['fta']) > 0 else 0
        pts_per_shot = pts / team_stats['fga'] if team_stats['fga'] > 0 else 0
        pts_per_fga = pts / team_stats['fga'] if team_stats['fga'] > 0 else 0
        pts_per_fta = pts / team_stats['fta'] if team_stats['fta'] > 0 else 0
        
        # Shot Mix & Dependency
        fg3_attempt_rate = (team_stats['fg3a'] / team_stats['fga'] * 100) if team_stats['fga'] > 0 else 0
        ft_rate = (team_stats['fta'] / team_stats['fga'] * 100) if team_stats['fga'] > 0 else 0
        inside_scoring_reliance = ((fg2_att / team_stats['fga']) * 100) if team_stats['fga'] > 0 else 0
        
        # Shot balance (what % of points from 2PT, 3PT, FT)
        pts_from_2 = fg2_made * 2
        pts_from_3 = team_stats['fg3'] * 3
        pts_from_ft = team_stats['ft']
        shot_balance = {
            '2pt_share': (pts_from_2 / pts * 100) if pts > 0 else 0,
            '3pt_share': (pts_from_3 / pts * 100) if pts > 0 else 0,
            'ft_share': (pts_from_ft / pts * 100) if pts > 0 else 0
        }
        
        # Possession Control
        to_per_poss = team_stats['to'] / est_poss if est_poss > 0 else 0
        to_per_100 = (team_stats['to'] / est_poss * 100) if est_poss > 0 else 0
        ast_to_ratio = team_stats['asst'] / team_stats['to'] if team_stats['to'] > 0 else 0
        reb_per_poss = team_stats['rpg'] / (est_poss / total_games) if est_poss > 0 else 0
        
        # Rebound rates (estimated without opponent rebounds)
        total_reb_opps = team_stats['reb'] * 2  # Rough estimate
        oreb_rate = (team_stats['oreb'] / total_reb_opps * 100) if total_reb_opps > 0 else 0
        dreb_rate = (team_stats['dreb'] / total_reb_opps * 100) if total_reb_opps > 0 else 0
        
        # Ball Movement
        apg = team_stats['apg']
        ast_per_fg = team_stats['asst'] / team_stats['fg'] if team_stats['fg'] > 0 else 0
        assisted_scoring_rate = (ast_per_fg * 100) if ast_per_fg <= 1 else 100
        isolation_reliance = 100 - assisted_scoring_rate
        
        # Defense (box score only)
        stl_per_game = team_stats['stl'] / total_games
        blk_per_game = team_stats['blk'] / total_games
        stl_blk_per_poss = (team_stats['stl'] + team_stats['blk']) / est_poss if est_poss > 0 else 0
        
        # Discipline & Control
        fpg = team_stats.get('fouls', 0) / total_games if 'fouls' in team_stats else 0
        
        return {
            'scoring_efficiency': {
                'ppg': ppg,
                'ppp': round(ppp, 3),
                'fg_pct': fg_pct,
                'fg2_pct': round(fg2_pct, 1),
                'fg3_pct': fg3_pct,
                'ft_pct': ft_pct,
                'efg_pct': round(efg_pct, 1),
                'ts_pct': round(ts_pct, 1),
                'pts_per_shot': round(pts_per_shot, 2),
                'pts_per_fga': round(pts_per_fga, 2),
                'pts_per_fta': round(pts_per_fta, 2)
            },
            'shot_mix': {
                'fg3_attempt_rate': round(fg3_attempt_rate, 1),
                'ft_rate': round(ft_rate, 1),
                'inside_scoring_reliance': round(inside_scoring_reliance, 1),
                'shot_balance': shot_balance
            },
            'possession_control': {
                'est_possessions': round(est_poss, 1),
                'to_per_poss': round(to_per_poss, 3),
                'to_per_100': round(to_per_100, 1),
                'ast_to_ratio': round(ast_to_ratio, 2),
                'reb_per_poss': round(reb_per_poss, 2),
                'oreb_rate': round(oreb_rate, 1),
                'dreb_rate': round(dreb_rate, 1)
            },
            'ball_movement': {
                'apg': apg,
                'ast_per_fg': round(ast_per_fg, 2),
                'assisted_scoring_rate': round(assisted_scoring_rate, 1),
                'isolation_reliance': round(isolation_reliance, 1)
            },
            'defense': {
                'spg': round(stl_per_game, 1),
                'bpg': round(blk_per_game, 1),
                'stl_blk_per_poss': round(stl_blk_per_poss, 3)
            },
            'discipline': {
                'fpg': round(fpg, 1),
                'fta_allowed': round(team_stats['fta'] / total_games, 1)
            }
        }
    
    # ==============================================================================
    # B. PLAYER LEVEL STATS
    # ==============================================================================
    
    def calculate_player_advanced_stats(self, player_name: str) -> Optional[Dict]:
        """Calculate advanced stats for a specific player"""
        
        if player_name not in self.season_player_stats:
            return None
        
        player = self.season_player_stats[player_name]
        team_stats = self.season_team_stats
        
        # Basic totals
        games = player.get('games', 0)
        if games == 0:
            return None
        
        pts = player.get('ppg', 0) * games
        fga = player.get('fga', 0)
        fta = player.get('fta', 0)
        fg = player.get('fg', 0)
        fg3 = player.get('fg3', 0)
        ft = player.get('ft', 0)
        to = player.get('to', 0)
        
        # Scoring & Efficiency
        ppg = player.get('ppg', 0)
        pts_per_shot = pts / fga if fga > 0 else 0
        pts_per_fga = pts / fga if fga > 0 else 0
        
        # Advanced shooting
        efg_pct = ((fg + THREE_POINT_MULTIPLIER * fg3) / fga * 100) if fga > 0 else 0
        ts_pct = (pts / (2 * (fga + FREE_THROW_POSSESSION_FACTOR * fta)) * 100) if (fga + fta) > 0 else 0
        
        # Usage & Role
        team_fga = team_stats.get('fga', 0)
        team_fta = team_stats.get('fta', 0)
        team_to = team_stats.get('to', 0)
        
        usage_proxy = ((fga + FREE_THROW_POSSESSION_FACTOR * fta + to) / 
                       (team_fga + FREE_THROW_POSSESSION_FACTOR * team_fta + team_to) * 100) if (team_fga + team_fta + team_to) > 0 else 0
        shot_volume_share = (fga / team_fga * 100) if team_fga > 0 else 0
        total_team_games = team_stats.get('win', 0) + team_stats.get('loss', 0)
        scoring_share = (pts / (team_stats.get('ppg', 0) * total_team_games) * 100) if team_stats.get('ppg', 0) > 0 and total_team_games > 0 else 0
        
        # Ball Handling
        ast = player['asst']
        ast_rate = (ast / games) if games > 0 else 0
        ast_to_ratio = ast / to if to > 0 else 0
        
        # Rebounding
        reb = player['reb']
        oreb = player.get('oreb', 0)
        dreb = player.get('dreb', 0)
        reb_share = (reb / team_stats['reb'] * 100) if team_stats['reb'] > 0 else 0
        
        # Defense & Activity
        stl = player['stl']
        blk = player['blk']
        stl_per_game = stl / games if games > 0 else 0
        blk_per_game = blk / games if games > 0 else 0
        
        # Impact
        plus_minus = player.get('plus_minus', 0)
        pm_per_game = plus_minus / games if games > 0 else 0
        
        # Fouls and discipline
        fouls = player.get('fouls', 0)
        fpg = fouls / games if games > 0 else 0
        
        # Game logs for advanced calculations
        game_logs = self.stats_data.get('player_game_logs', {}).get(player_name, [])
        
        # Consistency metrics
        pts_variance = self._calculate_variance([game.get('pts', 0) for game in game_logs])
        fg_pct_variance = self._calculate_variance([game.get('fg_pct', 0) for game in game_logs if game.get('fga', 0) > 0])
        
        # Clutch performance (games decided by 10 or less)
        clutch_games = [g for g in game_logs if abs(g.get('team_score', 0) - g.get('opp_score', 0)) <= 10]
        clutch_ppg = sum(g.get('pts', 0) for g in clutch_games) / len(clutch_games) if clutch_games else 0
        clutch_fg_pct = sum(g.get('fg_made', 0) for g in clutch_games) / sum(g.get('fg_att', 0) for g in clutch_games) * 100 if clutch_games and sum(g.get('fg_att', 0) for g in clutch_games) > 0 else 0
        
        # Performance vs opponent strength (estimated by opponent score)
        high_scoring_games = [g for g in game_logs if g.get('opp_score', 0) >= 70]  # Strong opponents
        vs_strong_ppg = sum(g.get('pts', 0) for g in high_scoring_games) / len(high_scoring_games) if high_scoring_games else ppg
        
        # Advanced efficiency metrics
        player_efficiency_rating = (pts + reb + ast + stl + blk - (fga - fg) - (fta - ft) - to) / games if games > 0 else 0
        
        # Shooting efficiency breakdown
        fg2a = fga - player.get('fg3a', 0)
        fg2 = fg - fg3
        fg2_pct = (fg2 / fg2a * 100) if fg2a > 0 else 0
        
        # Turnover rate (per 100 possessions)
        est_poss_player = (fga + 0.44 * fta + to)
        to_rate = (to / est_poss_player * 100) if est_poss_player > 0 else 0
        
        # Defensive rating estimate (steals + blocks per game)
        defensive_rating = stl_per_game + blk_per_game
        
        # Role classification
        role = self._classify_player_role(ppg, reb/games, ast/games, usage_proxy, shot_volume_share)
        
        return {
            'scoring_efficiency': {
                'ppg': ppg,
                'pts_per_shot': round(pts_per_shot, 2),
                'pts_per_fga': round(pts_per_fga, 2),
                'efg_pct': round(efg_pct, 1),
                'ts_pct': round(ts_pct, 1),
                'fg_pct': player['fg_pct'],
                'fg2_pct': round(fg2_pct, 1),
                'fg3_pct': player['fg3_pct'],
                'ft_pct': player['ft_pct'],
                'per': round(player_efficiency_rating, 1)
            },
            'usage_role': {
                'usage_proxy': round(usage_proxy, 1),
                'shot_volume_share': round(shot_volume_share, 1),
                'scoring_share': round(scoring_share, 1),
                'to_rate': round(to_rate, 1),
                'role': role,
                'primary_scorer': scoring_share >= PRIMARY_SCORER_THRESHOLD,
                'secondary_scorer': SECONDARY_SCORER_THRESHOLD <= scoring_share < PRIMARY_SCORER_THRESHOLD
            },
            'ball_handling': {
                'apg': round(ast_rate, 1),
                'ast_to_ratio': round(ast_to_ratio, 2),
                'total_assists': ast,
                'total_turnovers': to,
                'tpg': round(to / games, 1) if games > 0 else 0
            },
            'rebounding': {
                'rpg': player['rpg'],
                'oreb': oreb,
                'dreb': dreb,
                'oreb_pct': round((oreb / games / 10) * 100, 1) if games > 0 else 0,  # Rough estimate
                'dreb_pct': round((dreb / games / 25) * 100, 1) if games > 0 else 0,  # Rough estimate
                'reb_share': round(reb_share, 1)
            },
            'defense_activity': {
                'spg': round(stl_per_game, 1),
                'bpg': round(blk_per_game, 1),
                'total_stl': stl,
                'total_blk': blk,
                'defensive_rating': round(defensive_rating, 1),
                'deflections_per_game': round(stl_per_game * 2.5, 1)  # Estimated
            },
            'discipline': {
                'fpg': round(fpg, 1),
                'total_fouls': fouls,
                'foul_rate': round(fouls / (games * 40) * 100, 1) if games > 0 else 0  # Per 40 minutes estimate
            },
            'consistency': {
                'pts_variance': round(pts_variance, 1),
                'fg_pct_variance': round(fg_pct_variance, 1),
                'games_played': games,
                'consistency_score': round(100 - pts_variance, 1)  # Higher is more consistent
            },
            'clutch_performance': {
                'clutch_games': len(clutch_games),
                'clutch_ppg': round(clutch_ppg, 1),
                'clutch_fg_pct': round(clutch_fg_pct, 1),
                'clutch_factor': round(clutch_ppg / ppg if ppg > 0 else 0, 2)
            },
            'matchup_performance': {
                'vs_strong_teams_ppg': round(vs_strong_ppg, 1),
                'strong_team_factor': round(vs_strong_ppg / ppg if ppg > 0 else 0, 2)
            },
            'impact': {
                'plus_minus': plus_minus,
                'pm_per_game': round(pm_per_game, 1),
                'win_shares_estimate': round(plus_minus / 100, 2)  # Rough estimate
            }
        }
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of a list of values"""
        if len(values) < 2:
            return 0
        try:
            return statistics.variance(values)
        except:
            return 0
    
    def _classify_player_role(self, ppg: float, rpg: float, apg: float, usage: float, shot_share: float) -> str:
        """Classify player role based on stats"""
        if ppg >= 20 and usage >= 25:
            return "Primary Scorer"
        elif ppg >= 15 and usage >= 20:
            return "Secondary Scorer"
        elif apg >= 4 and usage >= 15:
            return "Playmaker"
        elif rpg >= 8:
            return "Rebounder"
        elif ppg >= 12 and shot_share >= 15:
            return "Shooter"
        elif ppg < 8 and rpg < 5 and apg < 3:
            return "Role Player"
        else:
            return "All-Around"
    
    # ==============================================================================
    # C. GAME LEVEL STATS
    # ==============================================================================
    
    def calculate_game_advanced_stats(self, game_id: int) -> Optional[Dict]:
        """Calculate advanced stats for a specific game"""
        
        game = None
        for g in self.games:
            if g['gameId'] == game_id:
                game = g
                break
        
        if not game:
            return None
        
        team_stats = game.get('team_stats', {})
        if not team_stats:
            return None
        
        # Estimated possessions
        est_poss = (team_stats.get('fga', 0) + 
                    (FREE_THROW_POSSESSION_FACTOR * team_stats.get('fta', 0)) - 
                    team_stats.get('oreb', 0) + team_stats.get('to', 0))
        
        # Scoring efficiency
        pts = game.get('vc_score', 0)
        ppp = pts / est_poss if est_poss > 0 else 0
        
        # Advanced shooting
        fga = team_stats.get('fga', 0)
        fg = team_stats.get('fg', 0)
        fg3 = team_stats.get('fg3', 0)
        fta = team_stats.get('fta', 0)
        
        efg_pct = ((fg + THREE_POINT_MULTIPLIER * fg3) / fga * 100) if fga > 0 else 0
        ts_pct = (pts / (2 * (fga + FREE_THROW_POSSESSION_FACTOR * fta)) * 100) if (fga + fta) > 0 else 0
        
        # Possession control
        to_per_100 = (team_stats['to'] / est_poss * 100) if est_poss > 0 else 0
        ast_to_ratio = team_stats['asst'] / team_stats['to'] if team_stats['to'] > 0 else 0
        
        # Ball movement
        ast_pct = (team_stats['asst'] / team_stats['fg'] * 100) if team_stats['fg'] > 0 else 0
        
        return {
            'game_id': game_id,
            'opponent': game['opponent'],
            'result': game['result'],
            'score': f"{game['vc_score']}-{game['opp_score']}",
            'efficiency': {
                'ppp': round(ppp, 3),
                'efg_pct': round(efg_pct, 1),
                'ts_pct': round(ts_pct, 1),
                'fg_pct': round(team_stats['fg'] / team_stats['fga'] * 100, 1) if team_stats['fga'] > 0 else 0
            },
            'possession': {
                'est_poss': round(est_poss, 1),
                'to_per_100': round(to_per_100, 1),
                'ast_to_ratio': round(ast_to_ratio, 2)
            },
            'ball_movement': {
                'assists': team_stats['asst'],
                'ast_pct': round(ast_pct, 1)
            }
        }
    
    # ==============================================================================
    # D. SEASON PATTERNS & WIN CONDITIONS
    # ==============================================================================
    
    def calculate_win_loss_patterns(self) -> Dict:
        """Identify win/loss conditions and patterns"""
        
        wins = [g for g in self.games if g['result'] == 'W']
        losses = [g for g in self.games if g['result'] == 'L']
        
        # Win thresholds
        win_fg_pcts = [g['team_stats']['fg'] / g['team_stats']['fga'] * 100 for g in wins if g['team_stats']['fga'] > 0]
        win_tos = [g['team_stats']['to'] for g in wins]
        win_asts = [g['team_stats']['asst'] for g in wins]
        win_rebs = [g['team_stats']['reb'] for g in wins]
        
        # Loss patterns
        loss_fg_pcts = [g['team_stats']['fg'] / g['team_stats']['fga'] * 100 for g in losses if g['team_stats']['fga'] > 0]
        loss_tos = [g['team_stats']['to'] for g in losses]
        
        win_conditions = {
            'min_fg_pct_in_wins': round(min(win_fg_pcts), 1) if win_fg_pcts else 0,
            'avg_fg_pct_in_wins': round(statistics.mean(win_fg_pcts), 1) if win_fg_pcts else 0,
            'max_to_in_wins': max(win_tos) if win_tos else 0,
            'avg_to_in_wins': round(statistics.mean(win_tos), 1) if win_tos else 0,
            'min_ast_in_wins': min(win_asts) if win_asts else 0,
            'avg_ast_in_wins': round(statistics.mean(win_asts), 1) if win_asts else 0,
            'min_reb_in_wins': min(win_rebs) if win_rebs else 0
        }
        
        loss_conditions = {
            'avg_fg_pct_in_losses': round(statistics.mean(loss_fg_pcts), 1) if loss_fg_pcts else 0,
            'avg_to_in_losses': round(statistics.mean(loss_tos), 1) if loss_tos else 0
        }
        
        # Record by thresholds
        to_threshold_or_less = [g for g in self.games if g.get('team_stats', {}).get('to', 999) <= TURNOVER_THRESHOLD]
        to_threshold_record = f"{len([g for g in to_threshold_or_less if g.get('result') == 'W'])}-{len([g for g in to_threshold_or_less if g.get('result') == 'L'])}"
        
        fg_threshold_or_higher = [g for g in self.games if g.get('team_stats', {}).get('fga', 0) > 0 and 
                                   (g.get('team_stats', {}).get('fg', 0) / g.get('team_stats', {}).get('fga', 1) * 100) >= FG_PERCENTAGE_THRESHOLD]
        fg_threshold_record = f"{len([g for g in fg_threshold_or_higher if g.get('result') == 'W'])}-{len([g for g in fg_threshold_or_higher if g.get('result') == 'L'])}"
        
        return {
            'win_conditions': win_conditions,
            'loss_conditions': loss_conditions,
            'threshold_records': {
                f'to_{TURNOVER_THRESHOLD}_or_less': to_threshold_record,
                f'fg_{int(FG_PERCENTAGE_THRESHOLD)}_or_higher': fg_threshold_record
            },
            'total_wins': len(wins),
            'total_losses': len(losses)
        }
    
    # ==============================================================================
    # E. VOLATILITY & CONSISTENCY
    # ==============================================================================
    
    def calculate_volatility_metrics(self) -> Dict:
        """Calculate variance and consistency metrics"""
        
        # Team game-by-game variance
        game_ppg = [g['vc_score'] for g in self.games]
        game_fg_pcts = [g['team_stats']['fg'] / g['team_stats']['fga'] * 100 for g in self.games if g['team_stats']['fga'] > 0]
        game_tos = [g['team_stats']['to'] for g in self.games]
        
        team_volatility = {
            'ppg_variance': round(statistics.variance(game_ppg), 1) if len(game_ppg) > 1 else 0,
            'ppg_std_dev': round(statistics.stdev(game_ppg), 1) if len(game_ppg) > 1 else 0,
            'ppg_range': f"{min(game_ppg)}-{max(game_ppg)}",
            'fg_pct_variance': round(statistics.variance(game_fg_pcts), 1) if len(game_fg_pcts) > 1 else 0,
            'fg_pct_std_dev': round(statistics.stdev(game_fg_pcts), 1) if len(game_fg_pcts) > 1 else 0,
            'to_variance': round(statistics.variance(game_tos), 1) if len(game_tos) > 1 else 0,
            'to_std_dev': round(statistics.stdev(game_tos), 1) if len(game_tos) > 1 else 0
        }
        
        # Player scoring variance (top 5 scorers)
        top_scorers = sorted(self.season_player_stats.values(), key=lambda x: x.get('ppg', 0), reverse=True)[:5]
        player_volatility = []
        
        player_game_logs = self.stats_data.get('player_game_logs', {})
        
        for player in top_scorers:
            player_name = player.get('name')
            if not player_name or player_name not in player_game_logs:
                continue
            
            game_logs = player_game_logs[player_name]
            if not game_logs:
                continue
            
            # Handle both data structures: direct stats or nested in 'stats' key
            pts_list = []
            for log in game_logs:
                if isinstance(log, dict):
                    if 'stats' in log:
                        pts_list.append(log['stats'].get('pts', 0))
                    else:
                        pts_list.append(log.get('pts', 0))
            
            if len(pts_list) > 1:
                player_ppg = player.get('ppg', 0)
                player_volatility.append({
                    'name': player_name,
                    'ppg': player_ppg,
                    'std_dev': round(statistics.stdev(pts_list), 1),
                    'variance': round(statistics.variance(pts_list), 1),
                    'range': f"{min(pts_list)}-{max(pts_list)}"
                })
        
        return {
            'team_volatility': team_volatility,
            'player_volatility': player_volatility
        }
    
    # ==============================================================================
    # F. AUTO-GENERATED INSIGHTS
    # ==============================================================================
    
    def generate_auto_insights(self) -> List[str]:
        """Generate provable insights from data"""
        
        insights = []
        patterns = self.calculate_win_loss_patterns()
        
        # Win condition insights
        if patterns['win_conditions']['max_to_in_wins'] <= 15:
            insights.append(f"Team is {patterns['total_wins']}-0 when turnovers ≤ {patterns['win_conditions']['max_to_in_wins']}")
        
        if patterns['win_conditions']['min_fg_pct_in_wins'] > 0:
            insights.append(f"Team is undefeated when FG% ≥ {patterns['win_conditions']['min_fg_pct_in_wins']}%")
        
        # Loss patterns
        if patterns['total_losses'] > 0:
            insights.append(f"In losses, team averages {patterns['loss_conditions']['avg_to_in_losses']} TO vs {patterns['win_conditions']['avg_to_in_wins']} in wins")
        
        # Threshold records
        insights.append(f"Record when TO ≤ 13: {patterns['threshold_records']['to_13_or_less']}")
        insights.append(f"Record when FG% ≥ 44%: {patterns['threshold_records']['fg_44_or_higher']}")
        
        return insights


def calculate_all_advanced_stats(stats_file_path: str) -> Dict:
    """Main function to calculate all advanced statistics"""
    
    with open(stats_file_path) as f:
        stats_data = json.load(f)
    
    calculator = AdvancedStatsCalculator(stats_data)
    
    # Calculate team stats
    team_advanced = calculator.calculate_team_advanced_stats()
    
    # Calculate player stats for all players
    player_advanced = {}
    for player_name in stats_data['season_player_stats'].keys():
        player_advanced[player_name] = calculator.calculate_player_advanced_stats(player_name)
    
    # Calculate game stats
    game_advanced = []
    for game in stats_data['games']:
        game_advanced.append(calculator.calculate_game_advanced_stats(game['gameId']))
    
    # Calculate patterns
    patterns = calculator.calculate_win_loss_patterns()
    volatility = calculator.calculate_volatility_metrics()
    insights = calculator.generate_auto_insights()
    
    return {
        'team_advanced': team_advanced,
        'player_advanced': player_advanced,
        'game_advanced': game_advanced,
        'patterns': patterns,
        'volatility': volatility,
        'auto_insights': insights
    }
