#!/usr/bin/env python3
"""
Test script to verify database setup works correctly
Run this before deploying to make sure everything is working
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from flask import Flask
from models import db, Game, Player, PlayerGameStats, SeasonStats
from config import Config

def test_database():
    """Test database connection and basic operations"""
    print("Testing database setup...")
    
    # Create test app
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Override database URL for local testing with SQLite
    if not app.config.get('DATABASE_URL'):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    
    db.init_app(app)
    
    with app.app_context():
        try:
            # Create tables
            print("Creating database tables...")
            db.create_all()
            print("✅ Tables created successfully")
            
            # Test basic queries
            print("Testing queries...")
            players_count = Player.query.count()
            games_count = Game.query.count()
            print(f"✅ Queries work - Players: {players_count}, Games: {games_count}")
            
            # Test creating a sample record
            print("Testing record creation...")
            test_player = Player.query.filter_by(name="Test Player").first()
            if not test_player:
                test_player = Player(
                    name="Test Player",
                    number=99,
                    grade="Test",
                    games=1,
                    pts=10,
                    ppg=10.0
                )
                db.session.add(test_player)
                db.session.commit()
                print("✅ Record creation successful")
            else:
                print("✅ Test record already exists")
            
            # Clean up test record
            db.session.delete(test_player)
            db.session.commit()
            print("✅ Record deletion successful")
            
            print("\n🎉 Database setup test completed successfully!")
            return True
            
        except Exception as e:
            print(f"\n❌ Database test failed: {e}")
            return False

if __name__ == '__main__':
    success = test_database()
    sys.exit(0 if success else 1)