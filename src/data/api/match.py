"""Module for fetching match data from Riot Games API."""

from typing import Optional, Dict, Any

import requests
from requests_ratelimiter import LimiterSession

from data.api.utils import save_compressed_json


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

    def get_match(self, match_id: str, data_dir: str = "data") -> Optional[str]:
        """
        Fetch match data by match ID and save as compressed JSON.

        Args:
            match_id: The match ID to fetch
            data_dir: Directory to save the file in

        Returns:
            Path to the saved file, or None if failed
        """
        url = f"{self.base_url}/lol/match/v5/matches/{match_id}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            filename = f"{self.region}_{match_id}"
            filepath = save_compressed_json(data, filename, data_dir)
            print(f"Saved match data: {filepath}")
            return filepath
        except Exception as e:
            print(f"Error fetching match {match_id}: {e}")
            return None

    def get_match_timeline(self, match_id: str, data_dir: str = "data") -> Optional[str]:
        """
        Fetch match timeline by match ID and save as compressed JSON.

        Args:
            match_id: The match ID to fetch timeline for
            data_dir: Directory to save the file in

        Returns:
            Path to the saved file, or None if failed
        """
        url = f"{self.base_url}/lol/match/v5/matches/{match_id}/timeline"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            filename = f"{self.region}_{match_id}_timeline"
            filepath = save_compressed_json(data, filename, data_dir)
            print(f"Saved match timeline: {filepath}")
            return filepath
        except Exception as e:
            print(f"Error fetching timeline for match {match_id}: {e}")
            return None

    def get_match_with_timeline(self, match_id: str, data_dir: str = "data") -> tuple:
        """
        Fetch both match data and timeline for a given match ID.

        Args:
            match_id: The match ID to fetch
            data_dir: Directory to save files in

        Returns:
            Tuple of (match_filepath, timeline_filepath)
        """
        match_path = self.get_match(match_id, data_dir)
        timeline_path = self.get_match_timeline(match_id, data_dir)
        return match_path, timeline_path

    def get_matches(self, match_ids: list, data_dir: str = "data") -> Dict[str, tuple]:
        """
        Fetch multiple matches with their timelines.

        Args:
            match_ids: List of match IDs to fetch
            data_dir: Directory to save files in

        Returns:
            Dictionary mapping match_id to (match_path, timeline_path) tuple
        """
        results = {}
        for match_id in match_ids:
            match_path, timeline_path = self.get_match_with_timeline(match_id, data_dir)
            results[match_id] = (match_path, timeline_path)
        return results
