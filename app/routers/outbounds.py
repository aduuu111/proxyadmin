"""
Outbound management routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import os

from app.database import get_db
from app.models import Admin
from app.auth import get_current_admin
from app.schemas import OutboundCreate, OutboundUpdate, OutboundResponse, SuccessResponse
from app.services.outbound_service import OutboundService
from app.core_client import CoreAdapter

router = APIRouter(prefix="/api/outbounds", tags=["Outbounds"])


def get_core_adapter() -> CoreAdapter:
    """Dependency to get Core Adapter instance."""
    return CoreAdapter(
        base_url=os.getenv("CORE_API_URL"),
        api_key=os.getenv("CORE_API_KEY")
    )


@router.get("", response_model=List[OutboundResponse])
async def get_all_outbounds(
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    core: CoreAdapter = Depends(get_core_adapter)
):
    """Get all outbound configurations."""
    service = OutboundService(db, core)
    outbounds = await service.get_all()
    return outbounds


@router.get("/{outbound_id}", response_model=OutboundResponse)
async def get_outbound(
    outbound_id: int,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    core: CoreAdapter = Depends(get_core_adapter)
):
    """Get outbound by ID."""
    service = OutboundService(db, core)
    outbound = await service.get_by_id(outbound_id)

    if not outbound:
        raise HTTPException(status_code=404, detail="Outbound not found")

    return outbound


@router.post("", response_model=OutboundResponse, status_code=201)
async def create_outbound(
    outbound_data: OutboundCreate,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    core: CoreAdapter = Depends(get_core_adapter)
):
    """Create new outbound configuration."""
    service = OutboundService(db, core)

    try:
        outbound = await service.create(outbound_data)
        return outbound
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{outbound_id}", response_model=OutboundResponse)
async def update_outbound(
    outbound_id: int,
    outbound_data: OutboundUpdate,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    core: CoreAdapter = Depends(get_core_adapter)
):
    """Update existing outbound configuration."""
    service = OutboundService(db, core)

    try:
        outbound = await service.update(outbound_id, outbound_data)
        return outbound
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{outbound_id}", status_code=204)
async def delete_outbound(
    outbound_id: int,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    core: CoreAdapter = Depends(get_core_adapter)
):
    """Delete outbound configuration."""
    service = OutboundService(db, core)

    try:
        await service.delete(outbound_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/scan", response_model=SuccessResponse)
async def scan_local_interfaces(
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    core: CoreAdapter = Depends(get_core_adapter)
):
    """
    One-click scan: Automatically create outbounds for all local network interfaces.
    This is a key feature for quickly setting up direct outbounds.
    """
    service = OutboundService(db, core)

    try:
        outbounds = await service.scan_local_interfaces()
        return SuccessResponse(
            message=f"Successfully scanned and created {len(outbounds)} outbounds",
            data={"count": len(outbounds)}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
