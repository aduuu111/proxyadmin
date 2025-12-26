"""
User Service Layer
Handles proxy user business logic with Core Service synchronization.
This is the critical service that manages the lifecycle of proxy users.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime
import logging

from app.models import User, Outbound, Rule, UserRule
from app.schemas import UserCreate, UserUpdate
from app.core_client import CoreAdapter, CoreConnectionError

logger = logging.getLogger(__name__)


class UserService:
    """
    Business logic for user management.
    Implements the core philosophy: SQLite is source of truth, Core is execution engine.
    """

    def __init__(self, db: AsyncSession, core_adapter: CoreAdapter):
        self.db = db
        self.core = core_adapter

    async def get_all(self) -> List[User]:
        """Get all users with relationships."""
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.outbound), selectinload(User.rules))
        )
        return list(result.scalars().all())

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_port(self, port: int) -> Optional[User]:
        """Get user by port."""
        result = await self.db.execute(
            select(User).where(User.port == port)
        )
        return result.scalar_one_or_none()

    def _should_sync_to_core(self, user: User) -> bool:
        """
        Determine if user should be active in Core Service.
        Logic: User must be enabled AND not expired.
        """
        from datetime import timezone
        now = datetime.now(timezone.utc)

        # Ensure both datetimes are timezone-aware for comparison
        expire_time = user.expire_time
        if expire_time.tzinfo is None:
            expire_time = expire_time.replace(tzinfo=timezone.utc)

        is_not_expired = expire_time > now
        return user.enable and is_not_expired

    def _update_user_status(self, user: User) -> None:
        """
        Update user status based on enable flag and expiration.
        Status logic:
        - active: enabled and not expired
        - expired: past expiration time
        - disabled: manually disabled
        """
        from datetime import timezone
        now = datetime.now(timezone.utc)

        # Ensure both datetimes are timezone-aware for comparison
        expire_time = user.expire_time
        if expire_time.tzinfo is None:
            expire_time = expire_time.replace(tzinfo=timezone.utc)

        if not user.enable:
            user.status = "disabled"
        elif expire_time <= now:
            user.status = "expired"
        else:
            user.status = "active"

    async def _build_core_user_data(self, user: User) -> dict:
        """
        Build user data in Core API format.
        Converts our database model to Core Service expected format.
        """
        # Get outbound
        outbound = await self.db.get(Outbound, user.outbound_id)
        if not outbound:
            raise ValueError(f"Outbound with ID {user.outbound_id} not found")

        # Get rules
        result = await self.db.execute(
            select(Rule)
            .join(UserRule)
            .where(UserRule.user_id == user.id)
        )
        rules = list(result.scalars().all())
        rule_names = [rule.name for rule in rules]

        # Build config based on protocol
        conf = user.config or {}
        if user.protocol in ["socks5", "http"]:
            conf = {
                "username": user.username,
                "password": user.password
            }
        elif user.protocol == "ss":
            # For shadowsocks, use 'method' instead of 'username' in conf
            conf = {
                "method": user.username,  # encryption method (e.g., aes-128-gcm)
                "password": user.password
            }

        # Format datetime
        delete_time = user.expire_time.strftime("%Y-%m-%d %H:%M:%S")

        return {
            "enable": user.enable,
            "listenAddr": f"0.0.0.0:{user.port}",
            "protocol": user.protocol,
            "deleteTime": delete_time,
            "maxSendByte": user.total_traffic if user.total_traffic > 0 else 0,
            "maxReceiveByte": user.total_traffic if user.total_traffic > 0 else 0,
            "sendByte": user.up_traffic,
            "receiveByte": user.down_traffic,
            "maxConnCount": user.max_conn_count,
            "sendLimit": user.send_limit,
            "receiveLimit": user.receive_limit,
            "rule": rule_names if rule_names else ["all"],
            "out": outbound.name,
            "conf": conf,
            "info": user.remark or ""
        }

    async def create(self, user_data: UserCreate) -> User:
        """
        Create new user.
        Saves to database and syncs to Core if enabled and not expired.
        """
        print(f"=== CREATING USER: port={user_data.port}, protocol={user_data.protocol} ===")
        logger.info(f"Creating user on port {user_data.port}, protocol: {user_data.protocol}")

        # Check if port already in use
        existing = await self.get_by_port(user_data.port)
        if existing:
            raise ValueError(f"Port {user_data.port} is already in use")

        # Verify outbound exists
        outbound = await self.db.get(Outbound, user_data.outbound_id)
        if not outbound:
            raise ValueError(f"Outbound with ID {user_data.outbound_id} not found")

        print(f"=== USING OUTBOUND: {outbound.name} ===")
        logger.info(f"Using outbound: {outbound.name}")

        # Create user
        user = User(
            username=user_data.username,
            password=user_data.password,
            port=user_data.port,
            protocol=user_data.protocol,
            total_traffic=user_data.total_traffic,
            expire_time=user_data.expire_time,
            enable=user_data.enable,
            send_limit=user_data.send_limit,
            receive_limit=user_data.receive_limit,
            max_conn_count=user_data.max_conn_count,
            outbound_id=user_data.outbound_id,
            config=user_data.config,
            remark=user_data.remark,
            email=user_data.email,
            up_traffic=0,
            down_traffic=0
        )

        # Update status
        self._update_user_status(user)

        self.db.add(user)
        await self.db.flush()

        # Associate rules
        if user_data.rule_ids:
            for rule_id in user_data.rule_ids:
                user_rule = UserRule(user_id=user.id, rule_id=rule_id)
                self.db.add(user_rule)

        await self.db.flush()

        # Sync to Core Service
        should_sync = self._should_sync_to_core(user)
        logger.info(f"User {user.id} should_sync={should_sync}, enable={user.enable}, expire_time={user.expire_time}")

        if should_sync:
            try:
                logger.info(f"Preparing to sync user {user.id} to Core Service...")
                core_data = await self._build_core_user_data(user)
                logger.info(f"Core data built: listenAddr={core_data.get('listenAddr')}, protocol={core_data.get('protocol')}")
                logger.info(f"Core data conf: {core_data.get('conf')}")
                logger.info(f"Full Core data: {core_data}")
                await self.core.create_user(core_data)
                logger.info(f"User {user.id} (port {user.port}) synced to Core successfully")
            except CoreConnectionError as e:
                logger.warning(f"Failed to sync user {user.id} to Core: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error syncing user {user.id} to Core: {str(e)}")
        else:
            logger.info(f"User {user.id} not syncing to Core (disabled or expired)")
            # User is disabled or expired - ensure it's not in Core
            try:
                await self.core.delete_user(f"0.0.0.0:{user.port}")
            except CoreConnectionError:
                pass  # It's okay if user doesn't exist in Core

        await self.db.commit()

        # Reload user with relationships
        result = await self.db.execute(
            select(User)
            .where(User.id == user.id)
            .options(selectinload(User.outbound), selectinload(User.rules))
        )
        return result.scalar_one()

    async def update(self, user_id: int, user_data: UserUpdate) -> User:
        """
        Update existing user.
        Updates database and syncs to Core based on enable/expire status.
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        old_port = user.port

        # Update fields
        if user_data.username is not None:
            user.username = user_data.username
        if user_data.password is not None:
            user.password = user_data.password
        if user_data.port is not None:
            # Check if new port is available
            if user_data.port != old_port:
                existing = await self.get_by_port(user_data.port)
                if existing:
                    raise ValueError(f"Port {user_data.port} is already in use")
            user.port = user_data.port
        if user_data.protocol is not None:
            user.protocol = user_data.protocol
        if user_data.total_traffic is not None:
            user.total_traffic = user_data.total_traffic
        if user_data.expire_time is not None:
            user.expire_time = user_data.expire_time
        if user_data.enable is not None:
            user.enable = user_data.enable
        if user_data.send_limit is not None:
            user.send_limit = user_data.send_limit
        if user_data.receive_limit is not None:
            user.receive_limit = user_data.receive_limit
        if user_data.max_conn_count is not None:
            user.max_conn_count = user_data.max_conn_count
        if user_data.outbound_id is not None:
            user.outbound_id = user_data.outbound_id
        if user_data.config is not None:
            user.config = user_data.config
        if user_data.remark is not None:
            user.remark = user_data.remark
        if user_data.email is not None:
            user.email = user_data.email

        # Update rules if provided
        if user_data.rule_ids is not None:
            # Remove old rules
            await self.db.execute(
                select(UserRule).where(UserRule.user_id == user.id)
            )
            # Add new rules
            for rule_id in user_data.rule_ids:
                user_rule = UserRule(user_id=user.id, rule_id=rule_id)
                self.db.add(user_rule)

        # Update status
        self._update_user_status(user)
        user.updated_at = datetime.now(datetime.now().astimezone().tzinfo)

        await self.db.flush()

        # Sync to Core Service
        should_sync = self._should_sync_to_core(user)

        # If port changed, delete old user from Core
        if user_data.port is not None and user_data.port != old_port:
            try:
                await self.core.delete_user(f"0.0.0.0:{old_port}")
            except CoreConnectionError:
                pass

        if should_sync:
            # User should be active - sync to Core
            try:
                core_data = await self._build_core_user_data(user)
                await self.core.sync_user(core_data)
            except CoreConnectionError as e:
                logger.warning(f"Failed to sync user {user_id} update to Core: {str(e)}")
        else:
            # User should be inactive - remove from Core
            try:
                await self.core.delete_user(f"0.0.0.0:{user.port}")
            except CoreConnectionError:
                pass

        await self.db.commit()

        # Reload user with relationships
        result = await self.db.execute(
            select(User)
            .where(User.id == user.id)
            .options(selectinload(User.outbound), selectinload(User.rules))
        )
        return result.scalar_one()

    async def delete(self, user_id: int) -> bool:
        """
        Delete user.
        Removes from database and Core Service.
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        # Delete from Core Service first
        try:
            await self.core.delete_user(f"0.0.0.0:{user.port}")
        except CoreConnectionError as e:
            logger.warning(f"Failed to delete user {user_id} from Core: {str(e)}")

        # Delete user rules associations using SQL
        await self.db.execute(
            delete(UserRule).where(UserRule.user_id == user_id)
        )

        # Delete from database
        await self.db.delete(user)
        await self.db.commit()
        return True

    async def reset_traffic(self, user_id: int) -> User:
        """
        Reset user traffic counters to zero.
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        user.up_traffic = 0
        user.down_traffic = 0
        user.updated_at = datetime.now(datetime.now().astimezone().tzinfo)

        # Sync to Core if user is active
        if self._should_sync_to_core(user):
            try:
                core_data = await self._build_core_user_data(user)
                await self.core.sync_user(core_data)
            except CoreConnectionError as e:
                logger.warning(f"Failed to sync traffic reset for user {user_id} to Core: {str(e)}")

        await self.db.commit()

        # Reload user with relationships
        result = await self.db.execute(
            select(User)
            .where(User.id == user.id)
            .options(selectinload(User.outbound), selectinload(User.rules))
        )
        return result.scalar_one()

    async def toggle_enable(self, user_id: int) -> User:
        """
        Toggle user enable status.
        This is a convenience method for quickly enabling/disabling users.
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        user.enable = not user.enable
        self._update_user_status(user)
        user.updated_at = datetime.now(datetime.now().astimezone().tzinfo)

        await self.db.flush()

        # Sync to Core
        should_sync = self._should_sync_to_core(user)

        if should_sync:
            try:
                core_data = await self._build_core_user_data(user)
                await self.core.sync_user(core_data)
            except CoreConnectionError as e:
                logger.warning(f"Failed to sync toggle for user {user_id} to Core: {str(e)}")
        else:
            try:
                await self.core.delete_user(f"0.0.0.0:{user.port}")
            except CoreConnectionError:
                pass

        await self.db.commit()

        # Reload user with relationships
        result = await self.db.execute(
            select(User)
            .where(User.id == user.id)
            .options(selectinload(User.outbound), selectinload(User.rules))
        )
        return result.scalar_one()

    async def renew_user(self, user_id: int, new_expire_time: datetime) -> User:
        """
        Renew/extend user expiration time.
        If user was expired and gets renewed, this will reactivate them in Core.
        This is the critical "recovery" feature mentioned in requirements.
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        user.expire_time = new_expire_time
        user.enable = True  # Auto-enable when renewing
        self._update_user_status(user)
        user.updated_at = datetime.now(datetime.now().astimezone().tzinfo)

        await self.db.flush()

        # Sync to Core (should now be active)
        if self._should_sync_to_core(user):
            try:
                core_data = await self._build_core_user_data(user)
                await self.core.sync_user(core_data)
            except CoreConnectionError as e:
                logger.warning(f"Failed to sync renewal for user {user_id} to Core: {str(e)}")

        await self.db.commit()

        # Reload user with relationships
        result = await self.db.execute(
            select(User)
            .where(User.id == user.id)
            .options(selectinload(User.outbound), selectinload(User.rules))
        )
        return result.scalar_one()
