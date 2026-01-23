#!/usr/bin/env python3
"""Diagnostic script to check tournament data integrity for 2026 tournament."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Tournament, Entry, Player, DailyScore, ScoreSnapshot, BonusPoint
from datetime import datetime

def diagnose_tournament(tournament_id: int):
    """Diagnose tournament data integrity."""
    db: Session = SessionLocal()
    
    try:
        print(f"\n{'='*80}")
        print(f"DIAGNOSING TOURNAMENT ID: {tournament_id}")
        print(f"{'='*80}\n")
        
        # 1. Check tournament exists and get details
        tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
        if not tournament:
            print(f"❌ ERROR: Tournament {tournament_id} not found!")
            return
        
        print(f"✅ Tournament Found:")
        print(f"   ID: {tournament.id}")
        print(f"   Year: {tournament.year}")
        print(f"   Name: {tournament.name}")
        print(f"   Tourn ID: {tournament.tourn_id}")
        print(f"   Org ID: {tournament.org_id}")
        print(f"   Current Round: {tournament.current_round}")
        print(f"   Start Date: {tournament.start_date}")
        print(f"   End Date: {tournament.end_date}")
        print()
        
        # 2. Check all tournaments to see if there's confusion
        all_tournaments = db.query(Tournament).order_by(Tournament.year.desc()).all()
        print(f"📊 All Tournaments in Database:")
        for t in all_tournaments:
            marker = " ⭐ CURRENT" if t.id == tournament_id else ""
            print(f"   ID {t.id}: {t.year} - {t.name} (Round {t.current_round}){marker}")
        print()
        
        # 3. Check entries for this tournament
        entries = db.query(Entry).filter(Entry.tournament_id == tournament_id).all()
        print(f"📝 Entries for Tournament {tournament_id}: {len(entries)}")
        
        # Check for entries with Min Woo Lee
        min_woo_lee_entries = []
        for entry in entries:
            players = [
                entry.player1_id, entry.player2_id, entry.player3_id,
                entry.player4_id, entry.player5_id, entry.player6_id
            ]
            if any(p and 'min' in str(p).lower() and 'woo' in str(p).lower() and 'lee' in str(p).lower() for p in players):
                min_woo_lee_entries.append(entry)
        
        if min_woo_lee_entries:
            print(f"   ⚠️  Found {len(min_woo_lee_entries)} entries with Min Woo Lee:")
            for entry in min_woo_lee_entries:
                print(f"      Entry ID {entry.id}: {entry.participant_name}")
        print()
        
        # 4. Check players - see if Min Woo Lee exists and which tournament they're from
        print(f"👤 Checking Players:")
        all_players = db.query(Player).all()
        min_woo_lee = None
        for player in all_players:
            if 'min' in player.first_name.lower() and 'woo' in player.last_name.lower() and 'lee' in player.last_name.lower():
                min_woo_lee = player
                break
        
        if min_woo_lee:
            print(f"   ✅ Found Min Woo Lee:")
            print(f"      Player ID: {min_woo_lee.player_id}")
            print(f"      Name: {min_woo_lee.first_name} {min_woo_lee.last_name}")
        else:
            print(f"   ❌ Min Woo Lee not found in players table")
        print()
        
        # 5. Check latest score snapshot for this tournament
        latest_snapshot = db.query(ScoreSnapshot).filter(
            ScoreSnapshot.tournament_id == tournament_id
        ).order_by(ScoreSnapshot.timestamp.desc()).first()
        
        if latest_snapshot:
            print(f"📸 Latest Score Snapshot:")
            print(f"   Snapshot ID: {latest_snapshot.id}")
            print(f"   Round: {latest_snapshot.round_id}")
            print(f"   Timestamp: {latest_snapshot.timestamp}")
            
            # Check leaderboard data
            leaderboard_data = latest_snapshot.leaderboard_data or {}
            leaderboard_rows = leaderboard_data.get("leaderboardRows", [])
            print(f"   Leaderboard Rows: {len(leaderboard_rows)}")
            
            # Check if Min Woo Lee is in leaderboard
            min_woo_in_leaderboard = False
            for row in leaderboard_rows:
                first_name = row.get("firstName", "").lower()
                last_name = row.get("lastName", "").lower()
                if 'min' in first_name and 'woo' in last_name and 'lee' in last_name:
                    min_woo_in_leaderboard = True
                    position = row.get("position", "N/A")
                    score = row.get("totalScore", "N/A")
                    print(f"   ✅ Min Woo Lee found in leaderboard:")
                    print(f"      Position: {position}")
                    print(f"      Score: {score}")
                    print(f"      Player ID: {row.get('playerId', 'N/A')}")
                    break
            
            if not min_woo_in_leaderboard:
                print(f"   ❌ Min Woo Lee NOT found in leaderboard snapshot")
                
                # Show top 10 players
                print(f"   Top 10 players in leaderboard:")
                for i, row in enumerate(leaderboard_rows[:10], 1):
                    name = f"{row.get('firstName', '')} {row.get('lastName', '')}"
                    pos = row.get("position", "N/A")
                    score = row.get("totalScore", "N/A")
                    print(f"      {i}. {name} - Position: {pos}, Score: {score}")
        else:
            print(f"   ❌ No score snapshots found for tournament {tournament_id}")
        print()
        
        # 6. Check daily scores for entries
        print(f"📊 Daily Scores Analysis:")
        daily_scores = db.query(DailyScore).join(Entry).filter(
            Entry.tournament_id == tournament_id
        ).all()
        print(f"   Total daily scores: {len(daily_scores)}")
        
        # Group by entry
        scores_by_entry = {}
        for score in daily_scores:
            if score.entry_id not in scores_by_entry:
                scores_by_entry[score.entry_id] = []
            scores_by_entry[score.entry_id].append(score)
        
        print(f"   Entries with scores: {len(scores_by_entry)}")
        
        # Check entries with Min Woo Lee
        if min_woo_lee_entries:
            for entry in min_woo_lee_entries:
                entry_scores = scores_by_entry.get(entry.id, [])
                total_points = sum(s.total_points for s in entry_scores)
                print(f"   Entry {entry.id} ({entry.participant_name}): {len(entry_scores)} scores, {total_points:.1f} total points")
        print()
        
        # 7. Check for cross-contamination (entries/players from wrong tournament)
        print(f"🔍 Checking for Data Contamination:")
        
        # Check entries assigned to wrong tournament
        wrong_entries = db.query(Entry).filter(Entry.tournament_id != tournament_id).all()
        if wrong_entries:
            print(f"   ⚠️  Found {len(wrong_entries)} entries assigned to other tournaments:")
            for entry in wrong_entries[:5]:  # Show first 5
                t = db.query(Tournament).filter(Tournament.id == entry.tournament_id).first()
                print(f"      Entry {entry.id} ({entry.participant_name}) -> Tournament {entry.tournament_id} ({t.year if t else 'Unknown'})")
        else:
            print(f"   ✅ No entries assigned to wrong tournaments")
        
        # Check daily scores for wrong tournament
        wrong_scores = db.query(DailyScore).join(Entry).filter(
            Entry.tournament_id != tournament_id
        ).all()
        if wrong_scores:
            print(f"   ⚠️  Found {len(wrong_scores)} daily scores for other tournaments")
        else:
            print(f"   ✅ No daily scores for wrong tournaments")
        print()
        
        # 8. Check what the leaderboard endpoint would return
        print(f"🏆 Simulating Leaderboard Endpoint:")
        leaderboard_entries = []
        for entry in entries:
            entry_scores = db.query(DailyScore).filter(
                DailyScore.entry_id == entry.id
            ).order_by(DailyScore.round_id).all()
            
            total_points = sum(score.total_points for score in entry_scores)
            
            leaderboard_entries.append({
                "entry_id": entry.id,
                "participant_name": entry.participant_name,
                "total_points": total_points,
                "num_scores": len(entry_scores)
            })
        
        leaderboard_entries.sort(key=lambda x: x["total_points"], reverse=True)
        
        print(f"   Top 10 entries:")
        for i, entry_data in enumerate(leaderboard_entries[:10], 1):
            print(f"      {i}. {entry_data['participant_name']}: {entry_data['total_points']:.1f} pts ({entry_data['num_scores']} scores)")
        
        # Check if Min Woo Lee entries are in leaderboard
        min_woo_entries_in_leaderboard = []
        for entry_data in leaderboard_entries:
            entry = next((e for e in entries if e.id == entry_data["entry_id"]), None)
            if entry and entry in min_woo_lee_entries:
                min_woo_entries_in_leaderboard.append((entry_data["rank"] if "rank" in entry_data else len(min_woo_entries_in_leaderboard) + 1, entry_data))
        
        if min_woo_entries_in_leaderboard:
            print(f"\n   ✅ Min Woo Lee entries found in leaderboard:")
            for rank, entry_data in min_woo_entries_in_leaderboard:
                print(f"      Rank {rank}: {entry_data['participant_name']} - {entry_data['total_points']:.1f} pts")
        else:
            print(f"\n   ❌ Min Woo Lee entries NOT found in leaderboard (or have 0 points)")
        print()
        
        # 9. Recommendations
        print(f"💡 Recommendations:")
        issues_found = []
        
        if not latest_snapshot:
            issues_found.append("No score snapshots - need to sync tournament data")
        
        if latest_snapshot and not min_woo_in_leaderboard:
            issues_found.append("Min Woo Lee not in latest leaderboard snapshot - may need to re-sync")
        
        if min_woo_lee_entries and not min_woo_entries_in_leaderboard:
            issues_found.append("Entries with Min Woo Lee have no scores - need to calculate scores")
        
        if not issues_found:
            print(f"   ✅ No obvious issues found")
        else:
            for issue in issues_found:
                print(f"   ⚠️  {issue}")
        
        print(f"\n{'='*80}\n")
        
    finally:
        db.close()

if __name__ == "__main__":
    # Check tournament_id=2 (should be 2026)
    diagnose_tournament(2)
    
    # Also check tournament_id=1 (2025) for comparison
    print("\n" + "="*80)
    print("COMPARING WITH TOURNAMENT ID 1 (2025)")
    print("="*80)
    diagnose_tournament(1)
