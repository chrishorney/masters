"""Admin endpoints for tournament data diagnostics and repair."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.database import get_db
from app.models import (
    Tournament, Entry, Player, DailyScore, ScoreSnapshot,
    BonusPoint, RankingSnapshot, Participant
)

router = APIRouter()


@router.get("/diagnostics/tournament/{tournament_id}")
async def diagnose_tournament(
    tournament_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Diagnose tournament data integrity.
    
    Returns detailed information about:
    - Tournament details
    - Entries and their associations
    - Score snapshots
    - Daily scores
    - Potential issues
    """
    result = {
        "tournament_id": tournament_id,
        "tournament": None,
        "entries": {
            "total": 0,
            "with_scores": 0,
            "without_scores": 0,
            "list": []
        },
        "snapshots": {
            "total": 0,
            "by_round": {},
            "latest": None
        },
        "daily_scores": {
            "total": 0,
            "by_round": {}
        },
        "issues": [],
        "warnings": [],
        "recommendations": []
    }
    
    # 1. Check tournament exists
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        result["issues"].append(f"Tournament {tournament_id} not found")
        return result
    
    result["tournament"] = {
        "id": tournament.id,
        "year": tournament.year,
        "name": tournament.name,
        "tourn_id": tournament.tourn_id,
        "org_id": tournament.org_id,
        "current_round": tournament.current_round,
        "start_date": tournament.start_date.isoformat(),
        "end_date": tournament.end_date.isoformat(),
        "status": tournament.status
    }
    
    # 2. Check entries
    entries = db.query(Entry).filter(Entry.tournament_id == tournament_id).all()
    result["entries"]["total"] = len(entries)
    
    # Get entry IDs
    entry_ids = [e.id for e in entries]
    
    # Check which entries have scores
    entries_with_scores = set()
    daily_scores = db.query(DailyScore).filter(
        DailyScore.entry_id.in_(entry_ids)
    ).all() if entry_ids else []
    
    for score in daily_scores:
        entries_with_scores.add(score.entry_id)
    
    result["entries"]["with_scores"] = len(entries_with_scores)
    result["entries"]["without_scores"] = len(entries) - len(entries_with_scores)
    
    # Entry details
    for entry in entries:
        entry_scores = [s for s in daily_scores if s.entry_id == entry.id]
        total_points = sum(s.total_points for s in entry_scores)
        
        result["entries"]["list"].append({
            "id": entry.id,
            "participant_name": entry.participant.name if entry.participant else "Unknown",
            "participant_id": entry.participant_id,
            "players": [
                entry.player1_id,
                entry.player2_id,
                entry.player3_id,
                entry.player4_id,
                entry.player5_id,
                entry.player6_id,
            ],
            "has_scores": entry.id in entries_with_scores,
            "total_points": total_points,
            "num_scores": len(entry_scores)
        })
    
    if result["entries"]["without_scores"] > 0:
        result["warnings"].append(
            f"{result['entries']['without_scores']} entries have no daily scores"
        )
    
    # 3. Check score snapshots
    snapshots = db.query(ScoreSnapshot).filter(
        ScoreSnapshot.tournament_id == tournament_id
    ).order_by(ScoreSnapshot.timestamp.desc()).all()
    
    result["snapshots"]["total"] = len(snapshots)
    
    if not snapshots:
        result["issues"].append("No score snapshots found - need to sync tournament data")
    else:
        latest = snapshots[0]
        result["snapshots"]["latest"] = {
            "id": latest.id,
            "round_id": latest.round_id,
            "timestamp": latest.timestamp.isoformat(),
            "has_leaderboard": bool(latest.leaderboard_data),
            "has_scorecards": bool(latest.scorecard_data),
            "player_count": len(latest.leaderboard_data.get("leaderboardRows", [])) if latest.leaderboard_data else 0
        }
        
        # Group by round
        for snapshot in snapshots:
            round_id = snapshot.round_id
            if round_id not in result["snapshots"]["by_round"]:
                result["snapshots"]["by_round"][round_id] = 0
            result["snapshots"]["by_round"][round_id] += 1
    
    # 4. Check daily scores
    result["daily_scores"]["total"] = len(daily_scores)
    
    for score in daily_scores:
        round_id = score.round_id
        if round_id not in result["daily_scores"]["by_round"]:
            result["daily_scores"]["by_round"][round_id] = 0
        result["daily_scores"]["by_round"][round_id] += 1
    
    # 5. Check for specific player (Min Woo Lee) if in latest snapshot
    if snapshots and snapshots[0].leaderboard_data:
        leaderboard_rows = snapshots[0].leaderboard_data.get("leaderboardRows", [])
        min_woo_lee = None
        
        for row in leaderboard_rows:
            first_name = row.get("firstName", "").lower()
            last_name = row.get("lastName", "").lower()
            if 'min' in first_name and 'woo' in last_name and 'lee' in last_name:
                min_woo_lee = {
                    "player_id": str(row.get("playerId", "")),
                    "name": f"{row.get('firstName', '')} {row.get('lastName', '')}",
                    "position": row.get("position"),
                    "score": row.get("totalScore")
                }
                break
        
        if min_woo_lee:
            # Check if any entries have this player
            entries_with_min_woo = []
            for entry in entries:
                players = [
                    str(entry.player1_id), str(entry.player2_id), str(entry.player3_id),
                    str(entry.player4_id), str(entry.player5_id), str(entry.player6_id)
                ]
                if min_woo_lee["player_id"] in players:
                    entry_scores = [s for s in daily_scores if s.entry_id == entry.id]
                    total_points = sum(s.total_points for s in entry_scores)
                    entries_with_min_woo.append({
                        "entry_id": entry.id,
                        "participant_name": entry.participant.name if entry.participant else "Unknown",
                        "total_points": total_points,
                        "has_scores": entry.id in entries_with_scores
                    })
            
            result["min_woo_lee"] = {
                "in_leaderboard": True,
                "player_info": min_woo_lee,
                "entries_with_player": entries_with_min_woo
            }
            
            if entries_with_min_woo:
                entries_without_scores = [e for e in entries_with_min_woo if not e["has_scores"]]
                if entries_without_scores:
                    result["issues"].append(
                        f"{len(entries_without_scores)} entries with Min Woo Lee have no scores"
                    )
        else:
            result["min_woo_lee"] = {
                "in_leaderboard": False,
                "message": "Min Woo Lee not found in latest leaderboard snapshot"
            }
    
    # 6. Check for cross-contamination
    wrong_snapshots = db.query(ScoreSnapshot).filter(
        ScoreSnapshot.tournament_id != tournament_id
    ).count()
    
    if wrong_snapshots > 0:
        result["warnings"].append(f"{wrong_snapshots} score snapshots exist for other tournaments")
    
    # 7. Generate recommendations
    if not snapshots:
        result["recommendations"].append("Sync tournament data: POST /api/tournament/sync?year={}".format(tournament.year))
    
    if result["entries"]["without_scores"] > 0 and snapshots:
        result["recommendations"].append(
            f"Calculate scores: POST /api/scores/calculate-all?tournament_id={tournament_id}"
        )
    
    if result["issues"]:
        result["recommendations"].append(
            f"Consider clearing and rebuilding: POST /api/admin/diagnostics/tournament/{tournament_id}/clear"
        )
    
    return result


