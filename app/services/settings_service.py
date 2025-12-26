"""
System Settings Service
Manages system-wide default settings for user creation.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime
import random
import string

from app.models import SystemSettings
from app.schemas import SystemSettingsUpdate


class SettingsService:
    """
    Service for managing system settings.
    This is a singleton pattern - only one settings record exists.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_settings(self) -> SystemSettings:
        """
        Get system settings. Creates default if not exists.
        """
        result = await self.db.execute(select(SystemSettings))
        settings = result.scalar_one_or_none()

        if not settings:
            # Create default settings
            settings = SystemSettings(
                default_protocol="socks5",
                default_expiration_days=30,
                default_max_send_byte=0,
                default_max_receive_byte=0,
                default_send_limit=0,
                default_receive_limit=0,
                default_max_conn_count=0,
                username_pattern="LLL###",
                password_pattern="LLL###"
            )
            self.db.add(settings)
            await self.db.commit()
            await self.db.refresh(settings)

        return settings

    async def update_settings(self, settings_data: SystemSettingsUpdate) -> SystemSettings:
        """
        Update system settings.
        """
        settings = await self.get_settings()

        # Update fields
        settings.default_protocol = settings_data.default_protocol
        settings.default_expiration_days = settings_data.default_expiration_days
        settings.default_max_send_byte = settings_data.default_max_send_byte
        settings.default_max_receive_byte = settings_data.default_max_receive_byte
        settings.default_send_limit = settings_data.default_send_limit
        settings.default_receive_limit = settings_data.default_receive_limit
        settings.default_max_conn_count = settings_data.default_max_conn_count
        settings.username_pattern = settings_data.username_pattern
        settings.password_pattern = settings_data.password_pattern

        settings.updated_at = datetime.now(datetime.now().astimezone().tzinfo)

        await self.db.commit()
        await self.db.refresh(settings)
        return settings

    def generate_credential(self, pattern: str) -> str:
        """
        Generate username or password based on pattern.

        Pattern format:
        - L or l = random lowercase letter
        - U = random uppercase letter
        - # = random digit
        - Any other character = literal

        Examples:
        - "LLL###" -> "abc123"
        - "UUU###" -> "ABC123"
        - "LlL###" -> "aBc123"
        """
        result = []
        for char in pattern:
            if char == 'L' or char == 'l':
                result.append(random.choice(string.ascii_lowercase))
            elif char == 'U':
                result.append(random.choice(string.ascii_uppercase))
            elif char == '#':
                result.append(random.choice(string.digits))
            else:
                result.append(char)

        return ''.join(result)

    async def generate_username(self, protocol: str = "socks5") -> str:
        """
        Generate username based on protocol type.
        For shadowsocks (ss), returns an encryption method.
        For socks5/http, generates username based on system settings pattern.
        """
        if protocol == "ss":
            # Return random shadowsocks encryption method
            encryption_methods = ["aes-128-gcm", "aes-256-gcm", "chacha20-ietf-poly1305"]
            return random.choice(encryption_methods)
        else:
            # Generate username based on pattern for socks5/http
            settings = await self.get_settings()
            return self.generate_credential(settings.username_pattern)

    async def generate_password(self) -> str:
        """Generate password based on system settings pattern."""
        settings = await self.get_settings()
        return self.generate_credential(settings.password_pattern)
