"""Validate that all HIO/eagle/double_eagle bonuses trigger Discord notification."""
import pytest
from datetime import date
from unittest.mock import patch, MagicMock

from app.services.scoring import ScoringService
from app.models import Tournament, Participant, Entry, Player


@pytest.fixture
def tournament(db):
    t = Tournament(
        year=2024,
        tourn_id="475",
        org_id="1",
        name="Test Tournament",
        start_date=date(2024, 4, 11),
        end_date=date(2024, 4, 14),
        status="Official",
        current_round=1,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@pytest.fixture
def entry(db, tournament):
    p = Participant(name="Test Participant")
    db.add(p)
    db.commit()
    e = Entry(
        participant_id=p.id,
        tournament_id=tournament.id,
        player1_id="50525",
        player2_id="47504",
        player3_id="34466",
        player4_id="57366",
        player5_id="12345",
        player6_id="67890",
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    return e


@pytest.fixture
def player_50525(db):
    pl = Player(
        player_id="50525",
        first_name="Test",
        last_name="Golfer",
        full_name="Test Golfer",
    )
    db.add(pl)
    db.commit()
    return pl


def test_hole_in_one_bonus_triggers_discord_notification(db, tournament, entry, player_50525):
    """When a new hole-in-one bonus is created, Discord notification must be sent."""
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
    # Scorecard: player 50525 has a hole-in-one on hole 5 (par 3) in round 1
    scorecard_data = {
        "50525": [
            {
                "roundId": 1,
                "holes": {
                    "5": {"holeScore": 1, "par": 3},
                },
            }
        ],
    }

    scoring_service = ScoringService(db)
    with patch.object(
        scoring_service,
        "_notify_discord_bonus_async",
        wraps=MagicMock(),
    ) as mock_discord:
        scoring_service.calculate_and_save_daily_score(
            entry=entry,
            tournament=tournament,
            leaderboard_data=leaderboard_data,
            scorecard_data=scorecard_data,
            round_id=1,
            score_date=tournament.start_date,
        )

    assert mock_discord.called, "Discord notification should be sent when a new hole-in-one bonus is created"
    call_args = mock_discord.call_args
    assert call_args[0][1]["bonus_type"] == "hole_in_one"
    assert call_args[0][1].get("hole") == 5
    assert call_args[0][1].get("player_id") == "50525"
