"""Test manual bonus points (GIR/Fairways)."""
import sys
from datetime import date
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Tournament, Participant, Entry, DailyScore, ScoreSnapshot, BonusPoint
from app.services.scoring import ScoringService
from app.services.score_calculator import ScoreCalculatorService

def main():
    """Test manual bonus points."""
    print("=" * 60)
    print("Manual Bonus Points Test (GIR/Fairways)")
    print("=" * 60)
    
    db: Session = SessionLocal()
    
    try:
        # Step 1: Create test tournament and entry
        print("\n1. Setting up test data...")
        tournament = Tournament(
            year=2024,
            tourn_id="TEST2",
            org_id="1",
            name="Test Tournament 2",
            start_date=date(2024, 4, 11),
            end_date=date(2024, 4, 14),
            status="Official",
            current_round=1
        )
        db.add(tournament)
        db.commit()
        db.refresh(tournament)
        
        participant = Participant(name="Test Participant 2")
        db.add(participant)
        db.commit()
        db.refresh(participant)
        
        entry = Entry(
            participant_id=participant.id,
            tournament_id=tournament.id,
            player1_id="50525",  # Will get GIR bonus
            player2_id="47504",  # Will get Fairways bonus
            player3_id="34466",
            player4_id="57366",
            player5_id="12345",
            player6_id="67890"
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        
        # Create snapshot
        leaderboard_data = {
            "leaderboardRows": [
                {"playerId": "50525", "position": "1", "status": "complete"},
                {"playerId": "47504", "position": "2", "status": "complete"},
            ]
        }
        snapshot = ScoreSnapshot(
            tournament_id=tournament.id,
            round_id=1,
            leaderboard_data=leaderboard_data,
            scorecard_data={}
        )
        db.add(snapshot)
        db.commit()
        
        print(f"   ✅ Tournament: {tournament.name} (ID: {tournament.id})")
        print(f"   ✅ Entry: {participant.name} (Entry ID: {entry.id})")
        
        # Step 2: Calculate initial scores (without manual bonuses)
        print("\n2. Calculating initial scores...")
        scoring_service = ScoringService(db)
        daily_score = scoring_service.calculate_and_save_daily_score(
            entry=entry,
            tournament=tournament,
            leaderboard_data=leaderboard_data,
            scorecard_data={},
            round_id=1,
            score_date=tournament.start_date
        )
        
        initial_total = daily_score.total_points
        initial_bonus = daily_score.bonus_points
        print(f"   ✅ Initial Total: {initial_total} points")
        print(f"   ✅ Initial Bonus: {initial_bonus} points")
        
        # Step 3: Add GIR leader bonus manually
        print("\n3. Adding GIR leader bonus for player 50525...")
        gir_bonus = BonusPoint(
            entry_id=entry.id,
            round_id=1,
            bonus_type="gir_leader",
            points=1.0,
            player_id="50525"
        )
        db.add(gir_bonus)
        db.commit()
        print(f"   ✅ GIR bonus added")
        
        # Step 4: Add Fairways leader bonus manually
        print("\n4. Adding Fairways leader bonus for player 47504...")
        fairways_bonus = BonusPoint(
            entry_id=entry.id,
            round_id=1,
            bonus_type="fairways_leader",
            points=1.0,
            player_id="47504"
        )
        db.add(fairways_bonus)
        db.commit()
        print(f"   ✅ Fairways bonus added")
        
        # Step 5: Recalculate scores (should include manual bonuses)
        print("\n5. Recalculating scores with manual bonuses...")
        daily_score = scoring_service.calculate_and_save_daily_score(
            entry=entry,
            tournament=tournament,
            leaderboard_data=leaderboard_data,
            scorecard_data={},
            round_id=1,
            score_date=tournament.start_date
        )
        
        final_total = daily_score.total_points
        final_bonus = daily_score.bonus_points
        print(f"   ✅ Final Total: {final_total} points")
        print(f"   ✅ Final Bonus: {final_bonus} points")
        
        # Verify bonuses are included
        expected_bonus = initial_bonus + 2.0  # +1 GIR +1 Fairways
        expected_total = initial_total + 2.0
        
        print(f"\n   Expected Bonus: {expected_bonus}")
        print(f"   Actual Bonus: {final_bonus}")
        print(f"   Expected Total: {expected_total}")
        print(f"   Actual Total: {final_total}")
        
        # Check bonus points in database
        bonuses = db.query(BonusPoint).filter(
            BonusPoint.entry_id == entry.id,
            BonusPoint.round_id == 1
        ).all()
        
        print(f"\n   Bonus Points in Database:")
        for bp in bonuses:
            print(f"   - {bp.bonus_type}: {bp.points} points (player: {bp.player_id})")
        
        # Verify
        if abs(final_bonus - expected_bonus) < 0.01 and abs(final_total - expected_total) < 0.01:
            print("\n" + "=" * 60)
            print("✅ All Tests Passed!")
            print("=" * 60)
            print("\nSummary:")
            print(f"- Initial Score: {initial_total} points")
            print(f"- Added GIR bonus: +1 point")
            print(f"- Added Fairways bonus: +1 point")
            print(f"- Final Score: {final_total} points")
            print(f"- Manual bonuses preserved and included correctly!")
        else:
            print("\n" + "=" * 60)
            print("⚠️  Tests had issues")
            print("=" * 60)
        
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
