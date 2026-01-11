import json
import sys

print("Starting test...", flush=True)

# Load the data
with open('vc_stats_output.json') as f:
    stats_data = json.load(f)
print("Data loaded", flush=True)

# Try to calculate volatility manually
games = stats_data['games']
print(f"Number of games: {len(games)}")

# Get vc_scores
game_ppg = [g['vc_score'] for g in games]
print(f"VC Scores: {game_ppg}")

# Get FG percentages
game_fg_pcts = [g['team_stats']['fg'] / g['team_stats']['fga'] * 100 for g in games if g['team_stats']['fga'] > 0]
print(f"FG Percentages: {[f'{pct:.1f}' for pct in game_fg_pcts]}")

# Get turnovers
game_tos = [g['team_stats']['to'] for g in games]
print(f"Turnovers: {game_tos}")

# Calculate the metrics
import statistics
ppg_range = f"{min(game_ppg)}-{max(game_ppg)}"
fg_std = round(statistics.stdev(game_fg_pcts), 1) if len(game_fg_pcts) > 1 else 0
to_std = round(statistics.stdev(game_tos), 1) if len(game_tos) > 1 else 0

print(f"\nResults:")
print(f"PPG Range: {ppg_range}")
print(f"FG% Std Dev: {fg_std}%")
print(f"TO Std Dev: {to_std}")