@router.get("/diagnostics/tournament/{tournament_id}/round/{round_id}/cut-status")
async def check_cut_status(
    tournament_id: int,
    round_id: int,
    player_name: Optional[str] = Query(None, description="Player name to check (e.g., 'Adam Long')"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Check cut status for players in a specific round.
    
    This helps diagnose why cut players might be getting points incorrectly.
    Shows comparison between Round 2 (where cut happens) and current round.
    """
    tournament = db.query(Tournament).filter(
        Tournament.id == tournament_id
    ).first()
    
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    # Get snapshot for this round
    snapshot = db.query(ScoreSnapshot).filter(
        ScoreSnapshot.tournament_id == tournament_id,
        ScoreSnapshot.round_id == round_id
    ).order_by(ScoreSnapshot.timestamp.desc()).first()
    
    if not snapshot:
        raise HTTPException(
            status_code=404, 
            detail=f"No snapshot found for tournament {tournament_id}, round {round_id}"
        )
    
    # Get Round 2 snapshot (where cut happens)
    round2_snapshot = db.query(ScoreSnapshot).filter(
        ScoreSnapshot.tournament_id == tournament_id,
        ScoreSnapshot.round_id == 2
    ).order_by(ScoreSnapshot.timestamp.desc()).first()
    
    result = {
        "tournament_id": tournament_id,
        "round_id": round_id,
        "round2_snapshot_exists": bool(round2_snapshot),
        "current_round_players": [],
        "round2_cut_players": [],
        "player_status_comparison": []
    }
    
    # Find player ID if name provided
    player_id_to_check = None
    if player_name:
        player = db.query(Player).filter(
            Player.full_name.ilike(f"%{player_name}%")
        ).first()
        if player:
            player_id_to_check = player.player_id
    
    # Get all players from current round
    if snapshot.leaderboard_data:
        rows = snapshot.leaderboard_data.get("leaderboardRows", [])
        for row in rows:
            player_id_str = str(row.get("playerId"))
            if player_id_to_check and player_id_str != str(player_id_to_check):
                continue
            
            position = row.get("position")
            status = row.get("status", "unknown")
            name = f"{row.get('firstName', '')} {row.get('lastName', '')}".strip()
            
            # Check Round 2 status
            round2_status = None
            round2_position = None
            if round2_snapshot and round2_snapshot.leaderboard_data:
                round2_rows = round2_snapshot.leaderboard_data.get("leaderboardRows", [])
                for r2_row in round2_rows:
                    if str(r2_row.get("playerId")) == player_id_str:
                        round2_status = r2_row.get("status", "unknown")
                        round2_position = r2_row.get("position")
                        break
            
            was_cut_in_round2 = round2_status and round2_status.lower() in ["cut", "wd", "dq"]
            
            result["current_round_players"].append({
                "player_id": player_id_str,
                "name": name,
                "position": position,
                "status": status,
                "round2_status": round2_status,
                "round2_position": round2_position,
                "was_cut_in_round2": was_cut_in_round2,
                "should_get_points": not was_cut_in_round2
            })
            
            if player_id_to_check and player_id_str == str(player_id_to_check):
                result["player_status_comparison"] = [{
                    "player_id": player_id_str,
                    "name": name,
                    "round2_status": round2_status,
                    "round2_position": round2_position,
                    "current_round_status": status,
                    "current_round_position": position,
                    "was_cut_in_round2": was_cut_in_round2,
                    "should_get_points": not was_cut_in_round2,
                    "explanation": "Player was cut in Round 2, so should get 0 points in Round 3 and 4" if was_cut_in_round2 else "Player made the cut, can earn points"
                }]
    
    # Get all cut players from Round 2
    if round2_snapshot and round2_snapshot.leaderboard_data:
        round2_rows = round2_snapshot.leaderboard_data.get("leaderboardRows", [])
        for row in round2_rows:
            status = row.get("status", "").lower()
            if status in ["cut", "wd", "dq"]:
                player_id_str = str(row.get("playerId"))
                if player_id_to_check and player_id_str != str(player_id_to_check):
                    continue
                
                name = f"{row.get('firstName', '')} {row.get('lastName', '')}".strip()
                result["round2_cut_players"].append({
                    "player_id": player_id_str,
                    "name": name,
                    "status": status,
                    "position": row.get("position")
                })
    
    return result


@router.post("/diagnostics/tournament/{tournament_id}/clear")
async def clear_tournament_data(
    tournament_id: int,
    confirm: bool = Query(False, description="Must be true to confirm deletion"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Clear all scoring data for a tournament (keeps entries and players).
    
    This will delete:
    - All daily scores
    - All bonus points
    - All ranking snapshots
    - All score snapshots
    
    Entries and players are NOT deleted.
    
    WARNING: This is irreversible!
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Must set confirm=true to clear tournament data"
        )
    
    # Verify tournament exists
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail=f"Tournament {tournament_id} not found")
    
    # Get entries for this tournament
    entries = db.query(Entry).filter(Entry.tournament_id == tournament_id).all()
    entry_ids = [e.id for e in entries]
    
    deleted_counts = {
        "daily_scores": 0,
        "bonus_points": 0,
        "ranking_snapshots": 0,
        "score_snapshots": 0
    }
    
    if entry_ids:
        # Delete daily scores
        deleted_counts["daily_scores"] = db.query(DailyScore).filter(
            DailyScore.entry_id.in_(entry_ids)
        ).delete(synchronize_session=False)
        
        # Delete bonus points
        deleted_counts["bonus_points"] = db.query(BonusPoint).filter(
            BonusPoint.entry_id.in_(entry_ids)
        ).delete(synchronize_session=False)
        
        # Delete ranking snapshots
        deleted_counts["ranking_snapshots"] = db.query(RankingSnapshot).filter(
            RankingSnapshot.entry_id.in_(entry_ids)
        ).delete(synchronize_session=False)
    
    # Delete score snapshots
    deleted_counts["score_snapshots"] = db.query(ScoreSnapshot).filter(
        ScoreSnapshot.tournament_id == tournament_id
    ).delete(synchronize_session=False)
    
    db.commit()
    
    return {
        "message": f"Cleared all scoring data for tournament {tournament_id}",
        "tournament": {
            "id": tournament.id,
            "name": tournament.name,
            "year": tournament.year
        },
        "deleted": deleted_counts,
        "next_steps": [
            f"1. Sync tournament: POST /api/tournament/sync?year={tournament.year}",
            f"2. Calculate scores: POST /api/scores/calculate-all?tournament_id={tournament_id}"
        ]
    }


@router.post("/diagnostics/tournament/{tournament_id}/clear-entries")
async def clear_tournament_entries(
    tournament_id: int,
    confirm: bool = Query(False, description="Must be true to confirm deletion"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Clear all entries for a tournament.
    
    This will delete:
    - All entries for this tournament
    - All daily scores for those entries
    - All bonus points for those entries
    - All ranking snapshots for those entries
    
    Participants and players are NOT deleted.
    
    WARNING: This is irreversible!
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Must set confirm=true to clear tournament entries"
        )
    
    # Verify tournament exists
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail=f"Tournament {tournament_id} not found")
    
    # Get entries for this tournament
    entries = db.query(Entry).filter(Entry.tournament_id == tournament_id).all()
    entry_ids = [e.id for e in entries]
    
    deleted_counts = {
        "entries": len(entry_ids),
        "daily_scores": 0,
        "bonus_points": 0,
        "ranking_snapshots": 0
    }
    
    if entry_ids:
        # Delete daily scores
        deleted_counts["daily_scores"] = db.query(DailyScore).filter(
            DailyScore.entry_id.in_(entry_ids)
        ).delete(synchronize_session=False)
        
        # Delete bonus points
        deleted_counts["bonus_points"] = db.query(BonusPoint).filter(
            BonusPoint.entry_id.in_(entry_ids)
        ).delete(synchronize_session=False)
        
        # Delete ranking snapshots
        deleted_counts["ranking_snapshots"] = db.query(RankingSnapshot).filter(
            RankingSnapshot.entry_id.in_(entry_ids)
        ).delete(synchronize_session=False)
        
        # Delete entries
        db.query(Entry).filter(Entry.tournament_id == tournament_id).delete(synchronize_session=False)
    
    db.commit()
    
    return {
        "message": f"Cleared all entries for tournament {tournament_id}",
        "tournament": {
            "id": tournament.id,
            "name": tournament.name,
            "year": tournament.year
        },
        "deleted": deleted_counts
    }


@router.post("/diagnostics/clear-all")
async def clear_all_tournament_data(
    confirm: bool = Query(False, description="Must be true to confirm deletion"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Clear ALL tournament data from the database.
    
    This will delete:
    - All entries (from all tournaments)
    - All daily scores
    - All bonus points
    - All ranking snapshots
    - All score snapshots
    - All tournaments
    
    Participants and players are NOT deleted (they can be reused).
    
    WARNING: This is irreversible and will delete ALL tournament data!
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Must set confirm=true to clear all tournament data"
        )
    
    deleted_counts = {
        "entries": 0,
        "daily_scores": 0,
        "bonus_points": 0,
        "ranking_snapshots": 0,
        "score_snapshots": 0,
        "tournaments": 0
    }
    
    try:
        # Delete in correct order to avoid foreign key constraint issues
        # 1. Delete child records first (they reference entries and tournaments)
        deleted_counts["daily_scores"] = db.query(DailyScore).delete(synchronize_session=False)
        deleted_counts["bonus_points"] = db.query(BonusPoint).delete(synchronize_session=False)
        deleted_counts["ranking_snapshots"] = db.query(RankingSnapshot).delete(synchronize_session=False)
        deleted_counts["score_snapshots"] = db.query(ScoreSnapshot).delete(synchronize_session=False)
        
        # 2. Delete entries (they reference tournaments and participants)
        deleted_counts["entries"] = db.query(Entry).delete(synchronize_session=False)
        
        # 3. Delete tournaments last (they might be referenced by entries)
        deleted_counts["tournaments"] = db.query(Tournament).delete(synchronize_session=False)
        
        db.commit()
    except Exception as e:
        db.rollback()
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error clearing all tournament data: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing all tournament data: {str(e)}"
        )
    
    return {
        "message": "Cleared all tournament data from database",
        "deleted": deleted_counts,
        "preserved": {
            "participants": "All participants preserved",
            "players": "All players preserved"
        },
        "next_steps": [
            "1. Import or create new tournaments",
            "2. Import entries for new tournaments",
            "3. Sync tournament data from API"
        ]
    }


@router.post("/diagnostics/tournament/{tournament_id}/fix")
async def fix_tournament_data(
    tournament_id: int,
    fix_entries: bool = Query(False, description="Fix entries with wrong tournament_id"),
    recalculate_scores: bool = Query(True, description="Recalculate scores after fixing"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Automatically fix common tournament data issues.
    
    This will:
    1. Check for entries with wrong tournament_id (if fix_entries=True)
    2. Verify score snapshots exist
    3. Recalculate scores (if recalculate_scores=True)
    """
    result = {
        "tournament_id": tournament_id,
        "fixes_applied": [],
        "errors": []
    }
    
    # Verify tournament exists
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail=f"Tournament {tournament_id} not found")
    
    # Check for entries that might be in wrong tournament
    if fix_entries:
        # This is tricky - we'd need to know which entries should be in which tournament
        # For now, we'll just check if entries exist
        entries = db.query(Entry).filter(Entry.tournament_id == tournament_id).all()
        result["fixes_applied"].append(f"Found {len(entries)} entries for tournament {tournament_id}")
    
    # Check if snapshots exist
    snapshots = db.query(ScoreSnapshot).filter(
        ScoreSnapshot.tournament_id == tournament_id
    ).count()
    
    if snapshots == 0:
        result["errors"].append("No score snapshots found - please sync tournament data first")
        result["fixes_applied"].append("Recommendation: POST /api/tournament/sync?year={}".format(tournament.year))
    else:
        result["fixes_applied"].append(f"Found {snapshots} score snapshots")
    
    # Recalculate scores if requested
    if recalculate_scores and snapshots > 0:
        try:
            from app.services.score_calculator import ScoreCalculatorService
            calculator = ScoreCalculatorService(db)
            calc_result = calculator.calculate_all_rounds(tournament_id)
            result["fixes_applied"].append(
                f"Recalculated scores: {calc_result['total_entries_processed']} entries processed"
            )
        except Exception as e:
            result["errors"].append(f"Error recalculating scores: {str(e)}")
    
    return result


@router.get("/diagnostics/tournament/{tournament_id}/round/{round_id}/bonuses")
async def get_round_bonuses_diagnostic(
    tournament_id: int,
    round_id: int,
    player_id: Optional[str] = Query(None, description="Specific player ID to check"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Diagnose bonus points for a round.
    Shows all bonuses awarded, low score leader, and any missing bonuses.
    """
    result = {
        "tournament_id": tournament_id,
        "round_id": round_id,
        "low_score_leader": None,
        "low_score_value": None,
        "low_score_display": None,
        "bonuses_found": [],
        "entries_with_player": [],
        "issues": []
    }
    
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        result["issues"].append(f"Tournament {tournament_id} not found")
        return result
    
    # Get snapshot for this round
    snapshot = db.query(ScoreSnapshot).filter(
        ScoreSnapshot.tournament_id == tournament_id,
        ScoreSnapshot.round_id == round_id
    ).order_by(ScoreSnapshot.timestamp.desc()).first()
    
    if not snapshot or not snapshot.leaderboard_data:
        result["issues"].append(f"No snapshot found for Round {round_id}")
        return result
    
    # Find low score leader (check all players, not just "complete")
    leaderboard_rows = snapshot.leaderboard_data.get("leaderboardRows", [])
    low_score_player = None
    low_score_value = None
    low_score_display = None
    
    for row in leaderboard_rows:
        status = row.get("status", "").lower()
        if status in ["wd", "dq"]:
            continue
        
        current_round_score = row.get("currentRoundScore", "")
        if not current_round_score:
            continue
        
        try:
            if current_round_score.startswith("-"):
                score = -int(current_round_score[1:])
            elif current_round_score.startswith("+"):
                score = int(current_round_score[1:])
            elif current_round_score == "E":
                score = 0
            else:
                continue
            
            if low_score_value is None or score < low_score_value:
                low_score_value = score
                low_score_player = str(row.get("playerId"))
                low_score_display = current_round_score
        except (ValueError, AttributeError):
            continue
    
    result["low_score_leader"] = low_score_player
    result["low_score_value"] = low_score_value
    result["low_score_display"] = low_score_display
    
    # Get all bonuses for this round
    from app.models import BonusPoint, Entry
    bonuses = db.query(BonusPoint).filter(
        BonusPoint.entry_id.in_(
            db.query(Entry.id).filter(Entry.tournament_id == tournament_id)
        ),
        BonusPoint.round_id == round_id
    ).all()
    
    for bonus in bonuses:
        entry = db.query(Entry).filter(Entry.id == bonus.entry_id).first()
        result["bonuses_found"].append({
            "entry_id": bonus.entry_id,
            "participant_name": entry.participant.name if entry and entry.participant else "Unknown",
            "bonus_type": bonus.bonus_type,
            "player_id": bonus.player_id,
            "hole": bonus.hole,
            "points": bonus.points,
            "awarded_at": bonus.awarded_at.isoformat() if bonus.awarded_at else None
        })
    
    # If specific player requested, check entries with that player
    if player_id:
        entries = db.query(Entry).filter(Entry.tournament_id == tournament_id).all()
        for entry in entries:
            player_ids = [
                str(entry.player1_id), str(entry.player2_id), str(entry.player3_id),
                str(entry.player4_id), str(entry.player5_id), str(entry.player6_id)
            ]
            if player_id in player_ids:
                # Check if this entry has bonuses for this player
                player_bonuses = [b for b in bonuses if b.player_id == player_id and b.entry_id == entry.id]
                result["entries_with_player"].append({
                    "entry_id": entry.id,
                    "participant_name": entry.participant.name if entry.participant else "Unknown",
                    "has_bonuses": len(player_bonuses) > 0,
                    "bonuses": [
                        {
                            "type": b.bonus_type,
                            "points": b.points,
                            "hole": b.hole
                        } for b in player_bonuses
                    ]
                })
    
    return result


@router.get("/diagnostics/tournament/{tournament_id}/round/{round_id}/player/{player_id}/scorecard")
async def check_player_scorecard(
    tournament_id: int,
    round_id: int,
    player_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Check scorecard data for a specific player in a round.
    Useful for debugging why bonuses aren't being awarded.
    """
    result = {
        "tournament_id": tournament_id,
        "round_id": round_id,
        "player_id": player_id,
        "scorecard_found": False,
        "scorecard_data": None,
        "eagles": [],
        "albatrosses": [],
        "hole_in_ones": [],
        "snapshots_checked": 0
    }
    
    # Get all snapshots for this round
    snapshots = db.query(ScoreSnapshot).filter(
        ScoreSnapshot.tournament_id == tournament_id,
        ScoreSnapshot.round_id == round_id
    ).order_by(ScoreSnapshot.timestamp.desc()).all()
    
    result["snapshots_checked"] = len(snapshots)
    
    # Check each snapshot for scorecard data
    for snapshot in snapshots:
        if snapshot.scorecard_data and player_id in snapshot.scorecard_data:
            result["scorecard_found"] = True
            scorecards = snapshot.scorecard_data[player_id]
            result["scorecard_data"] = scorecards
            
            # Ensure scorecards is a list
            if isinstance(scorecards, dict):
                scorecards = [scorecards]
            
            # Parse scorecards to find bonuses
            from app.services.data_sync import parse_mongodb_value
            for scorecard in scorecards:
                if not isinstance(scorecard, dict):
                    continue
                    
                scorecard_round_id = parse_mongodb_value(scorecard.get("roundId"))
                
                # Convert to int for comparison
                try:
                    scorecard_round_id_int = int(scorecard_round_id) if scorecard_round_id is not None else None
                    target_round_id_int = int(round_id)
                except (ValueError, TypeError):
                    scorecard_round_id_int = scorecard_round_id
                    target_round_id_int = round_id
                
                if scorecard_round_id_int == target_round_id_int:
                    holes = scorecard.get("holes", {})
                    for hole_num, hole_data in holes.items():
                        hole_score = parse_mongodb_value(hole_data.get("holeScore"))
                        par = parse_mongodb_value(hole_data.get("par"))
                        
                        if hole_score is not None and par is not None:
                            score_to_par = hole_score - par
                            
                            if hole_score == 1 and par == 3:
                                result["hole_in_ones"].append({
                                    "hole": int(hole_num),
                                    "score": hole_score,
                                    "par": par
                                })
                            elif score_to_par == -3:
                                result["albatrosses"].append({
                                    "hole": int(hole_num),
                                    "score": hole_score,
                                    "par": par
                                })
                            elif score_to_par == -2:
                                result["eagles"].append({
                                    "hole": int(hole_num),
                                    "score": hole_score,
                                    "par": par
                                })
            break  # Found scorecard, no need to check older snapshots
    
    # Also check if player is on any entries
    try:
        from app.models import Entry
        from sqlalchemy import or_
        
        entries_with_player = db.query(Entry).filter(
            Entry.tournament_id == tournament_id,
            or_(
                Entry.player1_id == player_id,
                Entry.player2_id == player_id,
                Entry.player3_id == player_id,
                Entry.player4_id == player_id,
                Entry.player5_id == player_id,
                Entry.player6_id == player_id
            )
        ).all()
        
        result["entries_with_player"] = [
            {
                "entry_id": entry.id,
                "participant_name": entry.participant.name if entry.participant else "Unknown"
            }
            for entry in entries_with_player
        ]
        
        # Check if bonuses exist for this player in this round
        if entries_with_player:
            from app.models import BonusPoint
            entry_ids = [e.id for e in entries_with_player]
            bonuses = db.query(BonusPoint).filter(
                BonusPoint.entry_id.in_(entry_ids),
                BonusPoint.round_id == round_id,
                BonusPoint.player_id == player_id
            ).all()
            
            result["bonuses_found"] = [
                {
                    "entry_id": b.entry_id,
                    "bonus_type": b.bonus_type,
                    "points": b.points,
                    "hole": b.hole,
                    "awarded_at": b.awarded_at.isoformat() if b.awarded_at else None
                }
                for b in bonuses
            ]
        else:
            result["entries_with_player"] = []
            result["bonuses_found"] = []
    except Exception as e:
        logger.error(f"Error checking entries and bonuses: {e}", exc_info=True)
        result["entries_with_player"] = []
        result["bonuses_found"] = []
        result["error"] = f"Error checking entries: {str(e)}"
    
    return result


@router.get("/diagnostics/tournament/{tournament_id}/round/{round_id}")
async def diagnose_round(
    tournament_id: int,
    round_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Diagnose specific round data and scores.
    
    Returns detailed information about:
    - Round snapshot existence and data
    - Daily scores for the round
    - Player matching between entries and leaderboard
    - Score calculation details
    """
    result = {
        "tournament_id": tournament_id,
        "round_id": round_id,
        "tournament": None,
        "snapshot": None,
        "snapshot_exists": False,
        "snapshot_data_summary": {},
        "daily_scores": {
            "total": 0,
            "entries_with_scores": 0,
            "entries_without_scores": 0,
            "total_points_sum": 0,
            "scores": []
        },
        "player_matching": {
            "entries_players": [],
            "leaderboard_players": [],
            "matched": [],
            "unmatched": []
        },
        "issues": [],
        "warnings": []
    }
    
    # 1. Check tournament exists
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        result["issues"].append(f"Tournament {tournament_id} not found")
        return result
    
    result["tournament"] = {
        "id": tournament.id,
        "year": tournament.year,
        "name": tournament.name,
        "current_round": tournament.current_round
    }
    
    # 2. Check snapshot for this round
    snapshot = db.query(ScoreSnapshot).filter(
        ScoreSnapshot.tournament_id == tournament_id,
        ScoreSnapshot.round_id == round_id
    ).order_by(ScoreSnapshot.timestamp.desc()).first()
    
    if snapshot:
        result["snapshot_exists"] = True
        result["snapshot"] = {
            "id": snapshot.id,
            "round_id": snapshot.round_id,
            "timestamp": snapshot.timestamp.isoformat(),
            "has_leaderboard_data": bool(snapshot.leaderboard_data),
            "has_scorecard_data": bool(snapshot.scorecard_data)
        }
        
        # Summarize leaderboard data
        if snapshot.leaderboard_data:
            leaderboard_rows = snapshot.leaderboard_data.get("leaderboardRows", [])
            result["snapshot_data_summary"] = {
                "leaderboard_rows": len(leaderboard_rows),
                "leaderboard_keys": list(snapshot.leaderboard_data.keys()) if isinstance(snapshot.leaderboard_data, dict) else [],
                "sample_players": [
                    {
                        "playerId": row.get("playerId"),
                        "name": f"{row.get('firstName', '')} {row.get('lastName', '')}".strip(),
                        "position": row.get("positionDisplay", row.get("position")),
                        "scoreToPar": row.get("scoreToPar"),
                        "currentRoundScore": row.get("currentRoundScore")
                    }
                    for row in leaderboard_rows[:10]  # First 10 players
                ]
            }
            
            # Get all player IDs from leaderboard
            leaderboard_player_ids = {str(row.get("playerId")) for row in leaderboard_rows if row.get("playerId")}
            result["player_matching"]["leaderboard_players"] = list(leaderboard_player_ids)
            
            if len(leaderboard_rows) == 0:
                result["issues"].append("Leaderboard data exists but is empty (0 rows)")
        else:
            result["issues"].append("Snapshot exists but has no leaderboard data")
        
        # Check scorecard data structure
        if snapshot.scorecard_data:
            scorecard_keys = list(snapshot.scorecard_data.keys()) if isinstance(snapshot.scorecard_data, dict) else []
            result["snapshot_data_summary"]["scorecard_players"] = len(scorecard_keys)
            result["snapshot_data_summary"]["scorecard_sample"] = {}
            
            # Sample first player's scorecard structure
            if scorecard_keys:
                first_player_id = scorecard_keys[0]
                first_scorecard = snapshot.scorecard_data.get(first_player_id)
                if isinstance(first_scorecard, list):
                    result["snapshot_data_summary"]["scorecard_sample"] = {
                        "player_id": first_player_id,
                        "scorecard_type": "list",
                        "rounds_count": len(first_scorecard),
                        "first_round_keys": list(first_scorecard[0].keys()) if first_scorecard and len(first_scorecard) > 0 else [],
                        "round_numbers": [r.get("roundId") for r in first_scorecard if isinstance(r, dict)],
                        "round_numbers_with_types": [
                            {"roundId": r.get("roundId"), "type": type(r.get("roundId")).__name__}
                            for r in first_scorecard if isinstance(r, dict)
                        ]
                    }
                elif isinstance(first_scorecard, dict):
                    result["snapshot_data_summary"]["scorecard_sample"] = {
                        "player_id": first_player_id,
                        "scorecard_type": "dict",
                        "keys": list(first_scorecard.keys())
                    }
    else:
        result["issues"].append(f"No snapshot found for Round {round_id}")
        result["warnings"].append("You may need to sync this round first: POST /api/tournament/sync-round?tournament_id={}&round_id={}".format(tournament_id, round_id))
    
    # 3. Check daily scores for this round
    entries = db.query(Entry).filter(Entry.tournament_id == tournament_id).all()
    entry_ids = [e.id for e in entries]
    
    daily_scores = db.query(DailyScore).filter(
        DailyScore.entry_id.in_(entry_ids),
        DailyScore.round_id == round_id
    ).all() if entry_ids else []
    
    result["daily_scores"]["total"] = len(daily_scores)
    result["daily_scores"]["entries_with_scores"] = len(set(s.entry_id for s in daily_scores))
    result["daily_scores"]["entries_without_scores"] = len(entries) - result["daily_scores"]["entries_with_scores"]
    result["daily_scores"]["total_points_sum"] = sum(s.total_points for s in daily_scores)
    
    # Detailed score breakdown
    for score in daily_scores:
        entry = next((e for e in entries if e.id == score.entry_id), None)
        result["daily_scores"]["scores"].append({
            "entry_id": score.entry_id,
            "participant_name": entry.participant.name if entry and entry.participant else "Unknown",
            "round_id": score.round_id,
            "base_points": score.base_points,
            "bonus_points": score.bonus_points,
            "total_points": score.total_points,
            "calculated_at": score.calculated_at.isoformat() if score.calculated_at else None
        })
    
    # 4. Check player matching between entries and leaderboard
    if snapshot and snapshot.leaderboard_data:
        leaderboard_rows = snapshot.leaderboard_data.get("leaderboardRows", [])
        leaderboard_player_ids = {str(row.get("playerId")) for row in leaderboard_rows if row.get("playerId")}
        
        # Get all player IDs from entries
        entry_player_ids = set()
        for entry in entries:
            for player_id_field in ["player1_id", "player2_id", "player3_id", "player4_id", "player5_id", "player6_id"]:
                player_id = getattr(entry, player_id_field, None)
                if player_id:
                    entry_player_ids.add(str(player_id))
        
        result["player_matching"]["entries_players"] = list(entry_player_ids)
        result["player_matching"]["matched"] = list(entry_player_ids & leaderboard_player_ids)
        result["player_matching"]["unmatched"] = list(entry_player_ids - leaderboard_player_ids)
        
        if result["player_matching"]["unmatched"]:
            result["warnings"].append(
                f"Found {len(result['player_matching']['unmatched'])} entry players not in Round {round_id} leaderboard. "
                "This may cause 0 points for those players."
            )
    
    # 5. Check for entries with 0 points
    zero_point_entries = [s for s in daily_scores if s.total_points == 0]
    if zero_point_entries:
        result["warnings"].append(
            f"Found {len(zero_point_entries)} entries with 0 points for Round {round_id}. "
            "This may be normal if players didn't make the cut or weren't in the leaderboard."
        )
    
    return result
