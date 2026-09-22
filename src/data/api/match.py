"""Module for fetching match data from Riot Games API."""

from typing import Optional, Dict, Any

import requests
from requests_ratelimiter import LimiterSession

from data.api.utils import save_compressed_json, file_exists


class RiotMatchAPI:
    """Client for fetching match data from Riot Games API."""

    # Shared session across all instances - rate limited
    _session = None

    def __init__(self, api_key: str, region: str = "europe"):
        """
        Initialize the Riot Match API client.

        Args:
            api_key: Riot Games API key
            region: Region to fetch data from (e.g., 'europe', 'americas', 'asia')
        """
        self.api_key = api_key
        self.region = region
        self.base_url = f"https://{region}.api.riotgames.com"
        
        # Create or reuse shared rate-limited session
        if RiotMatchAPI._session is None:
            RiotMatchAPI._session = LimiterSession(
                rate_limits=[
                    "20/1s",
                    "100/2m"
                ]
            )
        self.session = RiotMatchAPI._session
        self.session.headers.update({"X-Riot-Token": self.api_key})

    def get_match(self, match_id: str, match_dir: str = "data/match", timeline_dir: str = "data/timeline") -> Optional[str]:
        """
        Fetch match data by match ID and save as compressed JSON.

        Args:
            match_id: The match ID to fetch
            match_dir: Directory to save match files in
            timeline_dir: Directory to save timeline files in (unused here)

        Returns:
            Path to the saved file, or None if failed or already exists
        """
        filename = f"{self.region}_{match_id}"
        if file_exists(filename, match_dir):
            print(f"  Match data already exists: {match_dir}/{filename}.json.zst")
            return None
        
        url = f"{self.base_url}/lol/match/v5/matches/{match_id}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            filepath = save_compressed_json(data, filename, match_dir)
            print(f"  Saved match data: {filepath}")
            return filepath
        except Exception as e:
            print(f"  Error fetching match {match_id}: {e}")
            return None

    def get_match_timeline(self, match_id: str, match_dir: str = "data/match", timeline_dir: str = "data/timeline") -> Optional[str]:
        """
        Fetch match timeline by match ID and save as compressed JSON.

        Args:
            match_id: The match ID to fetch timeline for
            match_dir: Directory for match files (unused here)
            timeline_dir: Directory to save timeline files in

        Returns:
            Path to the saved file, or None if failed or already exists
        """
        filename = f"{self.region}_{match_id}_timeline"
        if file_exists(filename, timeline_dir):
            print(f"  Timeline already exists: {timeline_dir}/{filename}.json.zst")
            return None
        
        url = f"{self.base_url}/lol/match/v5/matches/{match_id}/timeline"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            filepath = save_compressed_json(data, filename, timeline_dir)
            print(f"  Saved match timeline: {filepath}")
            return filepath
        except Exception as e:
            print(f"  Error fetching timeline for match {match_id}: {e}")
            return None

    def get_match_with_timeline(self, match_id: str, match_dir: str = "data/match", timeline_dir: str = "data/timeline") -> tuple:
        """
        Fetch both match data and timeline for a given match ID.

        Args:
            match_id: The match ID to fetch
            match_dir: Directory to save match files in
            timeline_dir: Directory to save timeline files in

        Returns:
            Tuple of (match_filepath, timeline_filepath)
        """
        match_path = self.get_match(match_id, match_dir, timeline_dir)
        timeline_path = self.get_match_timeline(match_id, match_dir, timeline_dir)
        return match_path, timeline_path

    def get_matches(self, match_ids: list, match_dir: str = "data/match", timeline_dir: str = "data/timeline") -> Dict[str, tuple]:
        """
        Fetch multiple matches with their timelines.

        Args:
            match_ids: List of match IDs to fetch
            match_dir: Directory to save match files in
            timeline_dir: Directory to save timeline files in

        Returns:
            Dictionary mapping match_id to (match_path, timeline_path) tuple
        """
        results = {}
        for match_id in match_ids:
            match_path, timeline_path = self.get_match_with_timeline(match_id, match_dir, timeline_dir)
            results[match_id] = (match_path, timeline_path)
        return results
