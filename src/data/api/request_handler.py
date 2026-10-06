"""RequestHandler for Riot Games API interactions.

Handles rate limiting, request execution, error handling, and data storage.
Each endpoint has its own method with a shared request method.
"""

import os
import logging
from typing import Optional, List
from urllib.parse import quote

from requests_ratelimiter import LimiterSession

from data.api.utils import save_compressed_json, file_exists

logger = logging.getLogger(__name__)


class FetchStatus:
    """Status codes for fetch operations."""
    EXISTS = "exists"
    SUCCESS = "success"
    FAILED = "failed"


class RequestHandler:
    """Handler for Riot Games API requests with rate limiting."""

    _session: Optional[LimiterSession] = None

    def __init__(self, api_key: Optional[str] = None, storage_path: str = "data", region: str = "europe"):
        """
        Initialize the RequestHandler.

        Args:
            api_key: Riot Games API key (defaults to RIOT_API_KEY env var)
            storage_path: Base path for storing API responses
            region: Default region for API requests
        """
        self.api_key = api_key or os.environ.get("RIOT_API_KEY")
        if not self.api_key:
            raise ValueError("API key required. Set RIOT_API_KEY env var or pass api_key.")
        self.storage_path = storage_path
        self.region = region
        self.base_url = f"https://{region}.api.riotgames.com"
        self.current_account: Optional[str] = None

        if RequestHandler._session is None:
            RequestHandler._session = LimiterSession(
                rate_limits=["20/1s", "100/2m"]
            )
        self.session = RequestHandler._session
        self.session.headers.update({"X-Riot-Token": self.api_key})

    def _request(self, url: str, params: Optional[dict] = None) -> Optional[dict]:
        """
        Shared request method that handles errors and retries.

        Args:
            url: The API endpoint URL
            params: Optional query parameters

        Returns:
            Parsed JSON response, or None if request failed
        """
        try:
            response = self.session.get(url, params=params)
            if response.status_code == 404:
                logger.debug("404 Not Found: %s", url)
                return None
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 1))
                logger.warning("Rate limited. Retrying after %s seconds: %s", retry_after, url)
                import time
                time.sleep(retry_after)
                return self._request(url, params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("Request failed for %s: %s", url, e)
            return None

    def get_account_by_riot_id(self, game_name: str, tag: str) -> Optional[dict]:
        """
        Get account information by riot ID (game_name#tag).

        Args:
            game_name: Summoner game name
            tag: Summoner tagline

        Returns:
            Account data, or None if not found
        """
        encoded_name = quote(game_name)
        encoded_tag = quote(tag)
        url = f"{self.base_url}/riot/account/v1/accounts/by-riot-id/{encoded_name}/{encoded_tag}"
        return self._request(url)

    def get_matches_by_puuid(self, puuid: str, start: int = 0, count: int = 100) -> List[str]:
        """
        Get list of match IDs for a given PUUID.

        Args:
            puuid: Player UUID
            start: Starting index
            count: Number of matches to retrieve

        Returns:
            List of match IDs
        """
        url = f"{self.base_url}/lol/match/v5/matches/by-puuid/{puuid}/ids"
        params = {"start": start, "count": count}
        result = self._request(url, params)
        return result if result else []

    def get_all_matches_for_account(self, game_name: str, tag: str) -> List[str]:
        """
        Get all match IDs for a given account.

        Args:
            game_name: Summoner game name
            tag: Summoner tagline

        Returns:
            List of all match IDs
        """
        account_data = self.get_account_by_riot_id(game_name, tag)
        if not account_data:
            return []

        puuid = account_data["puuid"]
        all_match_ids: List[str] = []
        start = 0

        while True:
            match_ids = self.get_matches_by_puuid(puuid, start=start, count=100)
            if not match_ids:
                break
            all_match_ids.extend(match_ids)
            if len(match_ids) < 100:
                break
            start += 100

        return all_match_ids

    def get_match(self, match_id: str) -> Optional[dict]:
        """
        Get match data by match ID.

        Args:
            match_id: The match ID to fetch

        Returns:
            Match data dict, or None if not found
        """
        url = f"{self.base_url}/lol/match/v5/matches/{match_id}"
        return self._request(url)

    def get_match_timeline(self, match_id: str) -> Optional[dict]:
        """
        Get match timeline by match ID.

        Args:
            match_id: The match ID to fetch timeline for

        Returns:
            Timeline data dict, or None if not found
        """
        url = f"{self.base_url}/lol/match/v5/matches/{match_id}/timeline"
        return self._request(url)

    def _get_data_dir(self, subdir: str) -> str:
        """Get full path for a data subdirectory."""
        return os.path.join(self.storage_path, subdir)

    def save_match(self, match_id: str, data: dict) -> str:
        """
        Save match data to storage.

        Args:
            match_id: The match ID
            data: Match data to save

        Returns:
            Path to the saved file
        """
        filename = f"{self.region}_{match_id}"
        return save_compressed_json(data, filename, self._get_data_dir("match"))

    def save_timeline(self, match_id: str, data: dict) -> str:
        """
        Save timeline data to storage.

        Args:
            match_id: The match ID
            data: Timeline data to save

        Returns:
            Path to the saved file
        """
        filename = f"{self.region}_{match_id}"
        return save_compressed_json(data, filename, self._get_data_dir("timelines"))

    def save_account(self, puuid: str, data: dict) -> str:
        """
        Save account data to storage.

        Args:
            puuid: Player UUID
            data: Account data to save

        Returns:
            Path to the saved file
        """
        filename = f"{self.region}_{puuid}"
        return save_compressed_json(data, filename, self._get_data_dir("account"))

    def fetch_match(self, match_id: str) -> str:
        """
        Fetch and save match data.

        Args:
            match_id: The match ID to fetch and save

        Returns:
            FetchStatus constant
        """
        filename = f"{self.region}_{match_id}"
        if file_exists(filename, self._get_data_dir("match")):
            logger.debug("Match %s already exists", match_id)
            return FetchStatus.EXISTS

        data = self.get_match(match_id)
        if data is None:
            logger.warning("Failed to fetch match %s", match_id)
            return FetchStatus.FAILED

        self.save_match(match_id, data)
        logger.info("Saved match %s", match_id)
        return FetchStatus.SUCCESS

    def fetch_timeline(self, match_id: str) -> str:
        """
        Fetch and save timeline data.

        Args:
            match_id: The match ID to fetch and save

        Returns:
            FetchStatus constant
        """
        filename = f"{self.region}_{match_id}"
        if file_exists(filename, self._get_data_dir("timelines")):
            logger.debug("Timeline %s already exists", match_id)
            return FetchStatus.EXISTS

        data = self.get_match_timeline(match_id)
        if data is None:
            logger.warning("Failed to fetch timeline %s", match_id)
            return FetchStatus.FAILED

        self.save_timeline(match_id, data)
        logger.info("Saved timeline %s", match_id)
        return FetchStatus.SUCCESS

    def gather_data_for_account(self, summoner_name_tag: str) -> None:
        """
        Gather all missing data for an account.

        Finds all existing data per endpoint, sets self.current_account,
        and runs requests necessary for gathering all missing data.

        Args:
            summoner_name_tag: Summoner name and tag in format "name#tag"
        """
        if "#" not in summoner_name_tag:
            logger.error("Invalid summoner format: %s. Expected format: name#tag", summoner_name_tag)
            return

        game_name, tag = summoner_name_tag.split("#", 1)
        self.current_account = summoner_name_tag
        logger.info("Gathering data for account: %s", self.current_account)

        account_data = self.get_account_by_riot_id(game_name, tag)
        if not account_data:
            logger.error("Failed to get account info for %s", summoner_name_tag)
            return

        puuid = account_data["puuid"]
        region = account_data.get("region", self.region)

        if region != self.region:
            self.region = region
            self.base_url = f"https://{region}.api.riotgames.com"
            self.session.headers.update({"X-Riot-Token": self.api_key})

        account_filename = f"{self.region}_{puuid}"
        if not file_exists(account_filename, self._get_data_dir("account")):
            self.save_account(puuid, account_data)
            logger.info("Saved account data for %s", puuid)

        all_match_ids = self.get_all_matches_for_account(game_name, tag)
        logger.info("Found %d matches for account", len(all_match_ids))

        for match_id in all_match_ids:
            self.fetch_match(match_id)
            self.fetch_timeline(match_id)
