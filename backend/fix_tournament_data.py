#!/usr/bin/env python3
"""
Automated script to fix tournament data issues.

This script will:
1. Run diagnostics to identify issues
2. Clear corrupted data if needed
3. Re-sync tournament data
4. Recalculate scores

Usage:
    python fix_tournament_data.py --tournament-id 2 [--clear-all] [--api-url http://localhost:8000]
"""
import argparse
import sys
import requests
import time
from typing import Dict, Any, Optional

def run_diagnostics(api_url: str, tournament_id: int) -> Dict[str, Any]:
    """Run diagnostics on tournament."""
    print(f"\n{'='*80}")
    print(f"RUNNING DIAGNOSTICS FOR TOURNAMENT {tournament_id}")
    print(f"{'='*80}\n")
    
    url = f"{api_url}/api/admin/diagnostics/tournament/{tournament_id}"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error running diagnostics: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        sys.exit(1)

def clear_tournament_data(api_url: str, tournament_id: int) -> Dict[str, Any]:
    """Clear all scoring data for tournament."""
    print(f"\n{'='*80}")
    print(f"CLEARING TOURNAMENT DATA FOR TOURNAMENT {tournament_id}")
    print(f"{'='*80}\n")
    print("⚠️  This will delete all scoring data (snapshots, daily scores, bonus points)")
    print("⚠️  Entries and players will be preserved")
    print("\nProceeding in 3 seconds...")
    time.sleep(3)
    
    url = f"{api_url}/api/admin/diagnostics/tournament/{tournament_id}/clear"
    
    try:
        response = requests.post(url, params={"confirm": True}, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error clearing data: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        sys.exit(1)

def sync_tournament(api_url: str, year: int) -> Dict[str, Any]:
    """Sync tournament data from API."""
    print(f"\n{'='*80}")
    print(f"SYNCING TOURNAMENT DATA FOR YEAR {year}")
    print(f"{'='*80}\n")
    
    url = f"{api_url}/api/tournament/sync"
    
    try:
        response = requests.post(url, params={"year": year}, timeout=120)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error syncing tournament: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        sys.exit(1)

def calculate_scores(api_url: str, tournament_id: int, all_rounds: bool = True) -> Dict[str, Any]:
    """Calculate scores for tournament."""
    print(f"\n{'='*80}")
    print(f"CALCULATING SCORES FOR TOURNAMENT {tournament_id}")
    print(f"{'='*80}\n")
    
    if all_rounds:
        url = f"{api_url}/api/scores/calculate-all"
    else:
        url = f"{api_url}/api/scores/calculate"
    
    try:
        response = requests.post(url, params={"tournament_id": tournament_id}, timeout=120)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error calculating scores: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        sys.exit(1)

def print_diagnostics(diagnostics: Dict[str, Any]):
    """Print diagnostics results."""
    print("\n📊 DIAGNOSTICS RESULTS:")
    print("-" * 80)
    
    if diagnostics.get("tournament"):
        t = diagnostics["tournament"]
        print(f"Tournament: {t['name']} ({t['year']})")
        print(f"Current Round: {t['current_round']}")
    
    print(f"\nEntries: {diagnostics['entries']['total']}")
    print(f"  - With scores: {diagnostics['entries']['with_scores']}")
    print(f"  - Without scores: {diagnostics['entries']['without_scores']}")
    
    print(f"\nScore Snapshots: {diagnostics['snapshots']['total']}")
    if diagnostics['snapshots']['latest']:
        latest = diagnostics['snapshots']['latest']
        print(f"  - Latest: Round {latest['round_id']}, {latest['player_count']} players")
    
    print(f"\nDaily Scores: {diagnostics['daily_scores']['total']}")
    if diagnostics['daily_scores']['by_round']:
        print("  - By round:")
        for round_id, count in sorted(diagnostics['daily_scores']['by_round'].items()):
            print(f"    Round {round_id}: {count}")
    
    if diagnostics.get("min_woo_lee"):
        mwl = diagnostics["min_woo_lee"]
        if mwl.get("in_leaderboard"):
            print(f"\n✅ Min Woo Lee found in leaderboard:")
            print(f"   Position: {mwl['player_info']['position']}")
            print(f"   Entries with this player: {len(mwl.get('entries_with_player', []))}")
            for entry in mwl.get('entries_with_player', []):
                print(f"     - Entry {entry['entry_id']} ({entry['participant_name']}): "
                     f"{entry['total_points']:.1f} pts, Has scores: {entry['has_scores']}")
        else:
            print(f"\n❌ Min Woo Lee NOT found in leaderboard")
    
    if diagnostics.get("issues"):
        print(f"\n❌ ISSUES:")
        for issue in diagnostics["issues"]:
            print(f"   - {issue}")
    
    if diagnostics.get("warnings"):
        print(f"\n⚠️  WARNINGS:")
        for warning in diagnostics["warnings"]:
            print(f"   - {warning}")
    
    if diagnostics.get("recommendations"):
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in diagnostics["recommendations"]:
            print(f"   - {rec}")

def main():
    parser = argparse.ArgumentParser(description='Fix tournament data issues')
    parser.add_argument('--tournament-id', type=int, required=True, help='Tournament ID to fix')
    parser.add_argument('--clear-all', action='store_true', help='Clear all scoring data before fixing')
    parser.add_argument('--api-url', type=str, default='http://localhost:8000', 
                       help='API base URL (default: http://localhost:8000)')
    parser.add_argument('--skip-sync', action='store_true', help='Skip tournament sync step')
    parser.add_argument('--skip-calculate', action='store_true', help='Skip score calculation step')
    
    args = parser.parse_args()
    
    # Remove trailing slash from API URL
    api_url = args.api_url.rstrip('/')
    
    print("="*80)
    print("TOURNAMENT DATA FIX SCRIPT")
    print("="*80)
    print(f"Tournament ID: {args.tournament_id}")
    print(f"API URL: {api_url}")
    print(f"Clear all data: {args.clear_all}")
    print("="*80)
    
    # Step 1: Run diagnostics
    diagnostics_result = run_diagnostics(api_url, args.tournament_id)
    print_diagnostics(diagnostics_result)
    
    # Check if tournament exists
    if not diagnostics_result.get("tournament"):
        print("\n❌ Tournament not found. Exiting.")
        sys.exit(1)
    
    tournament = diagnostics_result["tournament"]
    year = tournament["year"]
    
    # Step 2: Clear data if requested
    if args.clear_all:
        clear_result = clear_tournament_data(api_url, args.tournament_id)
        print(f"\n✅ Cleared data:")
        for key, value in clear_result.get("deleted", {}).items():
            print(f"   - {key}: {value}")
    
    # Step 3: Sync tournament (unless skipped)
    if not args.skip_sync:
        sync_result = sync_tournament(api_url, year)
        print(f"\n✅ Tournament synced:")
        print(f"   Tournament ID: {sync_result.get('tournament_id')}")
        print(f"   Tournament Name: {sync_result.get('tournament_name')}")
        print(f"   Current Round: {sync_result.get('current_round')}")
        print(f"   Players Synced: {sync_result.get('players_synced')}")
        print(f"   Scorecards Fetched: {sync_result.get('scorecards_fetched', 0)}")
    
    # Step 4: Calculate scores (unless skipped)
    if not args.skip_calculate:
        calc_result = calculate_scores(api_url, args.tournament_id, all_rounds=True)
        print(f"\n✅ Scores calculated:")
        print(f"   Rounds Processed: {calc_result.get('rounds_processed', 0)}")
        print(f"   Total Entries Processed: {calc_result.get('total_entries_processed', 0)}")
        if calc_result.get("errors"):
            print(f"   Errors: {len(calc_result['errors'])}")
            for error in calc_result["errors"][:5]:  # Show first 5 errors
                print(f"     - {error}")
    
    # Step 5: Run diagnostics again to verify
    print(f"\n{'='*80}")
    print("RUNNING FINAL DIAGNOSTICS TO VERIFY FIX")
    print(f"{'='*80}\n")
    
    final_diagnostics = run_diagnostics(api_url, args.tournament_id)
    print_diagnostics(final_diagnostics)
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}\n")
    
    if final_diagnostics.get("issues"):
        print("⚠️  Some issues remain:")
        for issue in final_diagnostics["issues"]:
            print(f"   - {issue}")
    else:
        print("✅ No critical issues found!")
    
    if final_diagnostics.get("warnings"):
        print("\n⚠️  Warnings:")
        for warning in final_diagnostics["warnings"]:
            print(f"   - {warning}")
    
    print("\n✅ Fix process completed!")

if __name__ == "__main__":
    main()
