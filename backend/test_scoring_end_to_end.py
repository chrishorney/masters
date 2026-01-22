"""End-to-end test of the scoring system."""
import sys
from datetime import date
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Tournament, Participant, Entry, DailyScore, ScoreSnapshot
from app.services.data_sync import DataSyncService
from app.services.score_calculator import ScoreCalculatorService

def main():
    """Run end-to-end scoring test."""
    print("=" * 60)
    print("End-to-End Scoring System Test")
    print("=" * 60)
    
    db: Session = SessionLocal()
    
    try:
        # Step 1: Sync tournament data from API
        print("\n1. Syncing tournament data from API...")
        sync_service = DataSyncService(db)
        results = sync_service.sync_tournament_data(tourn_id="475", year=2024)
        
        if results["errors"]:
            print(f"   ⚠️  Warnings: {results['errors']}")
        
        tournament = results["tournament"]
        print(f"   ✅ Tournament synced: {tournament.name} ({tournament.year})")
        print(f"   ✅ Players synced: {results['players_synced']}")
        print(f"   ✅ Snapshot created: Round {tournament.current_round}")
        
        # Step 2: Create a test participant and entry
        print("\n2. Creating test entry...")
        
        # Get some real player IDs from the leaderboard
        snapshot = db.query(ScoreSnapshot).filter(
            ScoreSnapshot.tournament_id == tournament.id
        ).order_by(ScoreSnapshot.timestamp.desc()).first()
        
        leaderboard_rows = snapshot.leaderboard_data.get("leaderboardRows", [])
        if len(leaderboard_rows) < 6:
            print("   ❌ Not enough players in leaderboard for test")
            return
        
        # Pick top 6 players
        test_players = [str(row["playerId"]) for row in leaderboard_rows[:6]]
        player_names = [
            f"{row.get('firstName', '')} {row.get('lastName', '')}" 
            for row in leaderboard_rows[:6]
        ]
        
        participant = Participant(
            name="Test Participant",
            email="test@example.com",
            paid=True
        )
        db.add(participant)
        db.commit()
        db.refresh(participant)
        
        entry = Entry(
            participant_id=participant.id,
            tournament_id=tournament.id,
            player1_id=test_players[0],
            player2_id=test_players[1],
            player3_id=test_players[2],
            player4_id=test_players[3],
            player5_id=test_players[4],
            player6_id=test_players[5]
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        
        print(f"   ✅ Entry created: ID {entry.id}")
        print(f"   ✅ Selected players:")
        for i, (pid, name) in enumerate(zip(test_players, player_names), 1):
            print(f"      Player {i}: {name} (ID: {pid})")
        
        # Step 3: Calculate scores for Round 1
        print("\n3. Calculating scores for Round 1...")
        calculator = ScoreCalculatorService(db)
        
        round1_result = calculator.calculate_scores_for_tournament(
            tournament_id=tournament.id,
            round_id=1
        )
        
        if round1_result.get("success"):
            print(f"   ✅ Scores calculated for {round1_result['entries_updated']} entries")
            
            # Get the daily score
            daily_score = db.query(DailyScore).filter(
                DailyScore.entry_id == entry.id,
                DailyScore.round_id == 1
            ).first()
            
            if daily_score:
                print(f"\n   Round 1 Score Breakdown:")
                print(f"   - Base Points: {daily_score.base_points}")
                print(f"   - Bonus Points: {daily_score.bonus_points}")
                print(f"   - Total Points: {daily_score.total_points}")
                
                # Show player breakdown
                if daily_score.details and "base_breakdown" in daily_score.details:
                    print(f"\n   Player Points:")
                    for player_key, player_data in daily_score.details["base_breakdown"].items():
                        pos = player_data.get("position", "N/A")
                        pts = player_data.get("points", 0)
                        status = player_data.get("status", "unknown")
                        print(f"   - {player_key}: Position {pos} ({status}) = {pts} points")
                
                # Show bonuses
                if daily_score.details and "bonuses" in daily_score.details:
                    bonuses = daily_score.details["bonuses"]
                    if bonuses:
                        print(f"\n   Bonus Points:")
                        for bonus in bonuses:
                            bonus_type = bonus.get("bonus_type", "unknown")
                            bonus_points = bonus.get("points", 0)
                            player_id = bonus.get("player_id", "team")
                            print(f"   - {bonus_type}: {bonus_points} points (player: {player_id})")
        
        # Step 4: Calculate all rounds
        print("\n4. Calculating scores for all rounds...")
        all_rounds_result = calculator.calculate_all_rounds(tournament.id)
        
        print(f"   ✅ Processed {len(all_rounds_result['rounds_processed'])} rounds")
        for round_info in all_rounds_result["rounds_processed"]:
            print(f"   - Round {round_info['round_id']}: {round_info['entries_updated']} entries updated")
        
        # Step 5: Get total score
        print("\n5. Final Score Summary...")
        all_scores = db.query(DailyScore).filter(
            DailyScore.entry_id == entry.id
        ).order_by(DailyScore.round_id).all()
        
        total_points = sum(score.total_points for score in all_scores)
        print(f"   ✅ Total Points: {total_points}")
        print(f"\n   Round-by-Round Breakdown:")
        for score in all_scores:
            print(f"   - Round {score.round_id}: {score.total_points} points "
                  f"(Base: {score.base_points}, Bonus: {score.bonus_points})")
        
        # Step 6: Test leaderboard endpoint
        print("\n6. Testing Leaderboard...")
        from app.api.public.scores import get_leaderboard
        from fastapi import Request
        
        # Create a mock request (we'll just query directly)
        leaderboard_entries = db.query(Entry).filter(
            Entry.tournament_id == tournament.id
        ).all()
        
        print(f"   ✅ Found {len(leaderboard_entries)} entries in tournament")
        
        # Calculate totals for all entries
        entry_totals = []
        for e in leaderboard_entries:
            scores = db.query(DailyScore).filter(DailyScore.entry_id == e.id).all()
            total = sum(s.total_points for s in scores)
            entry_totals.append({
                "entry_id": e.id,
                "participant": e.participant.name,
                "total": total
            })
        
        entry_totals.sort(key=lambda x: x["total"], reverse=True)
        print(f"\n   Leaderboard:")
        for i, entry_info in enumerate(entry_totals[:5], 1):  # Show top 5
            print(f"   {i}. {entry_info['participant']}: {entry_info['total']} points")
        
        print("\n" + "=" * 60)
        print("✅ End-to-End Test Complete!")
        print("=" * 60)
        print("\nSummary:")
        print(f"- Tournament: {tournament.name} ({tournament.year})")
        print(f"- Test Entry: {participant.name} (Entry ID: {entry.id})")
        print(f"- Total Points: {total_points}")
        print(f"- Rounds Calculated: {len(all_scores)}")
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
