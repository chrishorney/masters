"""Tests for import service."""
import pytest
from datetime import date
from app.services.import_service import ImportService
from app.models import Tournament, Participant, Entry, Player, ScoreSnapshot


def test_parse_csv():
    """Test CSV parsing."""
    csv_content = b"""Participant Name,Player 1 Name,Player 2 Name,Player 3 Name,Player 4 Name,Player 5 Name,Player 6 Name
John Smith,Tiger Woods,Phil Mickelson,Rory McIlroy,Jordan Spieth,Dustin Johnson,Brooks Koepka
Jane Doe,Scottie Scheffler,Jon Rahm,Collin Morikawa,Xander Schauffele,Patrick Cantlay,Viktor Hovland"""
    
    db = None  # Will be provided by fixture
    service = ImportService(db)
    rows = service.parse_csv(csv_content)
    
    assert len(rows) == 2
    assert rows[0]["Participant Name"] == "John Smith"
    assert rows[0]["Player 1 Name"] == "Tiger Woods"
    assert rows[1]["Participant Name"] == "Jane Doe"


def test_validate_entries_columns(db):
    """Test entries column validation."""
    service = ImportService(db)
    
    # Valid columns
    valid_rows = [{
        "Participant Name": "John",
        "Player 1 Name": "Tiger",
        "Player 2 Name": "Phil",
        "Player 3 Name": "Rory",
        "Player 4 Name": "Jordan",
        "Player 5 Name": "Dustin",
        "Player 6 Name": "Brooks"
    }]
    is_valid, error = service.validate_entries_columns(valid_rows)
    assert is_valid is True
    assert error is None
    
    # Missing columns
    invalid_rows = [{"Participant Name": "John"}]
    is_valid, error = service.validate_entries_columns(invalid_rows)
    assert is_valid is False
    assert "Missing required columns" in error


def test_validate_rebuys_columns(db):
    """Test rebuys column validation."""
    service = ImportService(db)
    
    # Valid columns
    valid_rows = [{
        "Participant Name": "John",
        "Original Player Name": "Tiger",
        "Rebuy Player Name": "Scottie",
        "Rebuy Type": "missed_cut"
    }]
    is_valid, error = service.validate_rebuys_columns(valid_rows)
    assert is_valid is True
    
    # Missing columns
    invalid_rows = [{"Participant Name": "John"}]
    is_valid, error = service.validate_rebuys_columns(invalid_rows)
    assert is_valid is False


def test_match_player_name(db):
    """Test player name matching."""
    # Create test player
    player = Player(
        player_id="50525",
        first_name="Collin",
        last_name="Morikawa",
        full_name="Collin Morikawa"
    )
    db.add(player)
    db.commit()
    
    service = ImportService(db)
    
    # Exact match
    player_id = service.match_player_name("Collin Morikawa", 1)
    assert player_id == "50525"
    
    # Case insensitive
    player_id = service.match_player_name("collin morikawa", 1)
    assert player_id == "50525"
    
    # Not found
    player_id = service.match_player_name("Unknown Player", 1)
    assert player_id is None


def test_import_entries(db):
    """Test importing entries."""
    # Create tournament
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
    
    # Create players
    players_data = [
        ("50525", "Collin", "Morikawa", "Collin Morikawa"),
        ("47504", "Sam", "Burns", "Sam Burns"),
        ("34466", "Peter", "Malnati", "Peter Malnati"),
        ("57366", "Cameron", "Young", "Cameron Young"),
        ("12345", "Test", "Player1", "Test Player1"),
        ("67890", "Test", "Player2", "Test Player2"),
    ]
    
    for pid, first, last, full in players_data:
        player = Player(
            player_id=pid,
            first_name=first,
            last_name=last,
            full_name=full
        )
        db.add(player)
    db.commit()
    
    # Create CSV rows
    rows = [{
        "Participant Name": "John Smith",
        "Player 1 Name": "Collin Morikawa",
        "Player 2 Name": "Sam Burns",
        "Player 3 Name": "Peter Malnati",
        "Player 4 Name": "Cameron Young",
        "Player 5 Name": "Test Player1",
        "Player 6 Name": "Test Player2"
    }]
    
    service = ImportService(db)
    results = service.import_entries(rows, tournament.id)
    
    assert results["success"] is True
    assert results["imported"] == 1
    assert results["skipped"] == 0
    
    # Verify entry was created
    participant = db.query(Participant).filter(
        Participant.name == "John Smith"
    ).first()
    assert participant is not None
    
    entry = db.query(Entry).filter(
        Entry.participant_id == participant.id,
        Entry.tournament_id == tournament.id
    ).first()
    assert entry is not None
    assert entry.player1_id == "50525"


def test_import_rebuys(db):
    """Test importing rebuys."""
    # Create tournament and entry first
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
    
    participant = Participant(name="John Smith")
    db.add(participant)
    db.commit()
    db.refresh(participant)
    
    entry = Entry(
        participant_id=participant.id,
        tournament_id=tournament.id,
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
    
    # Create players
    players_data = [
        ("50525", "Collin", "Morikawa", "Collin Morikawa"),
        ("99999", "Scottie", "Scheffler", "Scottie Scheffler"),
    ]
    
    for pid, first, last, full in players_data:
        player = Player(
            player_id=pid,
            first_name=first,
            last_name=last,
            full_name=full
        )
        db.add(player)
    db.commit()
    
    # Create rebuy rows
    rows = [{
        "Participant Name": "John Smith",
        "Original Player Name": "Collin Morikawa",
        "Rebuy Player Name": "Scottie Scheffler",
        "Rebuy Type": "missed_cut"
    }]
    
    service = ImportService(db)
    results = service.import_rebuys(rows, tournament.id)
    
    assert results["success"] is True
    assert results["imported"] == 1
    
    # Verify rebuy was applied - need to query fresh from DB
    db.refresh(entry)
    # Handle case where arrays might be None or empty list
    rebuy_original = entry.rebuy_original_player_ids or []
    rebuy_players = entry.rebuy_player_ids or []
    
    assert "50525" in rebuy_original, f"Expected 50525 in {rebuy_original}"
    assert "99999" in rebuy_players, f"Expected 99999 in {rebuy_players}"
    assert entry.rebuy_type == "missed_cut"
