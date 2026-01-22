"""Test data synchronization service."""
import pytest
from app.services.data_sync import DataSyncService
from app.models import Tournament, Player, ScoreSnapshot


def test_sync_tournament(db):
    """Test syncing tournament data."""
    sync_service = DataSyncService(db)
    
    # Sync tournament (using test tournament)
    tournament = sync_service.sync_tournament(tourn_id="475", year=2024)
    
    assert tournament is not None
    assert tournament.tourn_id == "475"
    assert tournament.year == 2024
    assert tournament.name is not None
    assert tournament.api_data is not None


def test_sync_players_from_leaderboard(db):
    """Test syncing players from leaderboard."""
    sync_service = DataSyncService(db)
    
    # First sync tournament
    tournament = sync_service.sync_tournament(tourn_id="475", year=2024)
    
    # Get leaderboard
    leaderboard_data = sync_service.api_client.get_leaderboard(tourn_id="475", year=2024)
    
    # Sync players
    players = sync_service.sync_players_from_leaderboard(leaderboard_data)
    
    assert len(players) > 0
    assert all(isinstance(p, Player) for p in players)
    assert all(p.player_id is not None for p in players)
    assert all(p.full_name is not None for p in players)


def test_save_score_snapshot(db):
    """Test saving score snapshot."""
    sync_service = DataSyncService(db)
    
    # Create tournament first
    tournament = sync_service.sync_tournament(tourn_id="475", year=2024)
    
    # Get leaderboard
    leaderboard_data = sync_service.api_client.get_leaderboard(tourn_id="475", year=2024)
    
    # Save snapshot
    snapshot = sync_service.save_score_snapshot(
        tournament_id=tournament.id,
        round_id=1,
        leaderboard_data=leaderboard_data
    )
    
    assert snapshot is not None
    assert snapshot.tournament_id == tournament.id
    assert snapshot.round_id == 1
    assert snapshot.leaderboard_data is not None


def test_sync_tournament_data(db):
    """Test full tournament data sync."""
    sync_service = DataSyncService(db)
    
    results = sync_service.sync_tournament_data(tourn_id="475", year=2024)
    
    assert results["tournament"] is not None
    assert results["players_synced"] > 0
    assert results["snapshot"] is not None
    assert len(results["errors"]) == 0
