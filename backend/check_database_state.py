#!/usr/bin/env python3
"""
Quick script to check database state and see what tournaments exist.
Run this to diagnose why the website shows no tournament data.
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.models import Tournament, Entry, Player, ScoreSnapshot, DailyScore

def check_database():
    """Check what's in the database."""
    print("=" * 60)
    print("Database State Check")
    print("=" * 60)
    
    # Create database connection
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Check connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
        
        # Check tournaments
        tournaments = db.query(Tournament).all()
        print(f"\n📊 Tournaments in database: {len(tournaments)}")
        
        if tournaments:
            for t in tournaments:
                print(f"  - ID: {t.id}, Year: {t.year}, Name: {t.name}")
                print(f"    Tourn ID: {t.tourn_id}, Org ID: {t.org_id}")
                print(f"    Current Round: {t.current_round}")
                print(f"    Start: {t.start_date}, End: {t.end_date}")
                print()
        else:
            print("  ⚠️  NO TOURNAMENTS FOUND IN DATABASE")
            print("  This is why the website shows no data!")
        
        # Check entries
        entries = db.query(Entry).all()
        print(f"📝 Entries in database: {len(entries)}")
        
        if entries:
            # Group by tournament
            by_tournament = {}
            for e in entries:
                tid = e.tournament_id
                if tid not in by_tournament:
                    by_tournament[tid] = []
                by_tournament[tid].append(e)
            
            for tid, entry_list in by_tournament.items():
                print(f"  Tournament {tid}: {len(entry_list)} entries")
        else:
            print("  ⚠️  NO ENTRIES FOUND IN DATABASE")
        
        # Check players
        players = db.query(Player).all()
        print(f"👤 Players in database: {len(players)}")
        
        # Check score snapshots
        snapshots = db.query(ScoreSnapshot).all()
        print(f"📸 Score snapshots in database: {len(snapshots)}")
        
        if snapshots:
            by_tournament = {}
            for s in snapshots:
                tid = s.tournament_id
                if tid not in by_tournament:
                    by_tournament[tid] = []
                by_tournament[tid].append(s)
            
            for tid, snap_list in by_tournament.items():
                print(f"  Tournament {tid}: {len(snap_list)} snapshots")
        
        # Check daily scores
        daily_scores = db.query(DailyScore).all()
        print(f"📊 Daily scores in database: {len(daily_scores)}")
        
        print("\n" + "=" * 60)
        print("Summary:")
        print("=" * 60)
        
        if not tournaments:
            print("❌ NO TOURNAMENTS - This is the problem!")
            print("   Solution: Sync a tournament using the admin page")
        elif not entries:
            print("⚠️  Tournaments exist but no entries")
            print("   Solution: Import entries using the admin page")
        else:
            print("✅ Database has tournaments and entries")
            print("   If website still shows no data, check:")
            print("   1. Database connection in Railway")
            print("   2. API endpoint /api/tournament/current")
            print("   3. Frontend API URL configuration")
        
    except Exception as e:
        print(f"\n❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_database()
