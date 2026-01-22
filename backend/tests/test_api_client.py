"""Test Slash Golf API client."""
import pytest
from app.services.api_client import SlashGolfAPIClient
from app.config import settings


@pytest.fixture
def api_client():
    """Create API client instance."""
    return SlashGolfAPIClient()


def test_api_client_initialization(api_client):
    """Test API client initializes correctly."""
    assert api_client.api_key == settings.slash_golf_api_key
    assert api_client.api_host == settings.slash_golf_api_host
    assert api_client.base_url == "https://live-golf-data.p.rapidapi.com"


def test_get_tournament(api_client):
    """Test fetching tournament data."""
    data = api_client.get_tournament()
    
    assert "tournId" in data
    assert "name" in data
    assert "year" in data
    assert "date" in data


def test_get_leaderboard(api_client):
    """Test fetching leaderboard data."""
    data = api_client.get_leaderboard()
    
    assert "leaderboardRows" in data
    assert isinstance(data["leaderboardRows"], list)
    
    # Check first row has required fields
    if len(data["leaderboardRows"]) > 0:
        row = data["leaderboardRows"][0]
        assert "playerId" in row
        assert "firstName" in row
        assert "lastName" in row


def test_get_schedule(api_client):
    """Test fetching schedule data."""
    data = api_client.get_schedule()
    
    assert "schedule" in data
    assert isinstance(data["schedule"], list)
    
    # Check first tournament has required fields
    if len(data["schedule"]) > 0:
        tournament = data["schedule"][0]
        assert "tournId" in tournament
        assert "name" in tournament


def test_get_scorecard(api_client):
    """Test fetching scorecard data."""
    # Use a known player ID from the test data
    # Use tournament 475 (Valspar Championship 2024) where this player participated
    player_id = "47504"  # Sam Burns from test data
    data = api_client.get_scorecard(
        player_id,
        tourn_id="475",
        year=2024
    )
    
    assert isinstance(data, list)
    # Each item should be a round
    if len(data) > 0:
        round_data = data[0]
        assert "playerId" in round_data
        assert "roundId" in round_data


def test_find_tournament_by_name(api_client):
    """Test finding tournament by name."""
    # This will search the schedule
    tournament = api_client.find_tournament_by_name("Masters")
    
    # Should return a tournament dict or None
    assert tournament is None or isinstance(tournament, dict)
