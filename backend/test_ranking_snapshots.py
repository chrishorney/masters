"""Quick test script to verify ranking snapshots are being created."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models import Tournament, Entry, RankingSnapshot, DailyScore
from app.services.score_calculator import ScoreCalculatorService

def test_ranking_snapshots():
    """Test if ranking snapshots are being created."""
    db = SessionLocal()
    
    try:
        # Get the current tournament
        tournament = db.query(Tournament).order_by(Tournament.id.desc()).first()
        
        if not tournament:
            print("❌ No tournament found in database")
            return
        
        print(f"✅ Found tournament: {tournament.name} (ID: {tournament.id})")
        
        # Check for entries
        entries = db.query(Entry).filter(Entry.tournament_id == tournament.id).all()
        print(f"✅ Found {len(entries)} entries")
        
        if len(entries) == 0:
            print("❌ No entries found. Cannot create ranking snapshots.")
            return
        
        # Check for daily scores
        daily_scores = db.query(DailyScore).filter(
            DailyScore.entry_id.in_([e.id for e in entries])
        ).all()
        print(f"✅ Found {len(daily_scores)} daily scores")
        
        if len(daily_scores) == 0:
            print("⚠️  No daily scores found. You need to calculate scores first.")
            print("   Go to Admin → Tournament Management → Calculate Scores")
            return
        
        # Check existing ranking snapshots
        existing_snapshots = db.query(RankingSnapshot).filter(
            RankingSnapshot.tournament_id == tournament.id
        ).all()
        print(f"📊 Found {len(existing_snapshots)} existing ranking snapshots")
        
        if existing_snapshots:
            print("\nRecent snapshots:")
            for snapshot in existing_snapshots[-5:]:  # Show last 5
                print(f"  - Entry {snapshot.entry_id}: Position {snapshot.position}, "
                      f"{snapshot.total_points} pts (Round {snapshot.round_id})")
        
        # Try to manually capture a snapshot
        print("\n🔄 Attempting to manually capture ranking snapshot...")
        calculator = ScoreCalculatorService(db)
        current_round = tournament.current_round or 1
        snapshots_created = calculator._capture_ranking_snapshot(tournament.id, current_round)
        
        if snapshots_created > 0:
            print(f"✅ Successfully created {snapshots_created} ranking snapshots!")
        else:
            print("⚠️  No new snapshots created (may already exist or points unchanged)")
        
        # Check again
        final_snapshots = db.query(RankingSnapshot).filter(
            RankingSnapshot.tournament_id == tournament.id
        ).count()
        print(f"\n📊 Total ranking snapshots now: {final_snapshots}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_ranking_snapshots()
