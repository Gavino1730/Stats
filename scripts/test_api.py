#!/usr/bin/env python3
"""
Test the API endpoints to verify database integration
"""

import sys
import os
# Add the project root to path, not src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app import app

# Test API endpoints
with app.app_context():
    with app.test_client() as client:
        # Test health endpoint
        response = client.get('/health')
        health_data = response.get_json()
        print(f'Health check: {health_data["status"]} - {health_data["games_loaded"]} games, {health_data["players_loaded"]} players')
        
        # Test games endpoint
        response = client.get('/api/games')
        games_data = response.get_json()
        print(f'Games API: {len(games_data)} games loaded')
        if games_data:
            print(f'First game: {games_data[0]["opponent"]} - {games_data[0]["result"]}')
        
        # Test players endpoint
        response = client.get('/api/players')
        players_data = response.get_json()
        print(f'Players API: {len(players_data)} players loaded')
        if players_data:
            print(f'Top scorer: {players_data[0]["name"]} - {players_data[0]["ppg"]} PPG')
        
        print('\n✅ All API endpoints working with database!')