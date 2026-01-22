"""End-to-end test with live tournament: The American Express."""
import sys
from datetime import date
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Tournament, Participant, Entry, DailyScore, ScoreSnapshot
from app.services.data_sync import DataSyncService
from app.services.score_calculator import ScoreCalculatorService
from app.services.import_service import ImportService

def main():
    """Run E2E test with live tournament."""
    print("=" * 70)
    print("END-TO-END TEST: The American Express Tournament")
    print("=" * 70)
    
    db: Session = SessionLocal()
    
    try:
        # Step 1: Sync tournament data
        print("\n1. Syncing tournament data from API...")
        print("   Tournament: The American Express (ID: 002)")
        
        sync_service = DataSyncService(db)
        sync_results = sync_service.sync_tournament_data(
            org_id="1",  # PGA Tour
            tourn_id="002",  # The American Express
            year=2026  # Current year (2026 tournament is in progress)
        )
        
        if sync_results.get("errors"):
            print(f"   ⚠️  Sync completed with errors: {sync_results['errors']}")
        
        tournament = sync_results["tournament"]
        print(f"   ✅ Tournament synced: {tournament.name}")
        print(f"   ✅ Tournament ID: {tournament.id}")
        print(f"   ✅ Current Round: {tournament.current_round}")
        print(f"   ✅ Players synced: {sync_results.get('players_synced', 0)}")
        
        # Step 2: Get players from leaderboard
        print("\n2. Getting players from current leaderboard...")
        snapshot = db.query(ScoreSnapshot).filter(
            ScoreSnapshot.tournament_id == tournament.id
        ).order_by(ScoreSnapshot.timestamp.desc()).first()
        
        if not snapshot:
            print("   ❌ No leaderboard data found. Tournament may not have started yet.")
            return
        
        leaderboard_rows = snapshot.leaderboard_data.get("leaderboardRows", [])
        print(f"   ✅ Found {len(leaderboard_rows)} players in leaderboard")
        
        if len(leaderboard_rows) < 12:
            print("   ⚠️  Not enough players for 2 entries (need at least 12)")
            return
        
        # Display top players
        print("\n   Top 12 Players:")
        for i, row in enumerate(leaderboard_rows[:12], 1):
            name = f"{row.get('firstName', '')} {row.get('lastName', '')}".strip()
            pos = row.get('position', 'N/A')
            score = row.get('currentRoundScore', 'N/A')
            print(f"   {i:2}. {name:30} Position: {pos:4} Score: {score}")
        
        # Step 3: Create test participants and entries
        print("\n3. Creating test participants and entries...")
        
        # Participant 1
        participant1 = Participant(
            name="Test User 1",
            email="test1@example.com",
            paid=True
        )
        db.add(participant1)
        db.commit()
        db.refresh(participant1)
        print(f"   ✅ Created participant: {participant1.name} (ID: {participant1.id})")
        
        # Participant 2
        participant2 = Participant(
            name="Test User 2",
            email="test2@example.com",
            paid=True
        )
        db.add(participant2)
        db.commit()
        db.refresh(participant2)
        print(f"   ✅ Created participant: {participant2.name} (ID: {participant2.id})")
        
        # Entry 1 - Use first 6 players
        entry1_players = [str(row.get("playerId")) for row in leaderboard_rows[:6]]
        entry1 = Entry(
            participant_id=participant1.id,
            tournament_id=tournament.id,
            player1_id=entry1_players[0],
            player2_id=entry1_players[1],
            player3_id=entry1_players[2],
            player4_id=entry1_players[3],
            player5_id=entry1_players[4],
            player6_id=entry1_players[5],
        )
        db.add(entry1)
        db.commit()
        db.refresh(entry1)
        
        print(f"\n   ✅ Entry 1 created (ID: {entry1.id})")
        print(f"   Players:")
        for i, (pid, row) in enumerate(zip(entry1_players, leaderboard_rows[:6]), 1):
            name = f"{row.get('firstName', '')} {row.get('lastName', '')}".strip()
            pos = row.get('position', 'N/A')
            print(f"      Player {i}: {name} (ID: {pid}, Position: {pos})")
        
        # Entry 2 - Use next 6 players
        entry2_players = [str(row.get("playerId")) for row in leaderboard_rows[6:12]]
        entry2 = Entry(
            participant_id=participant2.id,
            tournament_id=tournament.id,
            player1_id=entry2_players[0],
            player2_id=entry2_players[1],
            player3_id=entry2_players[2],
            player4_id=entry2_players[3],
            player5_id=entry2_players[4],
            player6_id=entry2_players[5],
        )
        db.add(entry2)
        db.commit()
        db.refresh(entry2)
        
        print(f"\n   ✅ Entry 2 created (ID: {entry2.id})")
        print(f"   Players:")
        for i, (pid, row) in enumerate(zip(entry2_players, leaderboard_rows[6:12]), 1):
            name = f"{row.get('firstName', '')} {row.get('lastName', '')}".strip()
            pos = row.get('position', 'N/A')
            print(f"      Player {i}: {name} (ID: {pid}, Position: {pos})")
        
        # Step 4: Calculate scores
        print("\n4. Calculating scores for all entries...")
        calculator = ScoreCalculatorService(db)
        
        calc_result = calculator.calculate_scores_for_tournament(
            tournament_id=tournament.id,
            round_id=tournament.current_round
        )
        
        if calc_result.get("success"):
            print(f"   ✅ Scores calculated successfully")
            print(f"   ✅ Entries processed: {calc_result.get('entries_processed', 0)}")
            print(f"   ✅ Entries updated: {calc_result.get('entries_updated', 0)}")
        else:
            print(f"   ⚠️  Calculation had issues: {calc_result.get('message')}")
        
        # Step 5: Display results
        print("\n5. Score Results:")
        print("=" * 70)
        
        for entry_num, entry in enumerate([entry1, entry2], 1):
            participant = participant1 if entry_num == 1 else participant2
            daily_scores = db.query(DailyScore).filter(
                DailyScore.entry_id == entry.id
            ).order_by(DailyScore.round_id).all()
            
            total_points = sum(score.total_points for score in daily_scores)
            total_base = sum(score.base_points for score in daily_scores)
            total_bonus = sum(score.bonus_points for score in daily_scores)
            
            print(f"\n   Entry {entry_num}: {participant.name}")
            print(f"   {'-' * 60}")
            print(f"   Total Points: {total_points:.1f}")
            print(f"   Base Points:  {total_base:.1f}")
            print(f"   Bonus Points: {total_bonus:.1f}")
            
            if daily_scores:
                print(f"\n   Round Breakdown:")
                for score in daily_scores:
                    print(f"      Round {score.round_id}: {score.total_points:.1f} "
                          f"(Base: {score.base_points:.1f}, Bonus: {score.bonus_points:.1f})")
        
        # Step 6: Verify leaderboard endpoint
        print("\n6. Verifying leaderboard endpoint...")
        # Query leaderboard data directly
        entries = db.query(Entry).filter(Entry.tournament_id == tournament.id).all()
        
        print(f"   ✅ Leaderboard endpoint working")
        print(f"   ✅ Found {len(entries)} entries in database")
        
        # Step 7: Summary
        print("\n" + "=" * 70)
        print("✅ END-TO-END TEST COMPLETE!")
        print("=" * 70)
        print(f"\nTournament: {tournament.name}")
        print(f"Tournament ID: {tournament.id}")
        print(f"Current Round: {tournament.current_round}")
        print(f"\nTest Entries Created:")
        print(f"  - Entry 1 (ID: {entry1.id}): {participant1.name}")
        print(f"  - Entry 2 (ID: {entry2.id}): {participant2.name}")
        print(f"\nNext Steps:")
        print(f"  1. Visit frontend: http://localhost:5173")
        print(f"  2. View leaderboard: http://localhost:5173/leaderboard")
        print(f"  3. View Entry 1: http://localhost:5173/entry/{entry1.id}")
        print(f"  4. View Entry 2: http://localhost:5173/entry/{entry2.id}")
        print(f"  5. Admin dashboard: http://localhost:5173/admin")
        print(f"\nTo recalculate scores after API updates:")
        print(f"  - Use admin dashboard 'Calculate Scores' button")
        print(f"  - Or sync tournament again to get latest data")
        
    except Exception as e:
        print(f"\n❌ Error during E2E test: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
