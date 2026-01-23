#!/usr/bin/env python3
"""
Diagnostic and repair script for tournament data integrity.

This script will:
1. Check tournament data integrity for tournament_id=2 (2026)
2. Identify any issues with entries, players, scores, or snapshots
3. Optionally clear and rebuild all data for tournament_id=2

Usage:
    python check_and_fix_tournament_data.py [--fix] [--clear-all]
    
    --fix: Automatically fix issues where possible
    --clear-all: Clear all data for tournament_id=2 and prepare for rebuild
"""
import sys
import os
import argparse
sys.path.insert(0, os.path.dirname(__file__))

# Set up environment before importing app modules
os.environ.setdefault('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/masters')

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.database import SessionLocal
from app.models import (
    Tournament, Entry, Player, DailyScore, ScoreSnapshot, 
    BonusPoint, RankingSnapshot, Participant
)

def check_tournament_integrity(tournament_id: int, db: Session) -> dict:
    """Check data integrity for a tournament."""
    issues = []
    warnings = []
    info = []
    
    # 1. Check tournament exists
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        issues.append(f"Tournament {tournament_id} not found!")
        return {"issues": issues, "warnings": warnings, "info": info}
    
    info.append(f"Tournament: {tournament.name} ({tournament.year})")
    info.append(f"Current Round: {tournament.current_round}")
    
    # 2. Check entries
    entries = db.query(Entry).filter(Entry.tournament_id == tournament_id).all()
    info.append(f"Entries: {len(entries)}")
    
    # Check for entries with wrong tournament_id
    wrong_entries = db.query(Entry).filter(
        and_(
            Entry.tournament_id != tournament_id,
            or_(
                Entry.player1_id.in_([e.player1_id for e in entries if e.player1_id]),
                Entry.player2_id.in_([e.player2_id for e in entries if e.player2_id]),
            )
        )
    ).all()
    
    if wrong_entries:
        warnings.append(f"Found {len(wrong_entries)} entries in other tournaments that might conflict")
    
    # 3. Check score snapshots
    snapshots = db.query(ScoreSnapshot).filter(
        ScoreSnapshot.tournament_id == tournament_id
    ).order_by(ScoreSnapshot.timestamp.desc()).all()
    
    info.append(f"Score Snapshots: {len(snapshots)}")
    
    if not snapshots:
        issues.append("No score snapshots found - need to sync tournament data")
    else:
        latest_snapshot = snapshots[0]
        info.append(f"Latest Snapshot: Round {latest_snapshot.round_id}, {latest_snapshot.timestamp}")
        
        # Check if snapshot has leaderboard data
        if not latest_snapshot.leaderboard_data:
            issues.append("Latest snapshot has no leaderboard data")
        else:
            leaderboard_rows = latest_snapshot.leaderboard_data.get("leaderboardRows", [])
            info.append(f"Players in latest snapshot: {len(leaderboard_rows)}")
    
    # 4. Check daily scores
    daily_scores = db.query(DailyScore).join(Entry).filter(
        Entry.tournament_id == tournament_id
    ).all()
    
    info.append(f"Daily Scores: {len(daily_scores)}")
    
    # Check entries with no scores
    entries_with_scores = set()
    for score in daily_scores:
        entries_with_scores.add(score.entry_id)
    
    entries_without_scores = [e for e in entries if e.id not in entries_with_scores]
    if entries_without_scores:
        warnings.append(f"{len(entries_without_scores)} entries have no daily scores")
    
    # 5. Check for Min Woo Lee specifically
    min_woo_entries = []
    for entry in entries:
        players = [
            entry.player1_id, entry.player2_id, entry.player3_id,
            entry.player4_id, entry.player5_id, entry.player6_id
        ]
        # Check if any player ID might be Min Woo Lee
        # We'll check by looking in the leaderboard
        if snapshots:
            latest = snapshots[0]
            if latest.leaderboard_data:
                leaderboard_rows = latest.leaderboard_data.get("leaderboardRows", [])
                for row in leaderboard_rows:
                    first_name = row.get("firstName", "").lower()
                    last_name = row.get("lastName", "").lower()
                    player_id = str(row.get("playerId", ""))
                    if 'min' in first_name and 'woo' in last_name and 'lee' in last_name:
                        if player_id in [str(p) for p in players if p]:
                            min_woo_entries.append({
                                "entry_id": entry.id,
                                "participant": entry.participant.name if entry.participant else "Unknown",
                                "player_id": player_id,
                                "position": row.get("position"),
                                "has_scores": entry.id in entries_with_scores
                            })
    
    if min_woo_entries:
        info.append(f"\nMin Woo Lee Entries Found: {len(min_woo_entries)}")
        for entry_info in min_woo_entries:
            info.append(f"  Entry {entry_info['entry_id']} ({entry_info['participant']}): "
                       f"Position {entry_info['position']}, Has Scores: {entry_info['has_scores']}")
    else:
        warnings.append("No entries with Min Woo Lee found in current leaderboard")
    
    # 6. Check for cross-contamination
    wrong_snapshots = db.query(ScoreSnapshot).filter(
        ScoreSnapshot.tournament_id != tournament_id
    ).count()
    
    if wrong_snapshots > 0:
        info.append(f"Other tournament snapshots in DB: {wrong_snapshots}")
    
    return {
        "issues": issues,
        "warnings": warnings,
        "info": info,
        "tournament": tournament,
        "entries": entries,
        "snapshots": snapshots,
        "daily_scores": daily_scores,
        "min_woo_entries": min_woo_entries
    }

