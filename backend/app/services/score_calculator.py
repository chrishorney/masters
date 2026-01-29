"""Score calculator service - calculates scores for all entries."""
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import date, datetime
from sqlalchemy.orm import Session

from app.models import Tournament, Entry, ScoreSnapshot, DailyScore, RankingSnapshot
from app.services.scoring import ScoringService
from app.services.api_client import SlashGolfAPIClient

logger = logging.getLogger(__name__)


class ScoreCalculatorService:
    """Service for calculating scores for all entries in a tournament."""
    
    def __init__(self, db: Session):
        self.db = db
        self.scoring_service = ScoringService(db)
        self.api_client = SlashGolfAPIClient()
        # Initialize Discord service (will be None if disabled)
        try:
            from app.services.discord import get_discord_service
            self.discord_service = get_discord_service()
        except Exception as e:
            logger.debug(f"Discord service not available: {e}")
            self.discord_service = None
    
    def calculate_scores_for_tournament(
        self,
        tournament_id: int,
        round_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calculate scores for all entries in a tournament.
        
        Args:
            tournament_id: Tournament ID
            round_id: Specific round to calculate (None = current round)
            
        Returns:
            Dictionary with calculation results
        """
        tournament = self.db.query(Tournament).filter(
            Tournament.id == tournament_id
        ).first()
        
        if not tournament:
            raise ValueError(f"Tournament {tournament_id} not found")
        
        # Get current round if not specified
        if round_id is None:
            round_id = tournament.current_round or 1
        
        # Get latest score snapshot for this round
        snapshot = self.db.query(ScoreSnapshot).filter(
            ScoreSnapshot.tournament_id == tournament_id,
            ScoreSnapshot.round_id == round_id
        ).order_by(ScoreSnapshot.timestamp.desc()).first()
        
        if not snapshot:
            logger.warning(f"No score snapshot found for tournament {tournament_id}, round {round_id}")
            return {
                "success": False,
                "message": "No score snapshot found. Please sync tournament data first.",
                "entries_processed": 0
            }
        
        leaderboard_data = snapshot.leaderboard_data
        scorecard_data = snapshot.scorecard_data or {}
        
        # Merge scorecard data from all snapshots for this round to ensure we have complete data
        # This is important because scorecards might have been fetched in earlier snapshots
        # but not in the latest one (if player didn't improve by 2+ strokes)
        all_snapshots = self.db.query(ScoreSnapshot).filter(
            ScoreSnapshot.tournament_id == tournament_id,
            ScoreSnapshot.round_id == round_id
        ).order_by(ScoreSnapshot.timestamp.desc()).all()
        
        # Merge scorecard data from all snapshots (later snapshots override earlier ones)
        # Since we're iterating in descending timestamp order, later snapshots will naturally override
        merged_scorecard_data = {}
        for snap in all_snapshots:
            if snap.scorecard_data:
                for player_id, scorecards in snap.scorecard_data.items():
                    # Later snapshots (iterated first) will override earlier ones
                    merged_scorecard_data[player_id] = scorecards
        
        # Use merged data (fallback to snapshot data if merge didn't add anything)
        if merged_scorecard_data:
            scorecard_data = merged_scorecard_data
            logger.debug(
                f"Merged scorecard data from {len(all_snapshots)} snapshots for round {round_id}. "
                f"Total players with scorecards: {len(merged_scorecard_data)}"
            )
        
        # Get all entries for this tournament
        entries = self.db.query(Entry).filter(
            Entry.tournament_id == tournament_id
        ).all()
        
        results = {
            "success": True,
            "tournament_id": tournament_id,
            "round_id": round_id,
            "entries_processed": 0,
            "entries_updated": 0,
            "errors": []
        }
        
        # Calculate date for this round
        score_date = tournament.start_date
        if round_id > 1:
            # Approximate: add days for each round
            score_date = date.fromordinal(tournament.start_date.toordinal() + (round_id - 1))
        
        for entry in entries:
            try:
                daily_score = self.scoring_service.calculate_and_save_daily_score(
                    entry=entry,
                    tournament=tournament,
                    leaderboard_data=leaderboard_data,
                    scorecard_data=scorecard_data,
                    round_id=round_id,
                    score_date=score_date
                )
                results["entries_processed"] += 1
                results["entries_updated"] += 1
                logger.debug(f"Calculated score for entry {entry.id}: {daily_score.total_points} points")
            except Exception as e:
                error_msg = f"Error calculating score for entry {entry.id}: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
                results["entries_processed"] += 1
        
        logger.info(
            f"Calculated scores for {results['entries_updated']} entries "
            f"in tournament {tournament_id}, round {round_id}"
        )
        
        # Capture ranking snapshot after scores are calculated
        # Always capture if calculation was successful, even if no entries were updated
        # (entries might have same points but positions could have changed)
        if results["success"]:
            logger.info(f"Attempting to capture ranking snapshot for tournament {tournament_id}, round {round_id}")
            try:
                snapshots_created = self._capture_ranking_snapshot(tournament_id, round_id)
                logger.info(f"Successfully captured {snapshots_created} ranking snapshots")
                
                # Send Discord notifications for position changes (fire-and-forget, non-blocking)
                self._notify_discord_position_changes_async(tournament_id, round_id)
            except Exception as e:
                # Log error but don't fail the calculation
                logger.error(f"Error capturing ranking snapshot: {e}", exc_info=True)
                results["errors"].append(f"Warning: Ranking snapshot failed: {e}")
        else:
            logger.warning(
                f"Skipping ranking snapshot capture: calculation was not successful. "
                f"success={results.get('success')}, entries_updated={results.get('entries_updated')}"
            )
        
        return results
    
    def calculate_all_rounds(
        self,
        tournament_id: int
    ) -> Dict[str, Any]:
        """
        Calculate scores for all completed rounds.
        
        Args:
            tournament_id: Tournament ID
            
        Returns:
            Dictionary with results for each round
        """
        tournament = self.db.query(Tournament).filter(
            Tournament.id == tournament_id
        ).first()
        
        if not tournament:
            raise ValueError(f"Tournament {tournament_id} not found")
        
        current_round = tournament.current_round or 1
        results = {
            "tournament_id": tournament_id,
            "rounds_processed": [],
            "total_entries_processed": 0,
            "errors": []
        }
        
        # Calculate for each completed round
        for round_id in range(1, current_round + 1):
            try:
                round_result = self.calculate_scores_for_tournament(
                    tournament_id, round_id
                )
                results["rounds_processed"].append({
                    "round_id": round_id,
                    "entries_processed": round_result.get("entries_processed", 0),
                    "entries_updated": round_result.get("entries_updated", 0),
                })
                results["total_entries_processed"] += round_result.get("entries_processed", 0)
            except Exception as e:
                error_msg = f"Error calculating round {round_id}: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
        
        return results
    
    def _capture_ranking_snapshot(
        self,
        tournament_id: int,
        round_id: int
    ) -> int:
        """
        Capture a snapshot of current rankings for all entries.
        
        This creates RankingSnapshot records for each entry showing their
        position and total points at this moment in time.
        
        Args:
            tournament_id: Tournament ID
            round_id: Round number
            
        Returns:
            Number of snapshots created
        """
        # Get all entries for this tournament
        entries = self.db.query(Entry).filter(
            Entry.tournament_id == tournament_id
        ).all()
        
        if not entries:
            logger.warning(f"No entries found for tournament {tournament_id}")
            return 0
        
        # Calculate current rankings (same logic as get_leaderboard)
        leaderboard_data = []
        
        for entry in entries:
            # Get all daily scores for this entry
            daily_scores = self.db.query(DailyScore).filter(
                DailyScore.entry_id == entry.id
            ).order_by(DailyScore.round_id).all()
            
            total_points = sum(score.total_points for score in daily_scores)
            
            leaderboard_data.append({
                "entry_id": entry.id,
                "total_points": total_points
            })
        
        # Sort by total points descending
        leaderboard_data.sort(key=lambda x: x["total_points"], reverse=True)
        
        # Determine leader's points
        leader_points = leaderboard_data[0]["total_points"] if leaderboard_data else 0
        
        # Create ranking snapshots
        snapshots_created = 0
        for position, entry_data in enumerate(leaderboard_data, start=1):
            entry_id = entry_data["entry_id"]
            total_points = entry_data["total_points"]
            points_behind = leader_points - total_points if leader_points > 0 else 0
            
            # Always create a new snapshot to track position changes over time
            # Even if points are the same, position might have changed due to other entries
            # This allows us to see the full history of position changes
            should_create = True
            
            if should_create:
                snapshot = RankingSnapshot(
                    tournament_id=tournament_id,
                    entry_id=entry_id,
                    round_id=round_id,
                    position=position,
                    total_points=total_points,
                    points_behind_leader=points_behind,
                    timestamp=datetime.utcnow()
                )
                self.db.add(snapshot)
                snapshots_created += 1
        
        if snapshots_created > 0:
            self.db.commit()
            logger.info(
                f"Created {snapshots_created} ranking snapshots for tournament {tournament_id}, round {round_id}"
            )
        
        return snapshots_created
    
    def _notify_discord_position_changes_async(
        self,
        tournament_id: int,
        round_id: int
    ):
        """
        Check for position changes and send Discord notifications (fire-and-forget, non-blocking).
        
        Args:
            tournament_id: Tournament ID
            round_id: Round number
        """
        if not self.discord_service or not self.discord_service.enabled:
            return
        
        # Fire-and-forget async task (won't block scoring)
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # No event loop running, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Create task that runs in background
        asyncio.create_task(
            self._notify_discord_position_changes(tournament_id, round_id)
        )
    
    async def _notify_discord_position_changes(
        self,
        tournament_id: int,
        round_id: int
    ):
        """Async helper to check position changes and send Discord notifications."""
        try:
            tournament = self.db.query(Tournament).filter(
                Tournament.id == tournament_id
            ).first()
            
            if not tournament:
                return
            
            # Get current rankings
            entries = self.db.query(Entry).filter(
                Entry.tournament_id == tournament_id
            ).all()
            
            leaderboard_data = []
            for entry in entries:
                daily_scores = self.db.query(DailyScore).filter(
                    DailyScore.entry_id == entry.id
                ).order_by(DailyScore.round_id).all()
                
                total_points = sum(score.total_points for score in daily_scores)
                leaderboard_data.append({
                    "entry_id": entry.id,
                    "entry_name": entry.participant.name,
                    "total_points": total_points
                })
            
            leaderboard_data.sort(key=lambda x: x["total_points"], reverse=True)
            
            if not leaderboard_data:
                return
            
            # Check for new leader (position 1)
            current_leader = leaderboard_data[0]
            
            # Get previous snapshot to compare
            previous_snapshot = self.db.query(RankingSnapshot).filter(
                RankingSnapshot.tournament_id == tournament_id,
                RankingSnapshot.round_id == round_id
            ).order_by(RankingSnapshot.timestamp.desc()).offset(1).first()
            
            if previous_snapshot:
                # Get previous leader
                previous_leader_snapshot = self.db.query(RankingSnapshot).filter(
                    RankingSnapshot.tournament_id == tournament_id,
                    RankingSnapshot.round_id == round_id,
                    RankingSnapshot.position == 1
                ).order_by(RankingSnapshot.timestamp.desc()).offset(1).first()
                
                if previous_leader_snapshot:
                    previous_leader_entry = self.db.query(Entry).filter(
                        Entry.id == previous_leader_snapshot.entry_id
                    ).first()
                    
                    if previous_leader_entry and previous_leader_entry.id != current_leader["entry_id"]:
                        # New leader!
                        await self.discord_service.notify_new_leader(
                            entry_name=current_leader["entry_name"],
                            total_points=current_leader["total_points"],
                            previous_leader_name=previous_leader_entry.participant.name,
                            round_id=round_id,
                            tournament_name=tournament.name
                        )
                        # Also send push notification
                        self._notify_push_new_leader_async(
                            entry_name=current_leader["entry_name"],
                            total_points=current_leader["total_points"],
                            round_id=round_id,
                            tournament_name=tournament.name
                        )
            else:
                # First snapshot for this round - notify if there's a leader
                await self.discord_service.notify_new_leader(
                    entry_name=current_leader["entry_name"],
                    total_points=current_leader["total_points"],
                    previous_leader_name=None,
                    round_id=round_id,
                    tournament_name=tournament.name
                )
                # Also send push notification
                self._notify_push_new_leader_async(
                    entry_name=current_leader["entry_name"],
                    total_points=current_leader["total_points"],
                    round_id=round_id,
                    tournament_name=tournament.name
                )
            
            # Check for big position changes (5+ positions)
            for i, entry_data in enumerate(leaderboard_data, start=1):
                entry_id = entry_data["entry_id"]
                current_position = i
                
                # Get previous position for this entry
                previous_snapshot = self.db.query(RankingSnapshot).filter(
                    RankingSnapshot.tournament_id == tournament_id,
                    RankingSnapshot.entry_id == entry_id
                ).order_by(RankingSnapshot.timestamp.desc()).offset(1).first()
                
                if previous_snapshot:
                    previous_position = previous_snapshot.position
                    position_change = abs(current_position - previous_position)
                    
                    # Notify if moved 5+ positions
                    if position_change >= 5:
                        await self.discord_service.notify_big_position_change(
                            entry_name=entry_data["entry_name"],
                            old_position=previous_position,
                            new_position=current_position,
                            total_points=entry_data["total_points"],
                            round_id=round_id
                        )
                        # Also send push notification
                        self._notify_push_big_move_async(
                            entry_name=entry_data["entry_name"],
                            old_position=previous_position,
                            new_position=current_position,
                            total_points=entry_data["total_points"],
                            round_id=round_id
                        )
        except Exception as e:
            # Log but don't raise - Discord failures shouldn't break scoring
            logger.warning(f"Discord position change notification failed (non-critical): {e}")