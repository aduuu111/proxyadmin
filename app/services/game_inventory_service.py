"""
Game Inventory Service
Calculates available IP slots for each game (rule).
Core business logic for game-based IP management.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Dict, Optional
from datetime import datetime, timezone

from app.models import User, Outbound, Rule, UserRule


class GameInventoryService:
    """
    Service for calculating game inventory and IP availability.

    Business Rules:
    - Each IP (outbound) can serve max N users (default 10)
    - Same IP cannot be used by 2 users for the same game (rule)
    - Only active users (enabled and not expired) count toward usage
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_game_inventories(self) -> List[Dict]:
        """
        Calculate inventory for all games.
        Returns list of {rule_id, rule_name, total_ips, available_ips, used_ips}
        """
        # Get all rules (games)
        result = await self.db.execute(select(Rule))
        rules = list(result.scalars().all())

        # Get total outbounds count
        result = await self.db.execute(select(func.count(Outbound.id)))
        total_outbounds = result.scalar() or 0

        inventories = []
        for rule in rules:
            inventory = await self.get_game_inventory(rule.id)
            inventories.append({
                "rule_id": rule.id,
                "rule_name": rule.name,
                "total_ips": total_outbounds,
                "available_ips": inventory["available_ips"],
                "used_ips": inventory["used_ips"]
            })

        return inventories

    async def get_game_inventory(self, rule_id: int) -> Dict:
        """
        Calculate inventory for a specific game (rule).

        Returns:
            {
                "total_ips": int,  # Total number of outbounds
                "used_ips": int,   # Number of IPs used for this game
                "available_ips": int  # Number of IPs available for this game
            }
        """
        # Get total outbounds
        result = await self.db.execute(select(func.count(Outbound.id)))
        total_ips = result.scalar() or 0

        # Get IPs (outbounds) already used for this game by active users
        # Active user = enabled AND not expired
        now = datetime.now(timezone.utc)

        # Find distinct outbound_ids that are used by active users for this rule
        result = await self.db.execute(
            select(func.count(func.distinct(User.outbound_id)))
            .join(UserRule, User.id == UserRule.user_id)
            .where(
                UserRule.rule_id == rule_id,
                User.enable == True,
                User.expire_time > now
            )
        )
        used_ips = result.scalar() or 0

        available_ips = max(0, total_ips - used_ips)

        return {
            "total_ips": total_ips,
            "used_ips": used_ips,
            "available_ips": available_ips
        }

    async def get_available_outbounds_for_game(self, rule_id: int, limit: Optional[int] = None) -> List[Outbound]:
        """
        Get list of outbounds (IPs) that are available for a specific game.

        An outbound is available if:
        1. It has available slots (current_users < max_users)
        2. It's not already used by an active user for this game

        Args:
            rule_id: The game/rule ID
            limit: Maximum number of outbounds to return (None = all)

        Returns:
            List of available Outbound objects
        """
        now = datetime.now(timezone.utc)

        # Get all outbounds
        result = await self.db.execute(select(Outbound))
        all_outbounds = list(result.scalars().all())

        # Get outbounds already used for this game by active users
        result = await self.db.execute(
            select(User.outbound_id)
            .join(UserRule, User.id == UserRule.user_id)
            .where(
                UserRule.rule_id == rule_id,
                User.enable == True,
                User.expire_time > now
            )
            .distinct()
        )
        used_outbound_ids = set(row[0] for row in result.all())

        # Filter available outbounds
        available = []
        for outbound in all_outbounds:
            # Check if this outbound is already used for this game
            if outbound.id in used_outbound_ids:
                continue

            # Check if outbound has available slots
            result = await self.db.execute(
                select(func.count(User.id))
                .where(
                    User.outbound_id == outbound.id,
                    User.enable == True,
                    User.expire_time > now
                )
            )
            current_users = result.scalar() or 0

            if current_users < outbound.max_users:
                available.append(outbound)

                if limit and len(available) >= limit:
                    break

        return available

    async def can_create_users_for_game(self, rule_id: int, count: int) -> tuple[bool, str]:
        """
        Check if we can create N users for a specific game.

        Returns:
            (can_create: bool, message: str)
        """
        inventory = await self.get_game_inventory(rule_id)

        if inventory["available_ips"] < count:
            return False, f"Not enough available IPs. Available: {inventory['available_ips']}, Requested: {count}"

        return True, "OK"

    async def get_outbound_usage(self, outbound_id: int) -> Dict:
        """
        Get usage statistics for a specific outbound.

        Returns:
            {
                "outbound_id": int,
                "max_users": int,
                "active_users": int,
                "available_slots": int,
                "games": [{"rule_id": int, "rule_name": str, "user_count": int}, ...]
            }
        """
        # Get outbound
        outbound = await self.db.get(Outbound, outbound_id)
        if not outbound:
            raise ValueError(f"Outbound {outbound_id} not found")

        now = datetime.now(timezone.utc)

        # Get active users count
        result = await self.db.execute(
            select(func.count(User.id))
            .where(
                User.outbound_id == outbound_id,
                User.enable == True,
                User.expire_time > now
            )
        )
        active_users = result.scalar() or 0

        # Get games breakdown
        result = await self.db.execute(
            select(Rule.id, Rule.name, func.count(User.id).label("user_count"))
            .join(UserRule, Rule.id == UserRule.rule_id)
            .join(User, UserRule.user_id == User.id)
            .where(
                User.outbound_id == outbound_id,
                User.enable == True,
                User.expire_time > now
            )
            .group_by(Rule.id, Rule.name)
        )
        games = [
            {"rule_id": row[0], "rule_name": row[1], "user_count": row[2]}
            for row in result.all()
        ]

        return {
            "outbound_id": outbound_id,
            "max_users": outbound.max_users,
            "active_users": active_users,
            "available_slots": max(0, outbound.max_users - active_users),
            "games": games
        }
