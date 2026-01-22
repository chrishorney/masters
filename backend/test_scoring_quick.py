"""Quick scoring test with minimal data."""
import sys
from datetime import date
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Tournament, Participant, Entry, DailyScore, ScoreSnapshot
from app.services.scoring import ScoringService
from app.services.score_calculator import ScoreCalculatorService

def main():
    """Run quick scoring test."""
    print("=" * 60)
    print("Quick Scoring System Test")
    print("=" * 60)
    
    db: Session = SessionLocal()
    
    try:
        # Step 1: Create a test tournament
        print("\n1. Creating test tournament...")
        tournament = Tournament(
            year=2024,
            tourn_id="TEST",
            org_id="1",
            name="Test Tournament",
            start_date=date(2024, 4, 11),
            end_date=date(2024, 4, 14),
            status="Official",
            current_round=1
        )
        db.add(tournament)
        db.commit()
        db.refresh(tournament)
        print(f"   ✅ Tournament created: {tournament.name} (ID: {tournament.id})")
        
        # Step 2: Create test leaderboard data
        print("\n2. Creating test leaderboard data...")
        leaderboard_data = {
            "leaderboardRows": [
                {"playerId": "50525", "position": "1", "status": "complete", "firstName": "Collin", "lastName": "Morikawa", "currentRoundScore": "-5"},
                {"playerId": "47504", "position": "2", "status": "complete", "firstName": "Sam", "lastName": "Burns", "currentRoundScore": "-4"},
                {"playerId": "34466", "position": "5", "status": "complete", "firstName": "Peter", "lastName": "Malnati", "currentRoundScore": "-3"},
                {"playerId": "57366", "position": "10", "status": "complete", "firstName": "Cameron", "lastName": "Young", "currentRoundScore": "-2"},
                {"playerId": "12345", "position": "20", "status": "complete", "firstName": "Test", "lastName": "Player1", "currentRoundScore": "-1"},
                {"playerId": "67890", "position": "30", "status": "complete", "firstName": "Test", "lastName": "Player2", "currentRoundScore": "E"},
            ]
        }
        
        # Create snapshot
        snapshot = ScoreSnapshot(
            tournament_id=tournament.id,
            round_id=1,
            leaderboard_data=leaderboard_data,
            scorecard_data={}
        )
        db.add(snapshot)
        db.commit()
        print(f"   ✅ Snapshot created for Round 1")
        
        # Step 3: Create test entry
        print("\n3. Creating test entry...")
        participant = Participant(name="Test Participant", email="test@example.com")
        db.add(participant)
        db.commit()
        db.refresh(participant)
        
        entry = Entry(
            participant_id=participant.id,
            tournament_id=tournament.id,
            player1_id="50525",  # Position 1
            player2_id="47504",  # Position 2
            player3_id="34466",  # Position 5
            player4_id="57366",  # Position 10
            player5_id="12345",  # Position 20
            player6_id="67890",  # Position 30
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        print(f"   ✅ Entry created: {participant.name} (Entry ID: {entry.id})")
        
        # Step 4: Calculate scores
        print("\n4. Calculating scores for Round 1...")
        scoring_service = ScoringService(db)
        
        daily_score = scoring_service.calculate_and_save_daily_score(
            entry=entry,
            tournament=tournament,
            leaderboard_data=leaderboard_data,
            scorecard_data={},
            round_id=1,
            score_date=tournament.start_date
        )
        
        print(f"\n   ✅ Score Calculated!")
        print(f"\n   Round 1 Score Breakdown:")
        print(f"   - Base Points: {daily_score.base_points}")
        print(f"   - Bonus Points: {daily_score.bonus_points}")
        print(f"   - Total Points: {daily_score.total_points}")
        
        # Expected points for Round 1:
        # Player 1 (position 1): 8 points (leader)
        # Player 2 (position 2): 5 points (top 5)
        # Player 3 (position 5): 5 points (top 5)
        # Player 4 (position 10): 3 points (top 10)
        # Player 5 (position 20): 1 point (top 25)
        # Player 6 (position 30): 0 points (outside top 25 in round 1)
        # Expected total: 8 + 5 + 5 + 3 + 1 + 0 = 22 points
        
        expected_base = 22.0
        print(f"\n   Expected Base Points: {expected_base}")
        print(f"   Actual Base Points: {daily_score.base_points}")
        
        if abs(daily_score.base_points - expected_base) < 0.01:
            print(f"   ✅ Base points match expected value!")
        else:
            print(f"   ⚠️  Base points don't match (expected {expected_base}, got {daily_score.base_points})")
        
        # Show player breakdown
        if daily_score.details and "base_breakdown" in daily_score.details:
            print(f"\n   Player Points Breakdown:")
            for player_key, player_data in sorted(daily_score.details["base_breakdown"].items()):
                pos = player_data.get("position", "N/A")
                pts = player_data.get("points", 0)
                player_id = player_data.get("player_id", "N/A")
                print(f"   - {player_key} (ID: {player_id}): Position {pos} = {pts} points")
        
        # Test position point calculation directly
        print("\n5. Testing position point calculations...")
        scoring_service = ScoringService(db)
        
        test_cases = [
            ("1", 1, 8.0, "Round 1 Leader"),
            ("2", 1, 5.0, "Round 1 Top 5"),
            ("5", 1, 5.0, "Round 1 Top 5"),
            ("10", 1, 3.0, "Round 1 Top 10"),
            ("25", 1, 1.0, "Round 1 Top 25"),
            ("1", 2, 12.0, "Round 2 Leader"),
            ("30", 2, 1.0, "Round 2 Made Cut"),
            ("1", 4, 15.0, "Round 4 Winner (with is_winner=True)"),
        ]
        
        all_passed = True
        for position, round_id, expected, description in test_cases:
            is_winner = (round_id == 4 and position == "1" and expected == 15.0)
            actual = scoring_service.calculate_position_points(position, round_id, is_winner)
            passed = abs(actual - expected) < 0.01
            status = "✅" if passed else "❌"
            print(f"   {status} {description}: {actual} (expected {expected})")
            if not passed:
                all_passed = False
        
        print("\n" + "=" * 60)
        if all_passed and abs(daily_score.base_points - expected_base) < 0.01:
            print("✅ All Tests Passed!")
        else:
            print("⚠️  Some tests had issues")
        print("=" * 60)
        
        print(f"\nSummary:")
        print(f"- Tournament: {tournament.name} ({tournament.year})")
        print(f"- Entry: {participant.name} (ID: {entry.id})")
        print(f"- Round 1 Total: {daily_score.total_points} points")
        print(f"- Base Points: {daily_score.base_points}")
        print(f"- Bonus Points: {daily_score.bonus_points}")
        
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
