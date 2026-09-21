#!/usr/bin/env python3
"""
Runner script to fetch match data from Riot Games API.

Combines functions from api modules and shares the rate-limited session between them.
Saves match data and timelines as compressed JSON files in data/ directory.

Usage:
    python -m data.fetch_league_matches --api-key YOUR_API_KEY --region europe EUW1_1234567890
"""

import argparse
import os
import sys

from data.api.match import RiotMatchAPI


def main():
    parser = argparse.ArgumentParser(
        description='Fetch match data from Riot Games API and store as .json.zst files'
    )
    parser.add_argument('--api-key', required=True, help='Riot Games API key')
    parser.add_argument('--region', default='europe', 
                        help='Region (e.g., europe, americas, asia)')
    parser.add_argument('match_ids', nargs='+',
                        help='List of match IDs to fetch')
    parser.add_argument('--data-dir', default='data',
                        help='Directory to save data files (default: data/)')
    
    args = parser.parse_args()
    
    # Initialize API client with shared rate-limited session
    api = RiotMatchAPI(api_key=args.api_key, region=args.region)
    
    print(f"\nFetching {len(args.match_ids)} matches from {args.region} region...")
    print(f"Saving to: {os.path.abspath(args.data_dir)}\n")
    
    # Ensure data directory exists
    os.makedirs(args.data_dir, exist_ok=True)
    
    # Fetch each match with its timeline using shared session
    success_count = 0
    for match_id in args.match_ids:
        print(f"Fetching match: {match_id}")
        
        # Get match data and timeline
        match_path, timeline_path = api.get_match_with_timeline(match_id, args.data_dir)
        
        if match_path and timeline_path:
            success_count += 1
        else:
            print(f"  WARNING: Failed to fetch complete data for match {match_id}")
        print()
    
    print(f"Done! Successfully fetched {success_count}/{len(args.match_ids)} matches.")


if __name__ == '__main__':
    main()
