"""Discord integration service for sending notifications."""
import httpx
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from app.config import settings

logger = logging.getLogger(__name__)


class DiscordService:
    """Service for sending notifications to Discord via webhooks."""
    
    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize Discord service.
        
        Args:
            webhook_url: Discord webhook URL (if None, uses settings)
        """
        self.webhook_url = webhook_url or settings.discord_webhook_url
        self.enabled = bool(self.webhook_url) and settings.discord_enabled
        
        if self.enabled:
            logger.info("Discord service enabled")
        else:
            logger.debug("Discord service disabled (no webhook URL or disabled in settings)")
    
    async def send_notification(
        self,
        title: str,
        description: str,
        color: int = 0x00ff00,  # Green
        fields: Optional[List[Dict[str, Any]]] = None,
        footer: Optional[str] = None,
        thumbnail_url: Optional[str] = None
    ) -> bool:
        """
        Send a notification to Discord via webhook.
        
        Args:
            title: Notification title
            description: Notification description
            color: Embed color (hex integer, e.g., 0x00ff00 for green)
            fields: Optional list of field dictionaries with 'name', 'value', 'inline' keys
            footer: Optional footer text
            thumbnail_url: Optional thumbnail image URL
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        embed = {
            "title": title,
            "description": description,
            "color": color,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        if fields:
            embed["fields"] = fields
        
        if footer:
            embed["footer"] = {"text": footer}
        
        if thumbnail_url:
            embed["thumbnail"] = {"url": thumbnail_url}
        
        payload = {"embeds": [embed]}
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                )
                response.raise_for_status()
                logger.debug(f"Discord notification sent: {title}")
                return True
        except httpx.TimeoutException:
            logger.warning(f"Discord webhook timeout: {title}")
            return False
        except httpx.HTTPStatusError as e:
            logger.warning(f"Discord webhook HTTP error: {e.response.status_code} - {title}")
            return False
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}", exc_info=True)
            return False
    
    async def notify_hole_in_one(
        self,
        player_name: str,
        hole: int,
        round_id: int,
        tournament_name: str
    ) -> bool:
        """Notify about a hole-in-one."""
        return await self.send_notification(
            title="🎯 HOLE-IN-ONE!",
            description=f"**{player_name}** just got a hole-in-one on **hole {hole}**!",
            color=0xff0000,  # Red
            fields=[
                {"name": "Player", "value": player_name, "inline": True},
                {"name": "Hole", "value": str(hole), "inline": True},
                {"name": "Round", "value": f"Round {round_id}", "inline": True},
                {"name": "Tournament", "value": tournament_name, "inline": False},
            ],
            footer="All entries with this player earned 3 bonus points!"
        )
    
    async def notify_double_eagle(
        self,
        player_name: str,
        hole: int,
        round_id: int,
        tournament_name: str
    ) -> bool:
        """Notify about a double eagle (albatross)."""
        return await self.send_notification(
            title="🦅 DOUBLE EAGLE (ALBATROSS)!",
            description=f"**{player_name}** got a double eagle on **hole {hole}**!",
            color=0xff6600,  # Orange
            fields=[
                {"name": "Player", "value": player_name, "inline": True},
                {"name": "Hole", "value": str(hole), "inline": True},
                {"name": "Round", "value": f"Round {round_id}", "inline": True},
                {"name": "Tournament", "value": tournament_name, "inline": False},
            ],
            footer="All entries with this player earned 3 bonus points!"
        )
    
    async def notify_eagle(
        self,
        player_name: str,
        hole: int,
        round_id: int,
        tournament_name: str
    ) -> bool:
        """Notify about an eagle."""
        return await self.send_notification(
            title="🦅 EAGLE!",
            description=f"**{player_name}** got an eagle on **hole {hole}**!",
            color=0xffaa00,  # Gold/Orange
            fields=[
                {"name": "Player", "value": player_name, "inline": True},
                {"name": "Hole", "value": str(hole), "inline": True},
                {"name": "Round", "value": f"Round {round_id}", "inline": True},
                {"name": "Tournament", "value": tournament_name, "inline": False},
            ],
            footer="All entries with this player earned 2 bonus points!"
        )
    
    async def notify_new_leader(
        self,
        entry_name: str,
        total_points: float,
        previous_leader_name: Optional[str] = None,
        round_id: Optional[int] = None,
        tournament_name: Optional[str] = None
    ) -> bool:
        """Notify about a new leader."""
        fields = [
            {"name": "New Leader", "value": entry_name, "inline": True},
            {"name": "Total Points", "value": f"{total_points:.1f}", "inline": True},
        ]
        
        if round_id:
            fields.append({"name": "Round", "value": f"Round {round_id}", "inline": True})
        
        if previous_leader_name:
            fields.append({"name": "Previous Leader", "value": previous_leader_name, "inline": False})
        
        if tournament_name:
            fields.append({"name": "Tournament", "value": tournament_name, "inline": False})
        
        return await self.send_notification(
            title="👑 NEW LEADER!",
            description=f"**{entry_name}** has taken the lead!",
            color=0xffd700,  # Gold
            fields=fields
        )
    
    async def notify_round_complete(
        self,
        round_id: int,
        leader_name: str,
        leader_points: float,
        total_entries: int,
        tournament_name: str
    ) -> bool:
        """Notify about round completion."""
        return await self.send_notification(
            title=f"🏁 Round {round_id} Complete!",
            description=f"Round {round_id} has finished. Scores updated!",
            color=0x0099ff,  # Blue
            fields=[
                {"name": "Current Leader", "value": leader_name, "inline": True},
                {"name": "Leader Points", "value": f"{leader_points:.1f}", "inline": True},
                {"name": "Total Entries", "value": str(total_entries), "inline": True},
                {"name": "Tournament", "value": tournament_name, "inline": False},
            ]
        )
    
    async def notify_tournament_start(
        self,
        tournament_name: str,
        year: int,
        entry_count: int
    ) -> bool:
        """Notify about tournament start."""
        return await self.send_notification(
            title="🏌️ Tournament Started!",
            description=f"**{tournament_name}** is now in progress!",
            color=0x00ff00,  # Green
            fields=[
                {"name": "Tournament", "value": tournament_name, "inline": True},
                {"name": "Year", "value": str(year), "inline": True},
                {"name": "Entries", "value": str(entry_count), "inline": True},
            ]
        )
    
    async def notify_big_position_change(
        self,
        entry_name: str,
        old_position: int,
        new_position: int,
        total_points: float,
        round_id: Optional[int] = None
    ) -> bool:
        """Notify about a significant position change (5+ positions)."""
        position_change = old_position - new_position  # Positive = moved up
        direction = "up" if position_change > 0 else "down"
        
        return await self.send_notification(
            title=f"📈 Big Move {direction.title()}!",
            description=f"**{entry_name}** moved from **#{old_position}** to **#{new_position}**!",
            color=0x00ff00 if position_change > 0 else 0xff6600,  # Green for up, orange for down
            fields=[
                {"name": "Entry", "value": entry_name, "inline": True},
                {"name": "Position Change", "value": f"#{old_position} → #{new_position}", "inline": True},
                {"name": "Total Points", "value": f"{total_points:.1f}", "inline": True},
            ] + ([{"name": "Round", "value": f"Round {round_id}", "inline": True}] if round_id else [])
        )


# Global instance (will be initialized with settings)
_discord_service: Optional[DiscordService] = None


def get_discord_service() -> DiscordService:
    """Get or create Discord service instance."""
    global _discord_service
    if _discord_service is None:
        _discord_service = DiscordService()
    return _discord_service
