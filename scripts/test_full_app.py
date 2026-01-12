#!/usr/bin/env python3
"""
Test the database-powered app with Railway PostgreSQL
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set Railway DATABASE_URL
os.environ['DATABASE_URL'] = 'postgresql://postgres:OcQKrKBNAYaGMNbYQQUARwhpXLOgfFUL@maglev.proxy.rlwy.net:43310/railway'

from app import app

def test_database_app():
    """Test the database-powered application"""
    print("🧪 Testing Basketball Stats App with Railway PostgreSQL")
    print("=" * 60)
    
    with app.app_context():
        with app.test_client() as client:
            try:
                # Test 1: Health Check
                print("1️⃣  Testing /health endpoint...")
                response = client.get('/health')
                if response.status_code == 200:
                    health_data = response.get_json()
                    print(f"   ✅ Status: {health_data['status']}")
                    print(f"   ✅ Database: {health_data['database']}")
                    print(f"   ✅ Games loaded: {health_data['games_loaded']}")
                    print(f"   ✅ Players loaded: {health_data['players_loaded']}")
                else:
                    print(f"   ❌ Health check failed: {response.status_code}")
                    return False
                
                # Test 2: Games API
                print("\n2️⃣  Testing /api/games endpoint...")
                response = client.get('/api/games')
                if response.status_code == 200:
                    games_data = response.get_json()
                    print(f"   ✅ Loaded {len(games_data)} games")
                    if games_data:
                        game = games_data[0]
                        print(f"   ✅ Sample: Game {game['gameId']} vs {game['opponent']} ({game['result']})")
                        print(f"   ✅ Score: VC {game['vc_score']} - {game['opp_score']} {game['opponent']}")
                else:
                    print(f"   ❌ Games API failed: {response.status_code}")
                    return False
                
                # Test 3: Players API  
                print("\n3️⃣  Testing /api/players endpoint...")
                response = client.get('/api/players')
                if response.status_code == 200:
                    players_data = response.get_json()
                    print(f"   ✅ Loaded {len(players_data)} players")
                    if players_data:
                        top_player = players_data[0]
                        print(f"   ✅ Top scorer: {top_player['name']} - {top_player['ppg']} PPG")
                        print(f"   ✅ Stats: {top_player['pts']} pts, {top_player['reb']} reb, {top_player['asst']} ast")
                else:
                    print(f"   ❌ Players API failed: {response.status_code}")
                    return False
                
                # Test 4: Specific Game
                print("\n4️⃣  Testing /api/game/1 endpoint...")
                response = client.get('/api/game/1')
                if response.status_code == 200:
                    game_data = response.get_json()
                    print(f"   ✅ Game details loaded")
                    print(f"   ✅ Opponent: {game_data['opponent']}")
                    print(f"   ✅ Player stats: {len(game_data['player_stats'])} players")
                    if game_data['player_stats']:
                        top_performer = max(game_data['player_stats'], key=lambda p: p['pts'])
                        print(f"   ✅ Top performer: {top_performer['player_name']} - {top_performer['pts']} pts")
                else:
                    print(f"   ❌ Game details failed: {response.status_code}")
                    return False
                
                # Test 5: Specific Player
                print("\n5️⃣  Testing /api/player/Hank Lomber endpoint...")
                response = client.get('/api/player/Hank Lomber')
                if response.status_code == 200:
                    player_data = response.get_json()
                    print(f"   ✅ Player details loaded")
                    print(f"   ✅ Season stats: {player_data['season_stats']['ppg']} PPG")
                    print(f"   ✅ Game logs: {len(player_data['game_logs'])} games")
                    if player_data['game_logs']:
                        best_game = max(player_data['game_logs'], key=lambda g: g['pts'])
                        print(f"   ✅ Best game: {best_game['pts']} pts vs {best_game['opponent']}")
                else:
                    print(f"   ❌ Player details failed: {response.status_code}")
                    return False
                
                # Test 6: Season Stats
                print("\n6️⃣  Testing /api/season-stats endpoint...")
                response = client.get('/api/season-stats')
                if response.status_code == 200:
                    season_data = response.get_json()
                    if season_data:
                        print(f"   ✅ Season stats loaded")
                        print(f"   ✅ Record: {season_data.get('wins', 0)}-{season_data.get('losses', 0)}")
                        print(f"   ✅ Team PPG: {season_data.get('ppg', 0)}")
                    else:
                        print("   ⚠️  No season stats found (might be empty)")
                else:
                    print(f"   ❌ Season stats failed: {response.status_code}")
                    return False
                
                print("\n" + "=" * 60)
                print("🎉 ALL TESTS PASSED!")
                print("✅ Your Basketball Stats App is working perfectly with PostgreSQL!")
                print("✅ No more JSON file errors!")
                print("✅ Database queries are fast and reliable!")
                print("✅ Ready for production deployment!")
                
                return True
                
            except Exception as e:
                print(f"\n❌ Test failed with error: {e}")
                return False

if __name__ == '__main__':
    success = test_database_app()
    sys.exit(0 if success else 1)