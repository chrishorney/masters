"""End-to-end workflow tests."""
import pytest
from datetime import date
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Tournament, Participant, Entry, DailyScore, ScoreSnapshot, Player
from app.services.data_sync import DataSyncService
from app.services.score_calculator import ScoreCalculatorService
from app.services.import_service import ImportService


@pytest.fixture
def db():
    """Database session."""
    from app.database import Base
    db = SessionLocal()
    try:
        # Create all tables for testing
        Base.metadata.create_all(bind=db.bind)
        yield db
        # Clean up
        Base.metadata.drop_all(bind=db.bind)
    finally:
        db.close()


def test_complete_workflow(db: Session):
    """Test complete workflow: tournament sync -> import entries -> calculate scores."""
    
    # Step 1: Create tournament
    tournament = Tournament(
        year=2024,
        tourn_id="TEST_E2E",
        org_id="1",
        name="E2E Test Tournament",
        start_date=date(2024, 4, 11),
        end_date=date(2024, 4, 14),
        status="Official",
        current_round=1
    )
    db.add(tournament)
    db.commit()
    db.refresh(tournament)
    
    # Step 2: Create test players
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
    
    # Step 3: Import entries via ImportService
    import_service = ImportService(db)
    entries_csv = [{
        "Participant Name": "E2E Test Participant",
        "Player 1 Name": "Collin Morikawa",
        "Player 2 Name": "Sam Burns",
        "Player 3 Name": "Peter Malnati",
        "Player 4 Name": "Cameron Young",
        "Player 5 Name": "Test Player1",
        "Player 6 Name": "Test Player2"
    }]
    
    import_result = import_service.import_entries(entries_csv, tournament.id)
    assert import_result["success"] is True
    assert import_result["imported"] == 1
    
    # Step 4: Create leaderboard snapshot
    leaderboard_data = {
        "leaderboardRows": [
            {"playerId": "50525", "position": "1", "status": "complete", "currentRoundScore": "-5"},
            {"playerId": "47504", "position": "2", "status": "complete", "currentRoundScore": "-4"},
            {"playerId": "34466", "position": "5", "status": "complete", "currentRoundScore": "-3"},
            {"playerId": "57366", "position": "10", "status": "complete", "currentRoundScore": "-2"},
            {"playerId": "12345", "position": "20", "status": "complete", "currentRoundScore": "-1"},
            {"playerId": "67890", "position": "30", "status": "complete", "currentRoundScore": "E"},
        ]
    }
    
    snapshot = ScoreSnapshot(
        tournament_id=tournament.id,
        round_id=1,
        leaderboard_data=leaderboard_data,
        scorecard_data={}
    )
    db.add(snapshot)
    db.commit()
    
    # Step 5: Calculate scores
    calculator = ScoreCalculatorService(db)
    calc_result = calculator.calculate_scores_for_tournament(tournament.id, 1)
    
    assert calc_result["success"] is True
    assert calc_result["entries_processed"] >= 1
    
    # Step 6: Verify scores were created
    entry = db.query(Entry).filter(
        Entry.tournament_id == tournament.id
    ).first()
    
    assert entry is not None
    
    daily_score = db.query(DailyScore).filter(
        DailyScore.entry_id == entry.id,
        DailyScore.round_id == 1
    ).first()
    
    assert daily_score is not None
    assert daily_score.total_points > 0
    
    # Expected: 8 + 5 + 5 + 3 + 1 + 0 = 22 base points
    # Plus low score bonus = 1 point
    # Total = 23 points
    assert daily_score.base_points == 22.0
    assert daily_score.total_points >= 22.0


def test_rebuy_workflow(db: Session):
    """Test rebuy workflow."""
    # Create tournament and entry first
    tournament = Tournament(
        year=2024,
        tourn_id="TEST_REBUY",
        org_id="1",
        name="Rebuy Test Tournament",
        start_date=date(2024, 4, 11),
        end_date=date(2024, 4, 14),
        status="Official",
        current_round=3  # Weekend round
    )
    db.add(tournament)
    db.commit()
    db.refresh(tournament)
    
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
    
    # Create entry
    participant = Participant(name="Rebuy Test Participant")
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
    
    # Import rebuy
    import_service = ImportService(db)
    rebuy_csv = [{
        "Participant Name": "Rebuy Test Participant",
        "Original Player Name": "Collin Morikawa",
        "Rebuy Player Name": "Scottie Scheffler",
        "Rebuy Type": "missed_cut"
    }]
    
    rebuy_result = import_service.import_rebuys(rebuy_csv, tournament.id)
    assert rebuy_result["success"] is True
    assert rebuy_result["imported"] == 1
    
    # Verify rebuy was applied
    db.refresh(entry)
    assert "50525" in (entry.rebuy_original_player_ids or [])
    assert "99999" in (entry.rebuy_player_ids or [])
    assert entry.rebuy_type == "missed_cut"


def test_bonus_points_workflow(db: Session):
    """Test manual bonus points workflow."""
    # Setup tournament and entry
    tournament = Tournament(
        year=2024,
        tourn_id="TEST_BONUS",
        org_id="1",
        name="Bonus Test Tournament",
        start_date=date(2024, 4, 11),
        end_date=date(2024, 4, 14),
        status="Official",
        current_round=1
    )
    db.add(tournament)
    db.commit()
    db.refresh(tournament)
    
    player = Player(
        player_id="50525",
        first_name="Collin",
        last_name="Morikawa",
        full_name="Collin Morikawa"
    )
    db.add(player)
    db.commit()
    
    participant = Participant(name="Bonus Test Participant")
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
    
    # Add manual bonus point
    from app.models import BonusPoint
    bonus = BonusPoint(
        entry_id=entry.id,
        round_id=1,
        bonus_type="gir_leader",
        points=1.0,
        player_id="50525"
    )
    db.add(bonus)
    db.commit()
    
    # Create snapshot and calculate scores
    snapshot = ScoreSnapshot(
        tournament_id=tournament.id,
        round_id=1,
        leaderboard_data={
            "leaderboardRows": [
                {"playerId": "50525", "position": "1", "status": "complete"}
            ]
        },
        scorecard_data={}
    )
    db.add(snapshot)
    db.commit()
    
    # Recalculate scores (should include manual bonus)
    from app.services.scoring import ScoringService
    scoring_service = ScoringService(db)
    
    daily_score = scoring_service.calculate_and_save_daily_score(
        entry=entry,
        tournament=tournament,
        leaderboard_data=snapshot.leaderboard_data,
        scorecard_data={},
        round_id=1,
        score_date=tournament.start_date
    )
    
    # Verify bonus is included
    assert daily_score.bonus_points >= 1.0
