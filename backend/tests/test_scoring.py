"""Test scoring service."""
import pytest
from datetime import date
from app.services.scoring import ScoringService
from app.models import Tournament, Participant, Entry, Player


@pytest.fixture
def sample_tournament(db):
    """Create a sample tournament."""
    tournament = Tournament(
        year=2024,
        tourn_id="475",
        org_id="1",
        name="Test Tournament",
        start_date=date(2024, 4, 11),
        end_date=date(2024, 4, 14),
        status="Official",
        current_round=4
    )
    db.add(tournament)
    db.commit()
    db.refresh(tournament)
    return tournament


@pytest.fixture
def sample_entry(db, sample_tournament):
    """Create a sample entry."""
    participant = Participant(name="Test Participant")
    db.add(participant)
    db.commit()
    
    entry = Entry(
        participant_id=participant.id,
        tournament_id=sample_tournament.id,
        player1_id="50525",
        player2_id="47504",
        player3_id="34466",
        player4_id="57366",
        player5_id="12345",
        player6_id="67890"
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def test_calculate_position_points_round1(scoring_service):
    """Test position points for Round 1 (Thursday)."""
    # Leader
    assert scoring_service.calculate_position_points("1", 1) == 8.0
    # Top 5
    assert scoring_service.calculate_position_points("2", 1) == 5.0
    assert scoring_service.calculate_position_points("5", 1) == 5.0
    # Top 10
    assert scoring_service.calculate_position_points("6", 1) == 3.0
    assert scoring_service.calculate_position_points("10", 1) == 3.0
    # Top 25
    assert scoring_service.calculate_position_points("11", 1) == 1.0
    assert scoring_service.calculate_position_points("25", 1) == 1.0
    # Outside top 25
    assert scoring_service.calculate_position_points("26", 1) == 0.0


def test_calculate_position_points_round2(scoring_service):
    """Test position points for Round 2 (Friday)."""
    # Leader
    assert scoring_service.calculate_position_points("1", 2) == 12.0
    # Top 5
    assert scoring_service.calculate_position_points("3", 2) == 8.0
    # Top 10
    assert scoring_service.calculate_position_points("7", 2) == 5.0
    # Top 25
    assert scoring_service.calculate_position_points("20", 2) == 3.0
    # Made cut, outside top 25
    assert scoring_service.calculate_position_points("30", 2) == 1.0


def test_calculate_position_points_round4_winner(scoring_service):
    """Test position points for Round 4 (Sunday) - winner."""
    # Winner gets 15 points
    assert scoring_service.calculate_position_points("1", 4, is_winner=True) == 15.0
    # Leader but not winner
    assert scoring_service.calculate_position_points("1", 4, is_winner=False) == 12.0


def test_calculate_position_points_ties(scoring_service):
    """Test position points with ties."""
    # Tied positions should still work
    assert scoring_service.calculate_position_points("T2", 1) == 5.0
    assert scoring_service.calculate_position_points("T5", 1) == 5.0


def test_calculate_position_points_cut(scoring_service):
    """Test position points for cut players."""
    assert scoring_service.calculate_position_points("cut", 1) == 0.0
    assert scoring_service.calculate_position_points("wd", 2) == 0.0


def test_get_player_position(scoring_service):
    """Test getting player position from leaderboard."""
    leaderboard_data = {
        "leaderboardRows": [
            {"playerId": "50525", "position": "1", "status": "complete"},
            {"playerId": "47504", "position": "T2", "status": "complete"},
            {"playerId": "34466", "position": "5", "status": "complete"},
        ]
    }
    
    assert scoring_service.get_player_position(leaderboard_data, "50525") == "1"
    assert scoring_service.get_player_position(leaderboard_data, "47504") == "T2"
    assert scoring_service.get_player_position(leaderboard_data, "99999") is None


def test_calculate_daily_base_points(scoring_service, sample_entry, sample_tournament):
    """Test calculating daily base points."""
    leaderboard_data = {
        "leaderboardRows": [
            {"playerId": "50525", "position": "1", "status": "complete"},
            {"playerId": "47504", "position": "5", "status": "complete"},
            {"playerId": "34466", "position": "10", "status": "complete"},
            {"playerId": "57366", "position": "20", "status": "complete"},
            {"playerId": "12345", "position": "30", "status": "complete"},
            {"playerId": "67890", "position": "cut", "status": "cut"},
        ]
    }
    
    result = scoring_service.calculate_daily_base_points(
        sample_entry, leaderboard_data, 1, sample_tournament
    )
    
    assert result["total_points"] > 0
    assert "breakdown" in result
    assert len(result["breakdown"]) == 6
    
    # Check individual player points
    assert result["breakdown"]["player1"]["points"] == 8.0  # Leader
    assert result["breakdown"]["player2"]["points"] == 5.0  # Top 5
    assert result["breakdown"]["player3"]["points"] == 3.0  # Top 10
    assert result["breakdown"]["player4"]["points"] == 1.0  # Top 25
    assert result["breakdown"]["player5"]["points"] == 0.0  # Outside top 25 (round 1)
    assert result["breakdown"]["player6"]["points"] == 0.0  # Cut


@pytest.fixture
def scoring_service(db):
    """Create scoring service instance."""
    return ScoringService(db)
