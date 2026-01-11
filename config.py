"""
Configuration file for basketball stats application
Centralizes all magic numbers and configuration constants
"""

# API Configuration
OPENAI_MODEL = "gpt-4o"
OPENAI_TIMEOUT = 30
OPENAI_MAX_RETRIES = 3

# Analysis Configuration
MAX_TOKENS_GAME_ANALYSIS = 800
MAX_TOKENS_PLAYER_ANALYSIS = 1000
MAX_TOKENS_TEAM_SUMMARY = 2000
MAX_TOKENS_SEASON_ANALYSIS = 1500

# Basketball Statistics Constants
FREE_THROW_POSSESSION_FACTOR = 0.44
THREE_POINT_MULTIPLIER = 0.5
PRIMARY_SCORER_THRESHOLD = 20.0  # percentage
SECONDARY_SCORER_THRESHOLD = 10.0  # percentage
TURNOVER_THRESHOLD = 13
FG_PERCENTAGE_THRESHOLD = 44.0

# Performance Thresholds
PPG_PERFORMANCE_THRESHOLD = 1.0  # Points above/below average to be significant
MIN_GAMES_FOR_VARIANCE = 2
MIN_FGA_FOR_PERCENTAGE = 1  # Minimum attempts to calculate percentages

# Excluded Players (players not to analyze)
EXCLUDED_PLAYERS = {
    'Matthew Gunther',
    'Liam Plep',
    'Gavin Galan',
    'Kye Fixter'
}

# File Paths
STATS_FILE = 'vc_stats_output.json'
ROSTER_FILE = 'roster.json'
ANALYSIS_CACHE_FILE = 'season_analysis.json'
PLAYER_ANALYSIS_CACHE_FILE = 'player_analysis_cache.json'
TEAM_SUMMARY_CACHE = 'team_summary.json'

# Flask Configuration
FLASK_JSON_SORT_KEYS = False
FLASK_STATIC_CACHE_MAX_AGE = 31536000  # 1 year
FLASK_COMPRESS_LEVEL = 6

# Validation Constants
MAX_PLAYER_NAME_LENGTH = 100
MAX_QUERY_LENGTH = 1000

# Leaderboard Settings
LEADERBOARD_SIZE = 10
TOP_SCORERS_COUNT = 5

# Cache Settings
USE_CACHE = True
CACHE_ENABLED = True
