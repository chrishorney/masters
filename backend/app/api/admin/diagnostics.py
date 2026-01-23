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
