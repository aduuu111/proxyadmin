"""
Outbound Service Layer
Handles outbound proxy configuration business logic.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime

from app.models import Outbound
from app.schemas import OutboundCreate, OutboundUpdate
from app.core_client import CoreAdapter, CoreConnectionError


class OutboundService:
    """
    Business logic for outbound management.
    """

    def __init__(self, db: AsyncSession, core_adapter: CoreAdapter):
        self.db = db
        self.core = core_adapter

    async def get_all(self) -> List[Outbound]:
        """Get all outbounds from database."""
        result = await self.db.execute(select(Outbound))
        return list(result.scalars().all())

    async def get_by_id(self, outbound_id: int) -> Optional[Outbound]:
        """Get outbound by ID."""
        result = await self.db.execute(
            select(Outbound).where(Outbound.id == outbound_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Outbound]:
        """Get outbound by name."""
        result = await self.db.execute(
            select(Outbound).where(Outbound.name == name)
        )
        return result.scalar_one_or_none()

    async def create(self, outbound_data: OutboundCreate) -> Outbound:
        """
        Create new outbound.
        Saves to database and syncs to Core Service.
        """
        # Check if name already exists
        existing = await self.get_by_name(outbound_data.name)
        if existing:
            raise ValueError(f"Outbound with name '{outbound_data.name}' already exists")

        # Create database record
        outbound = Outbound(
            name=outbound_data.name,
            protocol=outbound_data.protocol,
            config=outbound_data.config,
            local_interface_ip=outbound_data.local_interface_ip,
            remark=outbound_data.remark,
            is_auto_generated=outbound_data.is_auto_generated
        )

        self.db.add(outbound)
        await self.db.flush()

        # Sync to Core Service
        try:
            eh = outbound_data.config.get("eh", outbound_data.local_interface_ip)
            proxy_url = outbound_data.config.get("proxyUrl", "")

            await self.core.create_outbound(
                name=outbound_data.name,
                eh=eh,
                proxy_url=proxy_url
            )
        except CoreConnectionError as e:
            # Log error but don't fail - database is source of truth
            print(f"Warning: Failed to sync outbound to Core: {str(e)}")

        await self.db.commit()
        await self.db.refresh(outbound)
        return outbound

    async def update(self, outbound_id: int, outbound_data: OutboundUpdate) -> Outbound:
        """
        Update existing outbound.
        Updates database and syncs to Core Service.
        """
        outbound = await self.get_by_id(outbound_id)
        if not outbound:
            raise ValueError(f"Outbound with ID {outbound_id} not found")

        # Update fields
        if outbound_data.name is not None:
            outbound.name = outbound_data.name
        if outbound_data.protocol is not None:
            outbound.protocol = outbound_data.protocol
        if outbound_data.config is not None:
            outbound.config = outbound_data.config
        if outbound_data.local_interface_ip is not None:
            outbound.local_interface_ip = outbound_data.local_interface_ip
        if outbound_data.remark is not None:
            outbound.remark = outbound_data.remark

        outbound.updated_at = datetime.utcnow()

        # Sync to Core Service
        try:
            eh = outbound.config.get("eh", outbound.local_interface_ip)
            proxy_url = outbound.config.get("proxyUrl", "")

            await self.core.edit_outbound(
                name=outbound.name,
                eh=eh,
                proxy_url=proxy_url
            )
        except CoreConnectionError as e:
            print(f"Warning: Failed to sync outbound update to Core: {str(e)}")

        await self.db.commit()
        await self.db.refresh(outbound)
        return outbound

    async def delete(self, outbound_id: int) -> bool:
        """
        Delete outbound.
        Removes from database and Core Service.
        """
        outbound = await self.get_by_id(outbound_id)
        if not outbound:
            raise ValueError(f"Outbound with ID {outbound_id} not found")

        # Delete from Core Service first
        try:
            await self.core.delete_outbound(outbound.name)
        except CoreConnectionError as e:
            print(f"Warning: Failed to delete outbound from Core: {str(e)}")

        # Delete from database
        await self.db.delete(outbound)
        await self.db.commit()
        return True

    async def scan_local_interfaces(self) -> List[Outbound]:
        """
        One-click scan: Get all local network interfaces and create outbounds.
        This is a key feature - automatically creates direct outbounds for all local IPs.

        Returns:
            List of created outbounds
        """
        created_outbounds = []

        try:
            # Get interfaces from Core Service
            interfaces = await self.core.get_interfaces()

            for interface in interfaces:
                eh_name = interface.get("ehName", "")
                eh_ip = interface.get("eh", "")
                public_ip = interface.get("ip", "")

                if not eh_ip:
                    continue

                # Generate unique name
                outbound_name = f"direct_{eh_name}_{eh_ip.replace('.', '_')}"

                # Check if already exists
                existing = await self.get_by_name(outbound_name)
                if existing:
                    continue

                # Create outbound
                outbound_data = OutboundCreate(
                    name=outbound_name,
                    protocol="direct",
                    config={
                        "eh": eh_ip,
                        "proxyUrl": "",
                        "publicIp": public_ip,
                        "interfaceName": eh_name
                    },
                    local_interface_ip=eh_ip,
                    remark=f"Auto-scanned: {eh_name} ({public_ip})",
                    is_auto_generated=True
                )

                outbound = await self.create(outbound_data)
                created_outbounds.append(outbound)

        except CoreConnectionError as e:
            raise ValueError(f"Failed to scan interfaces: {str(e)}")

        return created_outbounds
