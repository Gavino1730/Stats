#!/usr/bin/env python3
"""
Test Railway PostgreSQL connection
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from flask import Flask
from models import db
from config import Config

# Set your Railway DATABASE_URL for testing
os.environ['DATABASE_URL'] = 'postgresql://postgres:OcQKrKBNAYaGMNbYQQUARwhpXLOgfFUL@maglev.proxy.rlwy.net:43310/railway'

def test_connection():
    """Test connection to Railway PostgreSQL"""
    print("Testing Railway PostgreSQL connection...")
    
    app = Flask(__name__)
    
    # Force PostgreSQL connection for testing
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:OcQKrKBNAYaGMNbYQQUARwhpXLOgfFUL@maglev.proxy.rlwy.net:43310/railway'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {
            'connect_timeout': 10,
            'sslmode': 'prefer'
        }
    }
    
    print(f"Database URL: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
    
    db.init_app(app)
    
    with app.app_context():
        try:
            # Test connection
            db.create_all()
            print("✅ Successfully connected to Railway PostgreSQL!")
            
            # Test basic operations
            result = db.session.execute(db.text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ PostgreSQL version: {version[:50]}...")
            
            print("🎉 Railway database is ready for migration!")
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

if __name__ == '__main__':
    success = test_connection()
    sys.exit(0 if success else 1)