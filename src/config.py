"""
Configuration file for basketball stats application
Centralizes all magic numbers and configuration constants
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        # Fix Railway's postgres:// to postgresql://
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///basketball_stats.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Database engine options - conditional based on database type
    if DATABASE_URL and ('postgresql' in DATABASE_URL or 'postgres' in DATABASE_URL):
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
            'connect_args': {
                'connect_timeout': 10,
                'sslmode': 'prefer'
            }
        }
    else:
        # SQLite or other databases
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,
        }
    
    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    
    # App
    JSON_SORT_KEYS = False
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 year cache for static files
    COMPRESS_LEVEL = 6  # Gzip compression

# API Configuration
# Model selection based on task complexity and cost
OPENAI_MODEL_ANALYSIS = "gpt-4o"      # For diagnostic analysis, coach-style commentary
OPENAI_MODEL_CARDS = "gpt-4o-mini"      # For game cards, structured summaries, rankings
OPENAI_MODEL_TAGS = "gpt-4o-mini"       # For quick classifications, tags, formatting
OPENAI_TIMEOUT = 30
OPENAI_MAX_RETRIES = 3

# Server Configuration
GUNICORN_TIMEOUT = 600  # 10 minutes for long-running analysis
GUNICORN_WORKERS = 2
GUNICORN_KEEP_ALIVE = 5

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
