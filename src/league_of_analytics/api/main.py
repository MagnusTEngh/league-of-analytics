"""RequestHandler for Riot Games API interactions.

This module provides the main RequestHandler class that handles rate limiting,
request execution, and data storage for all Riot Games API endpoints.
"""
from functools import wraps
import logging
import os
import json
import zstandard as zstd
from typing import Optional, Dict, Any, List

from requests_ratelimiter import LimiterSession

from dotenv import load_dotenv

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def log_call(level=logging.DEBUG):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.log(
                level,
                "%s called with args=%s, kwargs=%s",
                func.__name__,
                args,
                kwargs,
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator

load_dotenv()

class RequestHandler:
    """
    Main handler for Riot Games API requests.
    
    Handles rate limiting, request execution, error handling, and data storage.
    Each endpoint has its own method, with a shared request method for common functionality.
    """
    storage_path = os.getenv("data_storage_path", None)

    @classmethod
    def set_storage_path(path: str):
        RequestHandler.storage_path = path

    def __init__(self, api_key: str | None = None, region: str = "europe"):
        """
        Initialize the RequestHandler.
        
        Args:
            api_key: Riot Games API key (default: gets token from .env file)
            storage_path: Base path for storing API responses (default: "data")
            region: Default region for API requests (default: "europe")
        """
        if not api_key:
            api_key = os.getenv("RIOT_GAMES_API_KEY", None)
            if not api_key:
                raise ValueError(
                    "Missing RIOT_GAMES_API_KEY environment variable. "
                    "Please add RIOT_GAMES_API_KEY=your_api_key to your .env file or provide it directly to the script."
                )
        self.api_key = api_key
        self.storage_path = RequestHandler.storage_path
        self.region = region
        self.base_url = f"https://{region}.api.riotgames.com"
        self.current_account = None
        
        # Create rate-limited session
        self.session = LimiterSession(
            per_second=20,
            per_minute=50,
        )
        self.session.headers.update({"X-Riot-Token": self.api_key})
    
    @log_call()
    def run_collection(self, accounts: List[str]) -> None:
        """
        Gather data for multiple Riot accounts.

        Args:
            accounts: List of Riot IDs in the format "game_name#tag".
        """
        total = len(accounts)

        for index, account in enumerate(accounts, start=1):
            logger.info(f"\n[{index}/{total}] Collecting data for {account}")

            try:
                self.gather_data_for_account(account)
            except Exception as e:
                logger.info(f"Failed to collect data for {account}: {e}")
                continue

        logger.info(f"\nCollection complete. Processed {total} accounts.")

    @log_call()
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
            logger.info(f"Error making request to {url}: {e}")
            return None

    @log_call()
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

    @log_call()
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

    @log_call()
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

    @log_call()
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

    @log_call()
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

    @log_call()
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

    @log_call()
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

    @log_call()
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

    @log_call()
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

    @log_call()
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
            logger.info(f"Invalid summoner format: {summoner_name_tag}. Expected format: name#tag")
            return
        
        game_name, tag = summoner_name_tag.split("#", 1)
        self.current_account = summoner_name_tag
        
        logger.info(f"Gathering data for account: {self.current_account}")
        
        # Get account info
        account_data = self.get_account_by_riot_id(game_name, tag)
        if account_data is None:
            logger.info(f"Failed to get account info for {summoner_name_tag}")
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
            logger.info(f"Saved account data for {puuid}")
        
        # Get all match IDs
        all_match_ids = self.get_all_matches_for_account(game_name, tag)
        logger.info(f"Found {len(all_match_ids)} matches for account")
        
        # Note: list of match ids is not saved as per architecture.md
        
        # Process each match
        for match_id in all_match_ids:
            # Check if match data already exists
            match_filename = f"{self.region}_{match_id}"
            if not self._file_exists(match_filename, "match_v5"):
                logger.info(f"Fetching match data for {match_id}")
                match_data = self.get_match(match_id)
                if match_data:
                    self.save_match_data(match_id, match_data)
                    logger.info(f"Saved match data for {match_id}")
            
            # Check if timeline data already exists
            timeline_filename = f"{self.region}_{match_id}"
            if not self._file_exists(timeline_filename, "timelines"):
                logger.info(f"Fetching timeline data for {match_id}")
                timeline_data = self.get_match_timeline(match_id)
                if timeline_data:
                    self.save_timeline_data(match_id, timeline_data)
                    logger.info(f"Saved timeline data for {match_id}")

def main() -> None:
    accounts = [
        "otwinterkart#EUW",
    ]

    handler = RequestHandler()
    handler.run_collection(accounts)

if __name__ == "__main__":
    main()