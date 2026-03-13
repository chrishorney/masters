#!/usr/bin/env python3
"""
Diagnostic script to check why Sahith Theegala's eagle on hole 5 wasn't detected.
Player ID: 51634, Round 1, Hole 5 (score: 3, par: 5)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Tournament, Entry, ScoreSnapshot
from app.services.data_sync import parse_mongodb_value
from app.services.scoring import ScoringService

def check_eagle_detection():
    db: Session = SessionLocal()
    try:
        # Find tournament (assuming current tournament)
        tournament = db.query(Tournament).order_by(Tournament.id.desc()).first()
        if not tournament:
            print("No tournament found")
            return
        
        print(f"Tournament: {tournament.name} (ID: {tournament.id})")
        print(f"Current Round: {tournament.current_round}\n")
        
        # Get Round 1 snapshot
        snapshot = db.query(ScoreSnapshot).filter(
            ScoreSnapshot.tournament_id == tournament.id,
            ScoreSnapshot.round_id == 1
        ).order_by(ScoreSnapshot.timestamp.desc()).first()
        
        if not snapshot:
            print("No Round 1 snapshot found")
            return
        
        print(f"Found Round 1 snapshot (ID: {snapshot.id}, timestamp: {snapshot.timestamp})\n")
        
        # Check scorecard data for player 51634
        player_id = "51634"
        scorecard_data = snapshot.scorecard_data or {}
        
        print(f"Checking scorecard data for player {player_id}...")
        print(f"Total players in scorecard_data: {len(scorecard_data)}\n")
        
        if player_id not in scorecard_data:
            print(f"❌ Player {player_id} NOT found in scorecard_data")
            print(f"Available player IDs: {list(scorecard_data.keys())[:10]}...")
            
            # Check if player_id is stored differently (as int, etc.)
            for key in scorecard_data.keys():
                if str(key) == player_id or key == int(player_id):
                    print(f"Found player with key: {key} (type: {type(key)})")
                    player_id = str(key)
                    break
        else:
            print(f"✅ Player {player_id} found in scorecard_data")
        
        if player_id in scorecard_data:
            player_scorecards = scorecard_data[player_id]
            print(f"\nPlayer has {len(player_scorecards)} scorecard(s)")
            
            # Check each scorecard
            for idx, scorecard in enumerate(player_scorecards):
                print(f"\n--- Scorecard {idx + 1} ---")
                scorecard_round_id = parse_mongodb_value(scorecard.get("roundId"))
                print(f"Round ID: {scorecard_round_id} (type: {type(scorecard_round_id)})")
                print(f"Target Round: 1 (type: {type(1)})")
                print(f"Round match: {scorecard_round_id == 1}")
                
                if scorecard_round_id == 1:
                    holes = scorecard.get("holes", {})
                    print(f"Holes found: {len(holes)}")
                    
                    # Check hole 5 specifically
                    if "5" in holes:
                        hole_data = holes["5"]
                        hole_score = parse_mongodb_value(hole_data.get("holeScore"))
                        par = parse_mongodb_value(hole_data.get("par"))
                        score_to_par = hole_score - par if (hole_score is not None and par is not None) else None
                        
                        print(f"\nHole 5 Data:")
                        print(f"  holeScore: {hole_data.get('holeScore')} -> parsed: {hole_score}")
                        print(f"  par: {hole_data.get('par')} -> parsed: {par}")
                        print(f"  score_to_par: {score_to_par}")
                        print(f"  Is eagle? {score_to_par == -2}")
                        
                        if score_to_par == -2:
                            print("\n✅ EAGLE DETECTED IN SCORECARD DATA!")
                        else:
                            print(f"\n❌ Not an eagle (expected -2, got {score_to_par})")
                    else:
                        print("❌ Hole 5 not found in holes")
                        print(f"Available holes: {list(holes.keys())[:10]}...")
        
        # Now check if any entries have this player
        print(f"\n\nChecking entries for player {player_id}...")
        entries = db.query(Entry).filter(
            Entry.tournament_id == tournament.id
        ).all()
        
        entries_with_player = []
        for entry in entries:
            player_ids = [
                str(entry.player1_id), str(entry.player2_id), str(entry.player3_id),
                str(entry.player4_id), str(entry.player5_id), str(entry.player6_id)
            ]
            if player_id in player_ids:
                entries_with_player.append(entry)
                print(f"  Entry {entry.id}: {entry.participant.name if entry.participant else 'Unknown'}")
        
        if not entries_with_player:
            print(f"❌ No entries found with player {player_id}")
        else:
            print(f"\n✅ Found {len(entries_with_player)} entry/entries with player {player_id}")
            
            # Test bonus calculation for first entry
            if entries_with_player:
                entry = entries_with_player[0]
                print(f"\nTesting bonus calculation for Entry {entry.id}...")
                
                scoring_service = ScoringService(db)
                leaderboard_data = snapshot.leaderboard_data or {}
                
                bonuses = scoring_service.calculate_bonus_points(
                    entry=entry,
                    leaderboard_data=leaderboard_data,
                    scorecard_data=scorecard_data,
                    round_id=1,
                    tournament=tournament
                )
                
                print(f"\nBonuses detected: {len(bonuses)}")
                for bonus in bonuses:
                    if bonus.get("player_id") == player_id:
                        print(f"  ✅ {bonus['bonus_type']} on hole {bonus.get('hole')} ({bonus['points']} points)")
                
                # Check if eagle for hole 5 was detected
                eagle_found = any(
                    b.get("player_id") == player_id 
                    and b.get("bonus_type") == "eagle" 
                    and b.get("hole") == 5
                    for b in bonuses
                )
                
                if eagle_found:
                    print("\n✅ EAGLE ON HOLE 5 WAS DETECTED!")
                else:
                    print("\n❌ EAGLE ON HOLE 5 WAS NOT DETECTED")
                    print("Checking why...")
                    
                    # Check player_id matching
                    player_id_str = str(player_id)
                    entry_player_ids = [
                        str(entry.player1_id), str(entry.player2_id), str(entry.player3_id),
                        str(entry.player4_id), str(entry.player5_id), str(entry.player6_id)
                    ]
                    print(f"\nEntry player IDs: {entry_player_ids}")
                    print(f"Looking for: {player_id_str}")
                    if player_id_str in entry_player_ids:
                        print("✅ Player ID matches entry")
                    else:
                        print("❌ Player ID does NOT match entry")
    
    finally:
        db.close()

if __name__ == "__main__":
    check_eagle_detection()
