#!/usr/bin/env python3
"""
Generate a test CSV file with 3 users and random players from tournament 2.

Usage:
    python3 generate_test_csv.py --tournament-id 2 --api-url https://masters-production.up.railway.app
"""
import argparse
import sys
import requests
import csv
import random
from typing import List, Dict, Any

def get_tournament_players(api_url: str, tournament_id: int) -> List[Dict[str, Any]]:
    """Get list of players from tournament."""
    url = f"{api_url}/api/admin/players/tournament/{tournament_id}"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("players", [])
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching players: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        sys.exit(1)

def generate_csv(players: List[Dict[str, Any]], output_file: str, num_users: int = 3):
    """Generate CSV file with random players for test users."""
    if len(players) < 6:
        print(f"❌ Error: Need at least 6 players, but only {len(players)} found")
        sys.exit(1)
    
    # Test user names
    user_names = [
        "Test User 1",
        "Test User 2",
        "Test User 3"
    ]
    
    # Generate CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'Participant Name',
            'Player 1 Name',
            'Player 2 Name',
            'Player 3 Name',
            'Player 4 Name',
            'Player 5 Name',
            'Player 6 Name'
        ]
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Generate entries for each user
        for i, user_name in enumerate(user_names[:num_users]):
            # Select 6 random players (without replacement)
            selected_players = random.sample(players, 6)
            
            # Use full_name for player names
            player_names = [p['full_name'] for p in selected_players]
            
            writer.writerow({
                'Participant Name': user_name,
                'Player 1 Name': player_names[0],
                'Player 2 Name': player_names[1],
                'Player 3 Name': player_names[2],
                'Player 4 Name': player_names[3],
                'Player 5 Name': player_names[4],
                'Player 6 Name': player_names[5]
            })
            
            print(f"✅ Generated entry for {user_name}:")
            for j, player in enumerate(selected_players, 1):
                print(f"   Player {j}: {player['full_name']} (Position: {player.get('position', 'N/A')})")
    
    print(f"\n✅ CSV file generated: {output_file}")
    print(f"   Total entries: {num_users}")
    print(f"   Players per entry: 6")

def main():
    parser = argparse.ArgumentParser(description='Generate test CSV file with random players')
    parser.add_argument('--tournament-id', type=int, default=2, help='Tournament ID (default: 2)')
    parser.add_argument('--api-url', type=str, default='http://localhost:8000',
                       help='API base URL (default: http://localhost:8000)')
    parser.add_argument('--output', type=str, default='test_entries.csv',
                       help='Output CSV file (default: test_entries.csv)')
    parser.add_argument('--num-users', type=int, default=3,
                       help='Number of test users (default: 3)')
    
    args = parser.parse_args()
    
    # Remove trailing slash from API URL
    api_url = args.api_url.rstrip('/')
    
    print("="*80)
    print("GENERATE TEST CSV FILE")
    print("="*80)
    print(f"Tournament ID: {args.tournament_id}")
    print(f"API URL: {api_url}")
    print(f"Output file: {args.output}")
    print(f"Number of users: {args.num_users}")
    print("="*80)
    
    # Get players from tournament
    print(f"\n📥 Fetching players from tournament {args.tournament_id}...")
    players = get_tournament_players(api_url, args.tournament_id)
    
    if not players:
        print("❌ No players found in tournament. Make sure tournament data is synced.")
        sys.exit(1)
    
    print(f"✅ Found {len(players)} players")
    
    # Generate CSV
    print(f"\n📝 Generating CSV file...")
    generate_csv(players, args.output, args.num_users)
    
    print(f"\n{'='*80}")
    print("NEXT STEPS:")
    print(f"{'='*80}")
    print(f"1. Clear existing entries:")
    print(f"   curl -X POST \"{api_url}/api/admin/diagnostics/tournament/{args.tournament_id}/clear-entries?confirm=true\"")
    print(f"\n2. Import the CSV file:")
    print(f"   curl -X POST \"{api_url}/api/admin/import/entries\" \\")
    print(f"     -F \"tournament_id={args.tournament_id}\" \\")
    print(f"     -F \"file=@{args.output}\"")

if __name__ == "__main__":
    main()
