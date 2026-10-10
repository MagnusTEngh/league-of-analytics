"""RequestHandler for Riot Games API interactions.

This module provides the main RequestHandler class that handles rate limiting,
request execution, and data storage for all Riot Games API endpoints.
"""

import os
import json
import zstandard as zstd
from typing import Optional, Dict, Any, List

from requests_ratelimiter import LimiterSession


class RequestHandler:
    """
    Main handler for Riot Games API requests.
    
    Handles rate limiting, request execution, error handling, and data storage.
    Each endpoint has its own method, with a shared request method for common functionality.
    """
    
    def __init__(self, api_key: str, storage_path: str = "data", region: str = "europe"):
        """
        Initialize the RequestHandler.
        
        Args:
            api_key: Riot Games API key
            storage_path: Base path for storing API responses (default: "data")
            region: Default region for API requests (default: "europe")
        """
        self.api_key = api_key
        self.storage_path = storage_path
        self.region = region
        self.base_url = f"https://{region}.api.riotgames.com"
        self.current_account = None
        
        # Create rate-limited session
        self.session = LimiterSession(
            rate_limits=[
                "20/1s",
                "100/2m"
            ]
        )
        self.session.headers.update({"X-Riot-Token": self.api_key})
    
    def _make_request(self, url: str, params: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        Shared request method that handles errors and rate limiting.
        
        Args:
            url: The API endpoint URL
            params: Optional query parameters
            
        Returns:
            Parsed JSON response, or None if request failed
        """
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error making request to {url}: {e}")
            return None
    
    def _save_data(self, data: Dict[str, Any], filename: str, subdir: str) -> str:
        """
        Save data as compressed JSON file.
        
        Args:
            data: Data to save
            filename: Name of the file (without extension)
            subdir: Subdirectory under storage_path
            
        Returns:
            Path to the saved file
        """
        dir_path = os.path.join(self.storage_path, subdir)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        
        filepath = os.path.join(dir_path, f"{filename}.json.zst")
        
        # Serialize to JSON
        json_data = json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        
        # Compress with zstd
        cctx = zstd.ZstdCompressor(level=3)
        compressed_data = cctx.compress(json_data)
        
        # Save to file
        with open(filepath, 'wb') as f:
            f.write(compressed_data)
        
        return filepath
    
    def _file_exists(self, filename: str, subdir: str) -> bool:
        """
        Check if a .json.zst file exists in the given subdirectory.
        
        Args:
            filename: Name of the file (without extension)
            subdir: Subdirectory under storage_path
            
        Returns:
            True if the file exists, False otherwise
        """
        filepath = os.path.join(self.storage_path, subdir, f"{filename}.json.zst")
        return os.path.exists(filepath)
    
    def get_account_by_riot_id(self, game_name: str, tag: str) -> Optional[Dict[str, Any]]:
        """
        Get account information by riot ID (game_name#tag).
        
        Args:
            game_name: Summoner game name
            tag: Summoner tagline
            
        Returns:
            Account data, or None if request failed
        """
        url = f"{self.base_url}/riot/account/v1/accounts/by-riot-id/{game_name}/{tag}"
        return self._make_request(url)
    
    def get_matches_by_puuid(self, puuid: str, start: int = 0, count: int = 100) -> Optional[List[str]]:
        """
        Get list of match IDs for a given PUUID.
        
        Args:
            puuid: Player UUID
            start: Starting index (default: 0)
            count: Number of matches to retrieve (default: 100, max: 100)
            
        Returns:
            List of match IDs, or None if request failed
        """
        url = f"{self.base_url}/lol/match/v5/matches/by-puuid/{puuid}/ids"
        params = {"start": start, "count": count}
        return self._make_request(url, params)
    
    def get_match(self, match_id: str) -> Optional[Dict[str, Any]]:
        """
        Get match data by match ID.
        
        Args:
            match_id: The match ID to fetch
            
        Returns:
            Match data, or None if request failed
        """
        url = f"{self.base_url}/lol/match/v5/matches/{match_id}"
        return self._make_request(url)
    
    def get_match_timeline(self, match_id: str) -> Optional[Dict[str, Any]]:
        """
        Get match timeline by match ID.
        
        Args:
            match_id: The match ID to fetch timeline for
            
        Returns:
            Timeline data, or None if request failed
        """
        url = f"{self.base_url}/lol/match/v5/matches/{match_id}/timeline"
        return self._make_request(url)
    
    def get_all_matches_for_account(self, game_name: str, tag: str) -> List[str]:
        """
        Get all match IDs for a given account.
        
        Args:
            game_name: Summoner game name
            tag: Summoner tagline
            
        Returns:
            List of all match IDs for the account
        """
        account_data = self.get_account_by_riot_id(game_name, tag)
        if account_data is None:
            return []
        
        puuid = account_data["puuid"]
        all_match_ids = []
        start = 0
        
        while True:
            match_ids = self.get_matches_by_puuid(puuid, start=start, count=100)
            if match_ids is None or len(match_ids) == 0:
                break
            all_match_ids.extend(match_ids)
            if len(match_ids) < 100:
                break
            start += 100
        
        return all_match_ids
    
    def save_match_data(self, match_id: str, data: Dict[str, Any]) -> str:
        """
        Save match data to storage.
        
        Args:
            match_id: The match ID
            data: Match data to save
            
        Returns:
            Path to the saved file
        """
        filename = f"{self.region}_{match_id}"
        return self._save_data(data, filename, "match_v5")
    
    def save_timeline_data(self, match_id: str, data: Dict[str, Any]) -> str:
        """
        Save timeline data to storage.
        
        Args:
            match_id: The match ID
            data: Timeline data to save
            
        Returns:
            Path to the saved file
        """
        filename = f"{self.region}_{match_id}"
        return self._save_data(data, filename, "timelines")
    
    def gather_data_for_account(self, summoner_name_tag: str) -> None:
        """
        Main method to gather all missing data for an account.
        
        Finds all existing data per endpoint, sets self.current_account,
        and runs requests necessary for gathering all missing data.
        
        Args:
            summoner_name_tag: Summoner name and tag in format "name#tag"
        """
        # Parse summoner name and tag
        if "#" not in summoner_name_tag:
            print(f"Invalid summoner format: {summoner_name_tag}. Expected format: name#tag")
            return
        
        game_name, tag = summoner_name_tag.split("#", 1)
        self.current_account = summoner_name_tag
        
        print(f"Gathering data for account: {self.current_account}")
        
        # Get account info
        account_data = self.get_account_by_riot_id(game_name, tag)
        if account_data is None:
            print(f"Failed to get account info for {summoner_name_tag}")
            return
        
        puuid = account_data["puuid"]
        region = account_data.get("region", self.region)
        
        # Update region if different from default
        if region != self.region:
            self.region = region
            self.base_url = f"https://{region}.api.riotgames.com"
            self.session.headers.update({"X-Riot-Token": self.api_key})
        
        # Save account data
        account_filename = f"{self.region}_{puuid}"
        if not self._file_exists(account_filename, "account"):
            self._save_data(account_data, account_filename, "account")
            print(f"Saved account data for {puuid}")
        
        # Get all match IDs
        all_match_ids = self.get_all_matches_for_account(game_name, tag)
        print(f"Found {len(all_match_ids)} matches for account")
        
        # Note: list of match ids is not saved as per architecture.md
        
        # Process each match
        for match_id in all_match_ids:
            # Check if match data already exists
            match_filename = f"{self.region}_{match_id}"
            if not self._file_exists(match_filename, "match_v5"):
                print(f"Fetching match data for {match_id}")
                match_data = self.get_match(match_id)
                if match_data:
                    self.save_match_data(match_id, match_data)
                    print(f"Saved match data for {match_id}")
            
            # Check if timeline data already exists
            timeline_filename = f"{self.region}_{match_id}"
            if not self._file_exists(timeline_filename, "timelines"):
                print(f"Fetching timeline data for {match_id}")
                timeline_data = self.get_match_timeline(match_id)
                if timeline_data:
                    self.save_timeline_data(match_id, timeline_data)
                    print(f"Saved timeline data for {match_id}")
