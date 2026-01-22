"""Test admin bonus points endpoints."""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from app.main import app
from app.models import Tournament, Participant, Entry, ScoreSnapshot

client = TestClient(app)


@pytest.fixture
def test_tournament(db):
    """Create test tournament."""
    tournament = Tournament(
        year=2024,
        tourn_id="TEST",
        org_id="1",
        name="Test Tournament",
        start_date=date(2024, 4, 11),
        end_date=date(2024, 4, 14),
        status="Official",
        current_round=1
    )
    db.add(tournament)
    db.commit()
    db.refresh(tournament)
    return tournament


@pytest.fixture
def test_entry(db, test_tournament):
    """Create test entry."""
    participant = Participant(name="Test Participant")
    db.add(participant)
    db.commit()
    
    entry = Entry(
        participant_id=participant.id,
        tournament_id=test_tournament.id,
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


@pytest.fixture
def test_snapshot(db, test_tournament):
    """Create test snapshot."""
    snapshot = ScoreSnapshot(
        tournament_id=test_tournament.id,
        round_id=1,
        leaderboard_data={
            "leaderboardRows": [
                {"playerId": "50525", "position": "1", "status": "complete"},
                {"playerId": "47504", "position": "2", "status": "complete"},
            ]
        },
        scorecard_data={}
    )
    db.add(snapshot)
    db.commit()
    return snapshot


def test_add_gir_bonus_point(db, test_tournament, test_entry, test_snapshot):
    """Test adding a GIR leader bonus point."""
    response = client.post(
        "/api/admin/bonus-points/add",
        json={
            "tournament_id": test_tournament.id,
            "round_id": 1,
            "player_id": "50525",
            "bonus_type": "gir_leader",
            "points": 1.0
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["bonus_type"] == "gir_leader"
    assert data["entries_found"] >= 1
    assert data["bonus_points_created"] >= 1


def test_add_fairways_bonus_point(db, test_tournament, test_entry, test_snapshot):
    """Test adding a fairways leader bonus point."""
    response = client.post(
        "/api/admin/bonus-points/add",
        json={
            "tournament_id": test_tournament.id,
            "round_id": 1,
            "player_id": "47504",
            "bonus_type": "fairways_leader",
            "points": 1.0
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["bonus_type"] == "fairways_leader"


def test_list_bonus_points(db, test_tournament, test_entry):
    """Test listing bonus points."""
    # First add one
    client.post(
        "/api/admin/bonus-points/add",
        json={
            "tournament_id": test_tournament.id,
            "round_id": 1,
            "player_id": "50525",
            "bonus_type": "gir_leader"
        }
    )
    
    # Then list them
    response = client.get(
        f"/api/admin/bonus-points/list?tournament_id={test_tournament.id}&round_id=1"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "bonus_points" in data
    assert len(data["bonus_points"]) >= 1
