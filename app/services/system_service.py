"""
System Service Layer
Handles system-level operations like stats, backups, etc.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Dict, Any
from datetime import datetime
import os

from app.models import User
from app.core_client import CoreAdapter, CoreConnectionError


class SystemService:
    """
    Business logic for system operations.
    """

    def __init__(self, db: AsyncSession, core_adapter: CoreAdapter):
        self.db = db
        self.core = core_adapter

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        Aggregate dashboard statistics.
        Combines data from Core Service and database.
        """
        stats = {
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "total_memory": 0,
            "used_memory": 0,
            "bandwidth_up": 0,
            "bandwidth_down": 0,
            "online_users": 0,
            "total_users": 0,
            "active_users": 0,
            "expired_users": 0,
            "system_version": "1.0.0",
            "uptime": "Unknown"
        }

        # Get system info from Core Service
        try:
            system_info = await self.core.get_system_current_info("all", "all")
            data = system_info.get("data") or {}

            # Parse system data
            if "cpu" in data:
                stats["cpu_usage"] = data["cpu"].get("usage", 0.0)

            if "memory" in data:
                mem = data["memory"]
                stats["total_memory"] = mem.get("total", 0)
                stats["used_memory"] = mem.get("used", 0)
                if stats["total_memory"] > 0:
                    stats["memory_usage"] = (stats["used_memory"] / stats["total_memory"]) * 100

            if "network" in data:
                net = data["network"]
                stats["bandwidth_up"] = net.get("sent", 0)
                stats["bandwidth_down"] = net.get("received", 0)

            if "uptime" in data:
                # Convert uptime from seconds to readable format
                uptime_seconds = data["uptime"]
                if isinstance(uptime_seconds, (int, float)):
                    days = int(uptime_seconds // 86400)
                    hours = int((uptime_seconds % 86400) // 3600)
                    minutes = int((uptime_seconds % 3600) // 60)
                    if days > 0:
                        stats["uptime"] = f"{days}d {hours}h {minutes}m"
                    elif hours > 0:
                        stats["uptime"] = f"{hours}h {minutes}m"
                    else:
                        stats["uptime"] = f"{minutes}m"
                else:
                    stats["uptime"] = str(uptime_seconds)

        except CoreConnectionError as e:
            print(f"Warning: Failed to get system info from Core: {str(e)}")

        # Get user statistics from database
        result = await self.db.execute(select(func.count(User.id)))
        stats["total_users"] = result.scalar() or 0

        result = await self.db.execute(
            select(func.count(User.id)).where(User.status == "active")
        )
        stats["active_users"] = result.scalar() or 0

        result = await self.db.execute(
            select(func.count(User.id)).where(User.status == "expired")
        )
        stats["expired_users"] = result.scalar() or 0

        # Count online users (users with recent activity)
        # For now, just use active users count
        stats["online_users"] = stats["active_users"]

        return stats

    async def get_database_path(self) -> str:
        """
        Get the path to the SQLite database file.
        """
        db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./proxy_admin.db")

        # Extract file path from database URL
        # Format: sqlite+aiosqlite:///./proxy_admin.db
        if ":///" in db_url:
            db_path = db_url.split("///")[1]
        else:
            db_path = "./proxy_admin.db"

        # Resolve to absolute path
        abs_path = os.path.abspath(db_path)
        return abs_path

    async def sync_traffic_from_core(self) -> int:
        """
        Sync traffic statistics from Core Service to database.
        This should be called periodically to keep traffic stats up to date.

        Returns:
            Number of users updated
        """
        updated_count = 0

        try:
            # Get all users from Core
            core_users = await self.core.get_all_users()

            for core_user in core_users:
                listen_addr = core_user.get("listenAddr", "")
                if not listen_addr:
                    continue

                # Extract port from listen address
                try:
                    port = int(listen_addr.split(":")[-1])
                except (ValueError, IndexError):
                    continue

                # Find user in database
                result = await self.db.execute(
                    select(User).where(User.port == port)
                )
                user = result.scalar_one_or_none()

                if not user:
                    continue

                # Update traffic stats
                user.up_traffic = core_user.get("sendByte", 0)
                user.down_traffic = core_user.get("receiveByte", 0)
                user.last_seen = datetime.now(datetime.now().astimezone().tzinfo)
                updated_count += 1

            await self.db.commit()

        except CoreConnectionError as e:
            print(f"Warning: Failed to sync traffic from Core: {str(e)}")

        return updated_count

    async def check_expired_users(self) -> int:
        """
        Check for expired users and update their status.
        Removes expired users from Core Service.

        Returns:
            Number of users expired
        """
        now = datetime.now(datetime.now().astimezone().tzinfo)
        expired_count = 0

        # Find users that just expired
        result = await self.db.execute(
            select(User).where(
                User.status == "active",
                User.expire_time <= now
            )
        )
        expired_users = list(result.scalars().all())

        for user in expired_users:
            user.status = "expired"
            user.updated_at = now

            # Remove from Core Service
            try:
                await self.core.delete_user(f"0.0.0.0:{user.port}")
            except CoreConnectionError as e:
                print(f"Warning: Failed to remove expired user from Core: {str(e)}")

            expired_count += 1

        if expired_count > 0:
            await self.db.commit()

        return expired_count
