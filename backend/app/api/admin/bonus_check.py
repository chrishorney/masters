"""Admin endpoint for manually checking all entry players' scorecards for bonuses."""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.database import get_db
from app.models import Tournament, Entry, ScoreSnapshot
from app.services.data_sync import DataSyncService
from app.services.score_calculator import ScoreCalculatorService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/bonus-check/check-all-players")
async def check_all_entry_players_for_bonuses(
    tournament_id: int = Query(..., description="Tournament ID"),
    round_id: int = Query(None, description="Specific round (default: current round)"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Manually check all entry players' scorecards for eagles, albatrosses, and hole-in-ones.
    
    This endpoint:
    1. Gets all distinct players from entries
    2. Fetches their scorecards from the API
    3. Recalculates bonuses for all entries
    4. Returns results showing any new bonuses found
    
    This is useful as a backup to catch bonuses that might have been missed by the
    2+ stroke improvement detection logic.
    """
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    # Use current round if not specified
    if round_id is None:
        round_id = tournament.current_round or 1
    
    if not (1 <= round_id <= 4):
        raise HTTPException(status_code=400, detail="Round must be between 1 and 4")
    
    results = {
        "tournament_id": tournament_id,
        "round_id": round_id,
        "players_checked": 0,
        "scorecards_fetched": 0,
        "entries_processed": 0,
        "new_bonuses_found": 0,
        "errors": []
    }
    
    try:
        # Get all distinct entry players
        entries = db.query(Entry).filter(Entry.tournament_id == tournament_id).all()
        entry_players = set()
        
        for entry in entries:
            for player_id_field in ["player1_id", "player2_id", "player3_id", "player4_id", "player5_id", "player6_id"]:
                player_id = getattr(entry, player_id_field, None)
                if player_id:
                    entry_players.add(str(player_id))
        
        results["players_checked"] = len(entry_players)
        logger.info(f"Checking {len(entry_players)} distinct entry players for bonuses (Round {round_id})")
        
        if not entry_players:
            return {
                **results,
                "message": "No entry players found. Please import entries first."
            }
        
        # Fetch scorecards for all entry players
        sync_service = DataSyncService(db)
        scorecard_data = {}
        scorecards_fetched = 0
        
        for player_id in entry_players:
            try:
                scorecards = sync_service.api_client.get_scorecard(
                    player_id=player_id,
                    org_id=tournament.org_id,
                    tourn_id=tournament.tourn_id,
                    year=tournament.year
                )
                scorecard_data[player_id] = scorecards
                scorecards_fetched += 1
                logger.debug(f"Fetched scorecard for player {player_id}")
            except Exception as e:
                error_msg = f"Failed to fetch scorecard for player {player_id}: {e}"
                logger.warning(error_msg)
                results["errors"].append(error_msg)
        
        results["scorecards_fetched"] = scorecards_fetched
        
        if not scorecard_data:
            return {
                **results,
                "message": "No scorecards were successfully fetched. Check errors for details."
            }
        
        # Get leaderboard data from latest snapshot
        snapshot = db.query(ScoreSnapshot).filter(
            ScoreSnapshot.tournament_id == tournament_id,
            ScoreSnapshot.round_id == round_id
        ).order_by(ScoreSnapshot.timestamp.desc()).first()
        
        if not snapshot:
            raise HTTPException(
                status_code=404,
                detail=f"No snapshot found for tournament {tournament_id}, round {round_id}. Please sync tournament data first."
            )
        
        leaderboard_data = snapshot.leaderboard_data or {}
        
        # Merge fetched scorecards with existing snapshot data
        # Scorecards from API contain ALL rounds, so we need to ensure we're using the full data
        existing_scorecard_data = snapshot.scorecard_data or {}
        
        # Merge scorecards, ensuring we keep all rounds from both sources
        merged_scorecard_data = {}
        
        # Add existing scorecards
        for player_id, existing_scorecards in existing_scorecard_data.items():
            merged_scorecard_data[player_id] = existing_scorecards
        
        # Add/update with newly fetched scorecards (which contain all rounds)
        for player_id, new_scorecards in scorecard_data.items():
            # Newly fetched scorecards contain all rounds, so they should replace existing ones
            # This ensures we have the most up-to-date data for all rounds
            merged_scorecard_data[player_id] = new_scorecards
        
        logger.info(
            f"Merged scorecard data: {len(merged_scorecard_data)} players with scorecards. "
            f"Newly fetched: {len(scorecard_data)}, Existing: {len(existing_scorecard_data)}"
        )
        
        # Recalculate bonuses for all entries
        calculator = ScoreCalculatorService(db)
        entries_processed = 0
        new_bonuses_found = 0
        
        for entry in entries:
            try:
                # Calculate and save daily score (this will detect and save bonuses)
                from datetime import date
                score_date = tournament.start_date
                if round_id > 1:
                    score_date = date.fromordinal(tournament.start_date.toordinal() + (round_id - 1))
                
                daily_score = calculator.scoring_service.calculate_and_save_daily_score(
                    entry=entry,
                    tournament=tournament,
                    leaderboard_data=leaderboard_data,
                    scorecard_data=merged_scorecard_data,
                    round_id=round_id,
                    score_date=score_date
                )
                
                entries_processed += 1
                
                # Count bonuses for this entry in this round (after recalculation)
                from app.models import BonusPoint
                bonuses = db.query(BonusPoint).filter(
                    BonusPoint.entry_id == entry.id,
                    BonusPoint.round_id == round_id
                ).all()
                
                # Count bonuses by type
                for bonus in bonuses:
                    if bonus.bonus_type in ["eagle", "double_eagle", "hole_in_one", "low_score"]:
                        new_bonuses_found += 1
                
            except Exception as e:
                error_msg = f"Error processing entry {entry.id}: {e}"
                logger.error(error_msg, exc_info=True)
                results["errors"].append(error_msg)
        
        results["entries_processed"] = entries_processed
        results["new_bonuses_found"] = new_bonuses_found
        
        # Update snapshot with merged scorecard data
        snapshot.scorecard_data = merged_scorecard_data
        db.commit()
        
        # Get summary of bonuses found
        from app.models import BonusPoint, Entry
        all_bonuses = db.query(BonusPoint).filter(
            BonusPoint.entry_id.in_(
                db.query(Entry.id).filter(Entry.tournament_id == tournament_id)
            ),
            BonusPoint.round_id == round_id,
            BonusPoint.bonus_type.in_(["eagle", "double_eagle", "hole_in_one", "low_score"])
        ).all()
        
        bonus_summary = {}
        for bonus in all_bonuses:
            bonus_type = bonus.bonus_type
            if bonus_type not in bonus_summary:
                bonus_summary[bonus_type] = 0
            bonus_summary[bonus_type] += 1
        
        return {
            **results,
            "message": f"Successfully checked {scorecards_fetched} players and processed {entries_processed} entries. Found {new_bonuses_found} bonuses (eagles/albatrosses/hole-in-ones/low_score) for Round {round_id}.",
            "bonus_summary": bonus_summary,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error in check_all_entry_players_for_bonuses: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error checking players for bonuses: {str(e)}"
        )
