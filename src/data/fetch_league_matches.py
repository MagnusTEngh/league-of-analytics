#!/usr/bin/env python3
"""
Runner script to fetch match data from Riot Games API.

Combines functions from api modules and shares the rate-limited session between them.
Saves match data in data/match and timelines in data/timeline as compressed JSON files.
Only requests data that doesn't already exist locally.

Usage:
    python -m data.fetch_league_matches --api-key YOUR_API_KEY --region europe EUW1_1234567890
"""

import argparse
import os

from requests_ratelimiter import LimiterSession

from data.api.match import RiotMatchAPI
from data.api.utils import file_exists


def filter_existing_matches(match_ids: list, region: str, match_dir: str = "data/match") -> list:
    """
    Filter out match IDs that already have match data saved.

    Args:
        match_ids: List of match IDs to check
        region: Region prefix used in filenames
        match_dir: Directory where match files are stored

    Returns:
        List of match IDs that need to be fetched
    """
    return [mid for mid in match_ids if not file_exists(f"{region}_{mid}", match_dir)]


def filter_existing_timelines(match_ids: list, region: str, timeline_dir: str = "data/timeline") -> list:
    """
    Filter out match IDs that already have timeline data saved.

    Args:
        match_ids: List of match IDs to check
        region: Region prefix used in filenames
        timeline_dir: Directory where timeline files are stored

    Returns:
        List of match IDs that need timeline fetching
    """
    return [mid for mid in match_ids if not file_exists(f"{region}_{mid}_timeline", timeline_dir)]


def get_puuid_and_matches(api_key: str, region: str, game_name: str, tag: str, count: int = 20) -> list:
    """
    Get PUUID from game_name#tag and fetch list of match IDs.

    Args:
        api_key: Riot Games API key
        region: Region (e.g., europe, americas, asia)
        game_name: Summoner game name
        tag: Summoner tagline
        count: Number of matches to fetch

    Returns:
        List of match IDs
    """
    base_url = f"https://{region}.api.riotgames.com"
    session = LimiterSession(
        rate_limits=["20/1s", "100/2m"]
    )
    session.headers.update({"X-Riot-Token": api_key})

    url = f"{base_url}/riot/account/v1/accounts/by-riot-id/{game_name}/{tag}"
    response = session.get(url)
    response.raise_for_status()
    account_data = response.json()
    puuid = account_data["puuid"]

    url = f"{base_url}/lol/match/v5/matches/by-puuid/{puuid}/ids?count={count}"
    response = session.get(url)
    response.raise_for_status()
    match_data = response.json()

    return match_data


def main():
    parser = argparse.ArgumentParser(
        description='Fetch match data from Riot Games API and store as .json.zst files'
    )
    parser.add_argument('--api-key', required=True, help='Riot Games API key')
    parser.add_argument('--region', default='europe', 
                        help='Region (e.g., europe, americas, asia)')
    parser.add_argument('--gamename', required=True, help='Summoner game name')
    parser.add_argument('--tag', required=True, help='Summoner tagline')
    parser.add_argument('--count', type=int, default=20, help='Number of matches to fetch')
    parser.add_argument('--match-dir', default='data/match',
                        help='Directory to save match files (default: data/match)')
    parser.add_argument('--timeline-dir', default='data/timeline',
                        help='Directory to save timeline files (default: data/timeline)')
    
    args = parser.parse_args()
    
    match_ids = get_puuid_and_matches(args.api_key, args.region, args.gamename, args.tag, args.count)
    
    # Initialize API client with shared rate-limited session
    api = RiotMatchAPI(api_key=args.api_key, region=args.region)
    
    # Ensure directories exist
    os.makedirs(args.match_dir, exist_ok=True)
    os.makedirs(args.timeline_dir, exist_ok=True)
    
    print(f"\nFetching data for {len(match_ids)} matches from {args.region} region...")
    print(f"Match files: {os.path.abspath(args.match_dir)}")
    print(f"Timeline files: {os.path.abspath(args.timeline_dir)}\n")
    
    # Filter out existing matches and timelines
    matches_to_fetch = filter_existing_matches(match_ids, args.region, args.match_dir)
    timelines_to_fetch = filter_existing_timelines(match_ids, args.region, args.timeline_dir)
    
    print(f"Matches to fetch: {len(matches_to_fetch)}/{len(match_ids)}")
    print(f"Timelines to fetch: {len(timelines_to_fetch)}/{len(match_ids)}\n")
    
    # Fetch only missing matches
    if matches_to_fetch:
        print("Fetching missing match data:")
        for match_id in matches_to_fetch:
            print(f"  Fetching match: {match_id}")
            api.get_match(match_id, args.match_dir, args.timeline_dir)
        print()
    
    # Fetch only missing timelines
    if timelines_to_fetch:
        print("Fetching missing timeline data:")
        for match_id in timelines_to_fetch:
            print(f"  Fetching timeline: {match_id}")
            api.get_match_timeline(match_id, args.match_dir, args.timeline_dir)
        print()
    
    print(f"Done!")


if __name__ == '__main__':
    main()
