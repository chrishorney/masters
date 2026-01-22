"""Slash Golf API client."""
import httpx
import logging
from typing import Optional, Dict, Any, List
from app.config import settings

logger = logging.getLogger(__name__)


class SlashGolfAPIClient:
    """Client for interacting with Slash Golf API via RapidAPI."""
    
    def __init__(self):
        self.api_key = settings.slash_golf_api_key
        self.api_host = settings.slash_golf_api_host
        self.base_url = "https://live-golf-data.p.rapidapi.com"
        self.default_org_id = settings.default_org_id
        self.default_tournament_id = settings.default_tournament_id
        self.default_year = settings.default_year
        
        self.headers = {
            "x-rapidapi-host": self.api_host,
            "x-rapidapi-key": self.api_key,
        }
    
    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """
        Make a request to the Slash Golf API.
        
        Args:
            endpoint: API endpoint (e.g., "/leaderboard")
            params: Query parameters
            timeout: Request timeout in seconds
            
        Returns:
            JSON response data
            
        Raises:
            httpx.HTTPError: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                
                # Check rate limits from headers
                remaining = response.headers.get("x-ratelimit-requests-remaining")
                if remaining:
                    logger.debug(f"API requests remaining: {remaining}")
                
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"API request failed for {endpoint}: {e}")
            raise
    
    def get_leaderboard(
        self,
        org_id: Optional[str] = None,
        tourn_id: Optional[str] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get tournament leaderboard.
        
        Args:
            org_id: Organization ID (default: from settings)
            tourn_id: Tournament ID (default: from settings)
            year: Year (default: from settings)
            
        Returns:
            Leaderboard data
        """
        params = {
            "orgId": org_id or self.default_org_id,
            "tournId": tourn_id or self.default_tournament_id,
            "year": str(year or self.default_year),
        }
        
        logger.info(f"Fetching leaderboard for tournament {params['tournId']} ({params['year']})")
        return self._make_request("/leaderboard", params=params)
    
    def get_tournament(
        self,
        org_id: Optional[str] = None,
        tourn_id: Optional[str] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get tournament information.
        
        Args:
            org_id: Organization ID (default: from settings)
            tourn_id: Tournament ID (default: from settings)
            year: Year (default: from settings)
            
        Returns:
            Tournament data
        """
        params = {
            "orgId": org_id or self.default_org_id,
            "tournId": tourn_id or self.default_tournament_id,
            "year": str(year or self.default_year),
        }
        
        logger.info(f"Fetching tournament info for {params['tournId']} ({params['year']})")
        return self._make_request("/tournament", params=params)
    
    def get_scorecard(
        self,
        player_id: str,
        org_id: Optional[str] = None,
        tourn_id: Optional[str] = None,
        year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get player scorecard.
        
        Args:
            player_id: Player ID
            org_id: Organization ID (default: from settings)
            tourn_id: Tournament ID (default: from settings)
            year: Year (default: from settings)
            
        Returns:
            List of scorecard data (one per round)
        """
        params = {
            "orgId": org_id or self.default_org_id,
            "tournId": tourn_id or self.default_tournament_id,
            "year": str(year or self.default_year),
            "playerId": player_id,
        }
        
        logger.debug(f"Fetching scorecard for player {player_id}")
        return self._make_request("/scorecard", params=params)
    
    def get_player(
        self,
        player_id: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get player information.
        
        Args:
            player_id: Player ID (optional)
            first_name: First name (optional)
            last_name: Last name (optional)
            
        Returns:
            List of matching players
        """
        params = {}
        if player_id:
            params["playerId"] = player_id
        if first_name:
            params["firstName"] = first_name
        if last_name:
            params["lastName"] = last_name
        
        if not params:
            raise ValueError("At least one parameter (player_id, first_name, or last_name) is required")
        
        logger.debug(f"Searching for player: {params}")
        return self._make_request("/players", params=params)
    
    def get_schedule(
        self,
        org_id: Optional[str] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get tournament schedule.
        
        Args:
            org_id: Organization ID (default: from settings)
            year: Year (default: from settings)
            
        Returns:
            Schedule data
        """
        params = {
            "orgId": org_id or self.default_org_id,
            "year": str(year or self.default_year),
        }
        
        logger.info(f"Fetching schedule for year {params['year']}")
        return self._make_request("/schedule", params=params)
    
    def find_tournament_by_name(
        self,
        tournament_name: str,
        year: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find tournament by name in schedule.
        
        Args:
            tournament_name: Tournament name to search for
            year: Year (default: from settings)
            
        Returns:
            Tournament info if found, None otherwise
        """
        schedule = self.get_schedule(year=year)
        
        for tournament in schedule.get("schedule", []):
            if tournament_name.lower() in tournament.get("name", "").lower():
                return tournament
        
        return None
