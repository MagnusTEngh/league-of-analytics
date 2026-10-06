"""Module for fetching match data from Riot Games API.

Deprecated: Use RequestHandler from data.api.request_handler instead.
"""

from typing import Optional

from data.api.request_handler import RequestHandler


class RiotMatchAPI:
    """Client for fetching match data from Riot Games API.
    
    Deprecated: Use RequestHandler instead.
    """

    def __init__(self, api_key: Optional[str] = None, region: str = "europe"):
        """
        Initialize the Riot Match API client.

        Args:
            api_key: Riot Games API key
            region: Region to fetch data from (e.g., 'europe', 'americas', 'asia')
        """
        self.handler = RequestHandler(api_key=api_key, region=region)
        self.region = region

    def get_match(self, match_id: str) -> Optional[dict]:
        """
        Fetch match data by match ID.

        Args:
            match_id: The match ID to fetch

        Returns:
            Match data dict, or None if not found
        """
        return self.handler.get_match(match_id)

    def get_match_timeline(self, match_id: str) -> Optional[dict]:
        """
        Fetch match timeline by match ID.

        Args:
            match_id: The match ID to fetch timeline for

        Returns:
            Timeline data dict, or None if not found
        """
        return self.handler.get_match_timeline(match_id)


