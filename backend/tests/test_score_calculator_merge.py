import pytest
from datetime import date, datetime
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.services.score_calculator import ScoreCalculatorService
from app.services.data_sync import DataSyncService
from app.models import Tournament, Participant, Entry, ScoreSnapshot


@pytest.fixture
def sqlite_db():
    """
    Local, in-memory DB for this test.

    The repo's default test DB fixture points at Supabase, which isn't reachable
    in this sandbox environment.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def tournament_for_score_calc_merge(sqlite_db):
    """Create a minimal tournament with 4 rounds."""
    tournament = Tournament(
        year=2024,
        tourn_id="475",
        org_id="1",
        name="Test Tournament",
        start_date=date(2024, 4, 11),
        end_date=date(2024, 4, 14),
        status="Official",
        current_round=4,
    )
    sqlite_db.add(tournament)
    sqlite_db.commit()
    sqlite_db.refresh(tournament)
    return tournament


@pytest.fixture
def entry_for_score_calc_merge(sqlite_db, tournament_for_score_calc_merge):
    """Create a single entry that includes player1_id used in snapshots."""
    participant = Participant(name="Test Participant")
    sqlite_db.add(participant)
    sqlite_db.commit()

    entry = Entry(
        participant_id=participant.id,
        tournament_id=tournament_for_score_calc_merge.id,
        player1_id="50525",
        player2_id="47504",
        player3_id="34466",
        player4_id="57366",
        player5_id="12345",
        player6_id="67890",
    )
    sqlite_db.add(entry)
    sqlite_db.commit()
    sqlite_db.refresh(entry)
    return entry


def test_merge_scorecards_across_snapshot_rounds_for_target_round(
    sqlite_db, tournament_for_score_calc_merge, entry_for_score_calc_merge, monkeypatch
):
    """
    Regression test:
    A player's Round 1 scorecard can be stored inside a later snapshot (round_id=2)
    because the sync job ran when current_round advanced.

    When calculating bonuses for Round 1, we must still consider that scorecard.
    """
    tournament_id = tournament_for_score_calc_merge.id

    # Round 1 snapshot exists, but doesn't include player1's Round 1 scorecard
    round1_snapshot = ScoreSnapshot(
        tournament_id=tournament_id,
        round_id=1,
        timestamp=datetime(2024, 4, 11, 10, 0, 0),
        leaderboard_data={"leaderboardRows": []},
        scorecard_data={},
    )
    sqlite_db.add(round1_snapshot)

    # Later snapshot (round 2) includes player1's Round 1 scorecard in its payload
    round2_snapshot = ScoreSnapshot(
        tournament_id=tournament_id,
        round_id=2,
        timestamp=datetime(2024, 4, 12, 10, 0, 0),
        leaderboard_data={"leaderboardRows": []},
        scorecard_data={
            "50525": [
                {
                    "roundId": 1,  # internal roundId matches target calculation round
                    "holes": {"9": {"holeScore": 2, "par": 4}},
                }
            ]
        },
    )
    sqlite_db.add(round2_snapshot)
    sqlite_db.commit()

    # Stub out scoring + ranking snapshot side effects.
    captured = {}

    def fake_calculate_and_save_daily_score(
        entry, tournament, leaderboard_data, scorecard_data, round_id, score_date
    ):
        captured["scorecard_data"] = scorecard_data
        return SimpleNamespace(total_points=0)

    service = ScoreCalculatorService(sqlite_db)
    monkeypatch.setattr(
        service.scoring_service,
        "calculate_and_save_daily_score",
        fake_calculate_and_save_daily_score,
    )
    monkeypatch.setattr(service, "_capture_ranking_snapshot", lambda *_args, **_kwargs: 0)
    monkeypatch.setattr(service, "_notify_discord_position_changes_async", lambda *_args, **_kwargs: None)

    results = service.calculate_scores_for_tournament(tournament_id, round_id=1)

    assert results["players_with_scorecards"] == 1
    assert "50525" not in results["missing_player_ids"]
    assert captured["scorecard_data"]["50525"][0]["roundId"] == 1


def test_get_player_ids_with_scorecard_for_round_uses_internal_round_id(
    sqlite_db, tournament_for_score_calc_merge
):
    """
    Regression test:
    `_get_player_ids_with_scorecard_for_round` must check internal scorecard `roundId`,
    not only `ScoreSnapshot.round_id`.
    """
    tournament_id = tournament_for_score_calc_merge.id

    # Snapshot for round 1 exists but doesn't have any scorecard payload
    sqlite_db.add(
        ScoreSnapshot(
            tournament_id=tournament_id,
            round_id=1,
            timestamp=datetime(2024, 4, 11, 10, 0, 0),
            leaderboard_data={"leaderboardRows": []},
            scorecard_data={},
        )
    )

    # Later snapshot contains player scorecards whose internal roundId=1
    sqlite_db.add(
        ScoreSnapshot(
            tournament_id=tournament_id,
            round_id=2,
            timestamp=datetime(2024, 4, 12, 10, 0, 0),
            leaderboard_data={"leaderboardRows": []},
            scorecard_data={
                "50525": [
                    {"roundId": 1},
                ]
            },
        )
    )
    sqlite_db.commit()

    sync_service = DataSyncService(sqlite_db)
    have = sync_service._get_player_ids_with_scorecard_for_round(tournament_id, 1)
    assert have == {"50525"}

