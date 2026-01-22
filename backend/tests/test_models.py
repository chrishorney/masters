"""Test database models."""
import pytest
from datetime import date, datetime
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import (
    Tournament,
    Participant,
    Player,
    Entry,
    ScoreSnapshot,
    DailyScore,
    BonusPoint,
)


def test_create_tournament(db: Session):
    """Test creating a tournament."""
    tournament = Tournament(
        year=2024,
        tourn_id="475",
        org_id="1",
        name="Masters Tournament",
        start_date=date(2024, 4, 11),
        end_date=date(2024, 4, 14),
        status="Official",
        current_round=4
    )
    db.add(tournament)
    db.commit()
    db.refresh(tournament)
    
    assert tournament.id is not None
    assert tournament.name == "Masters Tournament"
    assert tournament.year == 2024


def test_create_participant(db: Session):
    """Test creating a participant."""
    participant = Participant(
        name="John Smith",
        email="john@example.com",
        paid=True
    )
    db.add(participant)
    db.commit()
    db.refresh(participant)
    
    assert participant.id is not None
    assert participant.name == "John Smith"
    assert participant.paid is True


def test_create_player(db: Session):
    """Test creating a player."""
    player = Player(
        player_id="50525",
        first_name="Collin",
        last_name="Morikawa",
        full_name="Collin Morikawa"
    )
    db.add(player)
    db.commit()
    db.refresh(player)
    
    assert player.id is not None
    assert player.full_name == "Collin Morikawa"
    assert player.player_id == "50525"


def test_create_entry(db: Session):
    """Test creating an entry with relationships."""
    # Create tournament and participant first
    tournament = Tournament(
        year=2024,
        tourn_id="475",
        org_id="1",
        name="Masters Tournament",
        start_date=date(2024, 4, 11),
        end_date=date(2024, 4, 14),
        status="Official"
    )
    db.add(tournament)
    
    participant = Participant(
        name="John Smith",
        email="john@example.com"
    )
    db.add(participant)
    db.commit()
    
    # Create entry
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
    
    assert entry.id is not None
    assert entry.participant_id == participant.id
    assert entry.tournament_id == tournament.id
    assert len(entry.player1_id) > 0


def test_entry_relationships(db: Session):
    """Test entry relationships work correctly."""
    tournament = Tournament(
        year=2024,
        tourn_id="475",
        org_id="1",
        name="Masters Tournament",
        start_date=date(2024, 4, 11),
        end_date=date(2024, 4, 14),
        status="Official"
    )
    db.add(tournament)
    
    participant = Participant(name="John Smith")
    db.add(participant)
    db.commit()
    
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
    
    # Test relationships
    assert entry.participant.name == "John Smith"
    assert entry.tournament.name == "Masters Tournament"
    assert len(participant.entries) == 1
    assert len(tournament.entries) == 1
