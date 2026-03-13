"""Public score endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, Any
from datetime import datetime, timezone

from app.database import get_db
from app.models import Tournament, Entry, DailyScore, ScoreSnapshot
from app.services.score_calculator import ScoreCalculatorService
from app.services.api_client import SlashGolfAPIClient

router = APIRouter()


def _parse_score_to_par(score_str: str) -> Optional[int]:
    """
    Parse score-to-par strings from the leaderboard into integers so we can sort reliably.

    Examples:
    - "-5" -> -5
    - "+2" -> 2
    - "E"  -> 0
    - "" or invalid -> None
    """
    if not score_str:
        return None

    try:
        if score_str.startswith("-"):
            return -int(score_str[1:])
        if score_str.startswith("+"):
            return int(score_str[1:])
        if score_str == "E":
            return 0
        return int(score_str)
    except (ValueError, AttributeError):
        return None


def _score_sort_key(row: dict[str, Any]) -> tuple[int, int]:
    """
    Build a sort key for tournament leaderboard rows.

    Primary: total score to par (lower is better)
    Secondary: total strokes (lower is better)
    """
    score_to_par: Any = None

    # Prefer the overall tournament total (e.g. "-10") when present
    total_str = row.get("total")
    if isinstance(total_str, str):
        score_to_par = _parse_score_to_par(total_str)

    # Fallbacks for older snapshot formats
    if score_to_par is None:
        score_to_par = row.get("scoreToPar")
        if not isinstance(score_to_par, (int, float)):
            score_to_par = _parse_score_to_par(row.get("currentRoundScore", "") or "")

    if score_to_par is None:
        score_to_par = 999

    # Prefer numeric total strokes if available
    total_score: Any = row.get("totalScore")
    if not isinstance(total_score, (int, float)):
        # RapidAPI leaderboard uses totalStrokesFromCompletedRounds
        total_strokes_raw = row.get("totalStrokesFromCompletedRounds")
        try:
            total_score = int(total_strokes_raw) if total_strokes_raw is not None else 999
        except (TypeError, ValueError):
            total_score = 999

    return int(score_to_par), int(total_score)


@router.post("/scores/calculate")
async def calculate_scores(
    tournament_id: int = Query(..., description="Tournament ID"),
    round_id: Optional[int] = Query(None, description="Specific round (default: current round)"),
    fetch_missing_scorecards: bool = Query(False, description="Fetch missing scorecards before calculating (uses API calls)"),
    db: Session = Depends(get_db)
):
    """
    Calculate scores for all entries in a tournament.
    
    If fetch_missing_scorecards=True, will fetch scorecards for any entry players
    that don't have scorecard data in snapshots. This ensures bonuses are detected
    but uses additional API calls.
    """
    calculator = ScoreCalculatorService(db)
    
    try:
        # If requested, fetch missing scorecards first
        if fetch_missing_scorecards:
            from app.models import Tournament, Entry, ScoreSnapshot
            from app.services.data_sync import DataSyncService, parse_mongodb_value
            
            tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
            if not tournament:
                raise HTTPException(status_code=404, detail="Tournament not found")
            
            target_round = round_id or tournament.current_round or 1
            
            # Get all entry players
            entries = db.query(Entry).filter(Entry.tournament_id == tournament_id).all()
            entry_player_ids = set()
            for entry in entries:
                for player_id_field in ["player1_id", "player2_id", "player3_id", "player4_id", "player5_id", "player6_id"]:
                    player_id = getattr(entry, player_id_field, None)
                    if player_id:
                        entry_player_ids.add(str(player_id))
            
            # Check which players are missing scorecard data for this round
            snapshot = db.query(ScoreSnapshot).filter(
                ScoreSnapshot.tournament_id == tournament_id,
                ScoreSnapshot.round_id == target_round
            ).order_by(ScoreSnapshot.timestamp.desc()).first()
            
            missing_players = set()
            if snapshot and snapshot.scorecard_data:
                for player_id in entry_player_ids:
                    if player_id not in snapshot.scorecard_data:
                        missing_players.add(player_id)
                    else:
                        # Check if scorecard has data for target round
                        player_scorecards = snapshot.scorecard_data[player_id]
                        if isinstance(player_scorecards, dict):
                            player_scorecards = [player_scorecards]
                        
                        has_round_data = False
                        for scorecard in player_scorecards:
                            scorecard_round_id = parse_mongodb_value(scorecard.get("roundId"))
                            if scorecard_round_id == target_round:
                                has_round_data = True
                                break
                        
                        if not has_round_data:
                            missing_players.add(player_id)
            else:
                # No snapshot or no scorecard data - all players are missing
                missing_players = entry_player_ids
            
            # Fetch missing scorecards
            if missing_players:
                sync_service = DataSyncService(db)
                fetched_count = 0
                for player_id in missing_players:
                    try:
                        scorecards = sync_service.api_client.get_scorecard(
                            player_id=player_id,
                            org_id=tournament.org_id,
                            tourn_id=tournament.tourn_id,
                            year=tournament.year
                        )
                        
                        # Update snapshot with fetched scorecard
                        if not snapshot:
                            # Create new snapshot if needed
                            from app.services.data_sync import DataSyncService
                            leaderboard_data = {}  # Will be filled by sync
                            snapshot = sync_service.save_score_snapshot(
                                tournament_id=tournament_id,
                                round_id=target_round,
                                leaderboard_data=leaderboard_data,
                                scorecard_data={player_id: scorecards}
                            )
                        else:
                            # Update existing snapshot
                            if not snapshot.scorecard_data:
                                snapshot.scorecard_data = {}
                            snapshot.scorecard_data[player_id] = scorecards
                        
                        fetched_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to fetch scorecard for player {player_id}: {e}")
                
                if fetched_count > 0:
                    db.commit()
                    logger.info(f"Fetched {fetched_count} missing scorecards before calculating scores")
        
        results = calculator.calculate_scores_for_tournament(tournament_id, round_id)
        
        if not results.get("success"):
            raise HTTPException(status_code=400, detail=results.get("message", "Calculation failed"))
        
        response = {
            "message": "Scores calculated successfully",
            "tournament_id": results["tournament_id"],
            "round_id": results["round_id"],
            "entries_processed": results["entries_processed"],
            "entries_updated": results["entries_updated"],
            "errors": results.get("errors", [])
        }
        
        # Add diagnostic info if available
        if "players_with_scorecards" in results:
            response["players_with_scorecards"] = results["players_with_scorecards"]
            response["players_missing_scorecards"] = results["players_missing_scorecards"]
            if results["players_missing_scorecards"] > 0:
                response["warning"] = (
                    f"{results['players_missing_scorecards']} entry players are missing scorecard data. "
                    "Bonuses may not be detected. Use fetch_missing_scorecards=true to fetch them."
                )
                response["missing_player_ids"] = results.get("missing_player_ids", [])
        
        return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating scores: {str(e)}")


@router.post("/scores/calculate-all")
async def calculate_all_rounds(
    tournament_id: int = Query(..., description="Tournament ID"),
    db: Session = Depends(get_db)
):
    """Calculate scores for all completed rounds."""
    calculator = ScoreCalculatorService(db)
    
    try:
        results = calculator.calculate_all_rounds(tournament_id)
        
        return {
            "message": "Scores calculated for all rounds",
            "tournament_id": results["tournament_id"],
            "rounds_processed": results["rounds_processed"],
            "total_entries_processed": results["total_entries_processed"],
            "errors": results.get("errors", [])
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating scores: {str(e)}")


@router.get("/scores/leaderboard")
async def get_leaderboard(
    tournament_id: int = Query(..., description="Tournament ID"),
    db: Session = Depends(get_db)
):
    """Get current leaderboard with total scores."""
    # Get tournament
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    # Get all entries for tournament
    entries = db.query(Entry).filter(Entry.tournament_id == tournament_id).all()
    
    leaderboard = []
    
    for entry in entries:
        # Get all daily scores for this entry
        daily_scores = db.query(DailyScore).filter(
            DailyScore.entry_id == entry.id
        ).order_by(DailyScore.round_id).all()
        
        total_points = sum(score.total_points for score in daily_scores)
        
        leaderboard.append({
            "entry": {
                "id": entry.id,
                "participant_id": entry.participant_id,
                "tournament_id": entry.tournament_id,
                "player1_id": entry.player1_id,
                "player2_id": entry.player2_id,
                "player3_id": entry.player3_id,
                "player4_id": entry.player4_id,
                "player5_id": entry.player5_id,
                "player6_id": entry.player6_id,
                "rebuy_player_ids": entry.rebuy_player_ids or [],
                "rebuy_type": entry.rebuy_type,
                "rebuy_original_player_ids": entry.rebuy_original_player_ids or [],
                "weekend_bonus_earned": entry.weekend_bonus_earned,
                "weekend_bonus_forfeited": entry.weekend_bonus_forfeited,
                "created_at": entry.created_at.isoformat(),
                "updated_at": entry.updated_at.isoformat(),
                "participant": {
                    "id": entry.participant.id,
                    "name": entry.participant.name,
                    "email": entry.participant.email,
                    "entry_date": entry.participant.entry_date.isoformat(),
                    "paid": entry.participant.paid,
                }
            },
            "total_points": total_points,
            "daily_scores": [
                {
                    "id": score.id,
                    "entry_id": score.entry_id,
                    "round_id": score.round_id,
                    "date": score.date.isoformat(),
                    "base_points": score.base_points,
                    "bonus_points": score.bonus_points,
                    "total_points": score.total_points,
                    "details": score.details,
                    "calculated_at": score.calculated_at.isoformat(),
                }
                for score in daily_scores
            ]
        })
    
    # Sort by total points descending
    leaderboard.sort(key=lambda x: x["total_points"], reverse=True)
    
    # Add rank
    for i, item in enumerate(leaderboard, start=1):
        item["rank"] = i
    
    # Get the most recent score snapshot to get actual last sync time
    last_snapshot = db.query(ScoreSnapshot).filter(
        ScoreSnapshot.tournament_id == tournament_id
    ).order_by(ScoreSnapshot.timestamp.desc()).first()
    
    # Ensure timestamp is in UTC for proper timezone conversion on frontend
    if last_snapshot:
        # If timestamp is timezone-naive, assume it's UTC (database typically stores UTC)
        timestamp = last_snapshot.timestamp
        if timestamp.tzinfo is None:
            # Make it timezone-aware as UTC
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        last_updated = timestamp.isoformat()
    else:
        # Use UTC for current time
        last_updated = datetime.now(timezone.utc).isoformat()
    
    return {
        "tournament": {
            "id": tournament.id,
            "year": tournament.year,
            "tourn_id": tournament.tourn_id,
            "name": tournament.name,
            "start_date": tournament.start_date.isoformat(),
            "end_date": tournament.end_date.isoformat(),
            "status": tournament.status,
            "current_round": tournament.current_round,
        },
        "entries": leaderboard,
        "last_updated": last_updated,
        "view_type": "current"  # Indicates this is current/real-time view
    }


@router.get("/scores/tournament-leaderboard")
async def get_tournament_leaderboard(
    tournament_id: int = Query(..., description="Tournament ID"),
    db: Session = Depends(get_db)
):
    """
    Get the actual tournament leaderboard (golfers, not pool entries).

    This now calls the live Slash Golf `/leaderboard` endpoint for the
    configured tournament (org_id, tourn_id, year) instead of relying
    solely on cached ScoreSnapshot data, so it always reflects the
    latest API leaderboard.
    """
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    # Fetch live leaderboard from Slash Golf API using the tournament's
    # configured identifiers (set during admin setup).
    api_client = SlashGolfAPIClient()
    try:
        leaderboard_data = api_client.get_leaderboard(
            org_id=tournament.org_id,
            tourn_id=tournament.tourn_id,
            year=tournament.year,
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch live tournament leaderboard: {e}",
        )

    leaderboard_rows = leaderboard_data.get("leaderboardRows", [])
    if not leaderboard_rows:
        raise HTTPException(
            status_code=404,
            detail="No leaderboard data returned from external API.",
        )

    # Filter out withdrawn/disqualified players first
    active_rows = [
        row for row in leaderboard_rows
        if row.get("status", "").lower() not in ["wd", "dq"]
    ]

    # Sort the remaining rows by score, independent of whatever order came from the API
    active_rows.sort(key=_score_sort_key)

    # Re-assign positions after sorting so ties display correctly
    formatted_leaderboard = []
    previous_score_key: Optional[tuple[int, int]] = None
    current_position = 0

    for index, row in enumerate(active_rows):
        score_key = _score_sort_key(row)
        if previous_score_key is None or score_key != previous_score_key:
            current_position = index + 1
        previous_score_key = score_key

        position_display = f"T{current_position}" if any(
            _score_sort_key(r) == score_key and r is not row
            for r in active_rows
        ) else str(current_position)

        first_name = row.get("firstName", "")
        last_name = row.get("lastName", "")
        full_name = f"{first_name} {last_name}".strip()
        score_str = row.get("currentRoundScore", "")
        status = row.get("status", "").lower()

        formatted_leaderboard.append({
            "position": position_display,
            "player_name": full_name,
            "score": score_str,
            "status": status,
            "player_id": str(row.get("playerId", ""))
        })
    
    # Derive round and last-updated timestamp from API payload
    raw_round = leaderboard_data.get("roundId")
    round_id: Optional[int] = None
    if isinstance(raw_round, dict) and "$numberInt" in raw_round:
        try:
            round_id = int(raw_round["$numberInt"])
        except ValueError:
            round_id = None
    elif isinstance(raw_round, int):
        round_id = raw_round

    # Timestamp can be in Mongo-style {"$date": {"$numberLong": "..."}}
    raw_ts = leaderboard_data.get("timestamp") or leaderboard_data.get("lastUpdated")
    last_updated: datetime
    if isinstance(raw_ts, dict) and "$date" in raw_ts:
        date_val = raw_ts["$date"]
        try:
            if isinstance(date_val, dict) and "$numberLong" in date_val:
                ms = int(date_val["$numberLong"])
            else:
                ms = int(date_val)
            last_updated = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
        except (TypeError, ValueError):
            last_updated = datetime.now(timezone.utc)
    else:
        last_updated = datetime.now(timezone.utc)

    return {
        "tournament": {
            "id": tournament.id,
            "year": tournament.year,
            "tourn_id": tournament.tourn_id,
            "name": tournament.name,
            "start_date": tournament.start_date.isoformat(),
            "end_date": tournament.end_date.isoformat(),
            "status": tournament.status,
            "current_round": tournament.current_round,
        },
        "leaderboard": formatted_leaderboard,
        "round_id": round_id or tournament.current_round,
        "last_updated": last_updated.isoformat(),
        "view_type": "current"
    }


@router.get("/scores/tournament-leaderboard/round/{round_id}")
async def get_round_tournament_leaderboard(
    round_id: int,
    tournament_id: int = Query(..., description="Tournament ID"),
    db: Session = Depends(get_db)
):
    """
    Get tournament leaderboard snapshot for a specific round.
    Returns the leaderboard as it was at the end of that round.
    """
    # Get tournament
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    # Validate round
    if not (1 <= round_id <= 4):
        raise HTTPException(status_code=400, detail="Round must be between 1 and 4")
    
    # Get the latest snapshot for this round
    snapshot = db.query(ScoreSnapshot).filter(
        ScoreSnapshot.tournament_id == tournament_id,
        ScoreSnapshot.round_id == round_id
    ).order_by(ScoreSnapshot.timestamp.desc()).first()
    
    if not snapshot or not snapshot.leaderboard_data:
        raise HTTPException(
            status_code=404,
            detail=f"No snapshot found for tournament {tournament_id}, round {round_id}"
        )
    
    # Extract leaderboard rows from snapshot
    leaderboard_rows = snapshot.leaderboard_data.get("leaderboardRows", [])
    
    # Format leaderboard with position, name, and score
    formatted_leaderboard = []
    for row in leaderboard_rows:
        position = row.get("position", "")
        first_name = row.get("firstName", "")
        last_name = row.get("lastName", "")
        full_name = f"{first_name} {last_name}".strip()
        score_str = row.get("currentRoundScore", "")
        status = row.get("status", "").lower()
        
        # Skip withdrawn/disqualified players
        if status in ["wd", "dq"]:
            continue
        
        formatted_leaderboard.append({
            "position": position,
            "player_name": full_name,
            "score": score_str,
            "status": status,
            "player_id": str(row.get("playerId", ""))
        })
    
    # Get snapshot timestamp
    timestamp = snapshot.timestamp
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    
    return {
        "tournament": {
            "id": tournament.id,
            "year": tournament.year,
            "tourn_id": tournament.tourn_id,
            "name": tournament.name,
            "start_date": tournament.start_date.isoformat(),
            "end_date": tournament.end_date.isoformat(),
            "status": tournament.status,
            "current_round": tournament.current_round,
        },
        "leaderboard": formatted_leaderboard,
        "round_id": round_id,
        "snapshot_timestamp": timestamp.isoformat(),
        "view_type": "round_snapshot",
        "last_updated": timestamp.isoformat()
    }