def clear_tournament_data(tournament_id: int, db: Session):
    """Clear all data for a tournament (use with caution!)."""
    print(f"\n⚠️  CLEARING ALL DATA FOR TOURNAMENT {tournament_id}")
    print("This will delete:")
    print("  - All daily scores for entries in this tournament")
    print("  - All bonus points for entries in this tournament")
    print("  - All ranking snapshots for entries in this tournament")
    print("  - All score snapshots for this tournament")
    print("\n⚠️  Entries and players will NOT be deleted")
    print("\nPress Ctrl+C to cancel, or wait 5 seconds...")
    
    import time
    time.sleep(5)
    
    # Get entries for this tournament
    entries = db.query(Entry).filter(Entry.tournament_id == tournament_id).all()
    entry_ids = [e.id for e in entries]
    
    if entry_ids:
        # Delete daily scores
        deleted_scores = db.query(DailyScore).filter(
            DailyScore.entry_id.in_(entry_ids)
        ).delete(synchronize_session=False)
        print(f"Deleted {deleted_scores} daily scores")
        
        # Delete bonus points
        deleted_bonuses = db.query(BonusPoint).filter(
            BonusPoint.entry_id.in_(entry_ids)
        ).delete(synchronize_session=False)
        print(f"Deleted {deleted_bonuses} bonus points")
        
        # Delete ranking snapshots
        deleted_rankings = db.query(RankingSnapshot).filter(
            RankingSnapshot.entry_id.in_(entry_ids)
        ).delete(synchronize_session=False)
        print(f"Deleted {deleted_rankings} ranking snapshots")
    
    # Delete score snapshots
    deleted_snapshots = db.query(ScoreSnapshot).filter(
        ScoreSnapshot.tournament_id == tournament_id
    ).delete(synchronize_session=False)
    print(f"Deleted {deleted_snapshots} score snapshots")
    
    db.commit()
    print(f"\n✅ All data cleared for tournament {tournament_id}")
    print("Next steps:")
    print("  1. Sync tournament data: POST /api/tournament/sync?year=2026")
    print("  2. Calculate scores: POST /api/scores/calculate-all?tournament_id=2")

def main():
    parser = argparse.ArgumentParser(description='Check and fix tournament data integrity')
    parser.add_argument('--fix', action='store_true', help='Automatically fix issues')
    parser.add_argument('--clear-all', action='store_true', help='Clear all data for tournament_id=2')
    parser.add_argument('--tournament-id', type=int, default=2, help='Tournament ID to check (default: 2)')
    
    args = parser.parse_args()
    
    db: Session = SessionLocal()
    
    try:
        print("="*80)
        print("TOURNAMENT DATA INTEGRITY CHECK")
        print("="*80)
        
        result = check_tournament_integrity(args.tournament_id, db)
        
        print("\n📊 INFORMATION:")
        for info in result["info"]:
            print(f"  {info}")
        
        if result["warnings"]:
            print("\n⚠️  WARNINGS:")
            for warning in result["warnings"]:
                print(f"  - {warning}")
        
        if result["issues"]:
            print("\n❌ ISSUES FOUND:")
            for issue in result["issues"]:
                print(f"  - {issue}")
        else:
            print("\n✅ No critical issues found")
        
        if args.clear_all:
            clear_tournament_data(args.tournament_id, db)
        elif args.fix:
            print("\n🔧 Auto-fix not yet implemented")
            print("Use --clear-all to clear and rebuild data")
        
        print("\n" + "="*80)
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
