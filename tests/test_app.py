"""
Basic tests for the basketball stats application
"""

import pytest
from src.app import app


def test_app_exists():
    """Test that the app exists"""
    assert app is not None


def test_home_page():
    """Test that the home page loads"""
    with app.test_client() as client:
        response = client.get("/")
        assert response.status_code == 200


def test_api_games():
    """Test that the games API endpoint works"""
    with app.test_client() as client:
        response = client.get("/api/games")
        assert response.status_code == 200
        assert isinstance(response.get_json(), list)


def test_api_players():
    """Test that the players API endpoint works"""
    with app.test_client() as client:
        response = client.get("/api/players")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)


def test_api_season_stats():
    """Test that the season stats API endpoint works"""
    with app.test_client() as client:
        response = client.get("/api/season-stats")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, dict)
