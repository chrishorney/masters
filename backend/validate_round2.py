#!/usr/bin/env python3
"""
Validation script to check Round 2 data in endpoints.

Usage:
    python validate_round2.py [--api-url URL]
    
Example:
    python validate_round2.py --api-url http://localhost:8000
    python validate_round2.py --api-url https://masters-production.up.railway.app
"""

import argparse
import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(label: str, value: Any, status: str = "✓"):
    """Print a validation result."""
    status_symbol = "✓" if status == "✓" else "✗"
    print(f"{status_symbol} {label}: {value}")


def check_endpoint(url: str, endpoint: str) -> Optional[Dict[str, Any]]:
    """Check an API endpoint."""
    full_url = f"{url.rstrip('/')}{endpoint}"
    try:
        response = requests.get(full_url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"✗ Error calling {full_url}: {e}")
        return None


def validate_round2(api_url: str):
    """Validate Round 2 data across all endpoints."""
    
    print_section("Round 2 Validation Report")
    print(f"API URL: {api_url}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # 1. Check validation endpoint
    print_section("1. Sync Status Validation")
    validation_data = check_endpoint(api_url, "/api/validation/sync-status")
    
    if validation_data:
        tournament = validation_data.get("tournament", {})
        current_round = tournament.get("current_round")
        latest_snapshot = validation_data.get("latest_snapshot", {})
        snapshot_round = latest_snapshot.get("round_id")
        validation = validation_data.get("validation", {})
        
        print_result("Tournament Name", tournament.get("name", "N/A"))
        print_result("Current Round (Database)", current_round)
        print_result("Latest Snapshot Round", snapshot_round)
        print_result("Rounds Match", 
                    validation.get("current_round_matches_latest_snapshot", False),
                    "✓" if validation.get("current_round_matches_latest_snapshot") else "✗")
        print_result("Has Snapshots", validation.get("has_snapshots", False))
        print_result("Rounds with Snapshots", validation.get("rounds_with_snapshots", []))
        
        # Check round snapshots
        round_snapshots = validation_data.get("round_snapshots", {})
        if 2 in round_snapshots:
            round2_snapshot = round_snapshots[2]
            print_result("Round 2 Snapshot Exists", "Yes")
            print_result("Round 2 Snapshot ID", round2_snapshot.get("snapshot_id"))
            print_result("Round 2 Snapshot Timestamp", round2_snapshot.get("timestamp"))
            print_result("Round 2 Has Scorecard Data", round2_snapshot.get("has_scorecard_data", False))
            if round2_snapshot.get("scorecard_players"):
                print_result("Round 2 Scorecard Players", len(round2_snapshot.get("scorecard_players", [])))
        else:
            print_result("Round 2 Snapshot Exists", "No", "✗")
        
        # Validation summary
        is_round2 = current_round == 2
        print_result("Is Round 2?", is_round2, "✓" if is_round2 else "✗")
        
        if not is_round2:
            print(f"\n⚠️  WARNING: Current round is {current_round}, not Round 2!")
    else:
        print("✗ Could not fetch validation data")
    
    # 2. Check current tournament endpoint
    print_section("2. Current Tournament Endpoint")
    tournament_data = check_endpoint(api_url, "/api/tournament/current")
    
    if tournament_data:
        print_result("Tournament Name", tournament_data.get("name", "N/A"))
        print_result("Current Round", tournament_data.get("current_round"))
        print_result("Status", tournament_data.get("status", "N/A"))
        print_result("Year", tournament_data.get("year", "N/A"))
        
        is_round2 = tournament_data.get("current_round") == 2
        print_result("Is Round 2?", is_round2, "✓" if is_round2 else "✗")
    else:
        print("✗ Could not fetch tournament data")
    
    # 3. Check leaderboard endpoint
    print_section("3. Leaderboard Endpoint")
    if tournament_data:
        tournament_id = tournament_data.get("id")
        leaderboard_data = check_endpoint(api_url, f"/api/scores/leaderboard?tournament_id={tournament_id}")
        
        if leaderboard_data:
            leaderboard_tournament = leaderboard_data.get("tournament", {})
            print_result("Tournament Name", leaderboard_tournament.get("name", "N/A"))
            print_result("Current Round", leaderboard_tournament.get("current_round"))
            print_result("Entries Count", len(leaderboard_data.get("entries", [])))
            print_result("Last Updated", leaderboard_data.get("last_updated", "N/A"))
            
            is_round2 = leaderboard_tournament.get("current_round") == 2
            print_result("Is Round 2?", is_round2, "✓" if is_round2 else "✗")
            
            # Check if entries have Round 2 scores
            entries = leaderboard_data.get("entries", [])
            if entries:
                round2_scores = []
                for entry in entries:
                    daily_scores = entry.get("daily_scores", [])
                    for score in daily_scores:
                        if score.get("round_id") == 2:
                            round2_scores.append(entry.get("entry", {}).get("id"))
                            break
                
                print_result("Entries with Round 2 Scores", len(round2_scores))
                if len(round2_scores) < len(entries):
                    print(f"⚠️  WARNING: Only {len(round2_scores)}/{len(entries)} entries have Round 2 scores")
        else:
            print("✗ Could not fetch leaderboard data")
    
    # 4. Check score snapshots
    print_section("4. Score Snapshots Summary")
    if validation_data:
        round_snapshots = validation_data.get("round_snapshots", {})
        for round_id in sorted(round_snapshots.keys()):
            snapshot = round_snapshots[round_id]
            print(f"  Round {round_id}:")
            print(f"    - Snapshot ID: {snapshot.get('snapshot_id')}")
            print(f"    - Timestamp: {snapshot.get('timestamp')}")
            print(f"    - Has Scorecard Data: {snapshot.get('has_scorecard_data')}")
            if snapshot.get('scorecard_players'):
                print(f"    - Scorecard Players: {len(snapshot.get('scorecard_players'))}")
    
    # 5. Final Summary
    print_section("5. Validation Summary")
    
    all_checks = []
    if validation_data:
        tournament = validation_data.get("tournament", {})
        all_checks.append(tournament.get("current_round") == 2)
        all_checks.append(validation_data.get("validation", {}).get("current_round_matches_latest_snapshot", False))
    
    if tournament_data:
        all_checks.append(tournament_data.get("current_round") == 2)
    
    if leaderboard_data:
        leaderboard_tournament = leaderboard_data.get("tournament", {})
        all_checks.append(leaderboard_tournament.get("current_round") == 2)
    
    all_passed = all(all_checks) if all_checks else False
    
    if all_passed:
        print("✓ ALL CHECKS PASSED - Round 2 is correctly configured!")
    else:
        print("✗ SOME CHECKS FAILED - Please review the results above")
    
    print("\n" + "=" * 60)
    print("Validation complete!")
    print("=" * 60 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate Round 2 data in API endpoints")
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="API base URL (default: http://localhost:8000)"
    )
    
    args = parser.parse_args()
    
    validate_round2(args.api_url)


if __name__ == "__main__":
    main()
