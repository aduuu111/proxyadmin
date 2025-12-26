"""
User management routes.
Handles CRUD operations for proxy users.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime

from app.database import get_db
from app.models import Admin
from app.auth import get_current_admin
from app.schemas import UserCreate, UserUpdate, UserResponse
from app.services.user_service import UserService
from app.core_client import CoreAdapter
import os

router = APIRouter(prefix="/api/users", tags=["Users"])


def get_core_adapter() -> CoreAdapter:
    """Dependency to get Core Adapter instance."""
    return CoreAdapter(
        base_url=os.getenv("CORE_API_URL"),
        api_key=os.getenv("CORE_API_KEY")
    )


@router.get("", response_model=List[UserResponse])
async def get_all_users(
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    core: CoreAdapter = Depends(get_core_adapter)
):
    """Get all proxy users."""
    service = UserService(db, core)
    users = await service.get_all()
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    core: CoreAdapter = Depends(get_core_adapter)
):
    """Get user by ID."""
    service = UserService(db, core)
    user = await service.get_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    core: CoreAdapter = Depends(get_core_adapter)
):
    """Create new proxy user."""
    service = UserService(db, core)

    try:
        user = await service.create(user_data)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    core: CoreAdapter = Depends(get_core_adapter)
):
    """Update existing user."""
    service = UserService(db, core)

    try:
        user = await service.update(user_id, user_data)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    core: CoreAdapter = Depends(get_core_adapter)
):
    """Delete user."""
    service = UserService(db, core)

    try:
        await service.delete(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{user_id}/reset-traffic", response_model=UserResponse)
async def reset_traffic(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    core: CoreAdapter = Depends(get_core_adapter)
):
    """Reset user traffic counters."""
    service = UserService(db, core)

    try:
        user = await service.reset_traffic(user_id)
        return user
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{user_id}/toggle", response_model=UserResponse)
async def toggle_enable(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    core: CoreAdapter = Depends(get_core_adapter)
):
    """Toggle user enable/disable status."""
    service = UserService(db, core)

    try:
        user = await service.toggle_enable(user_id)
        return user
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{user_id}/renew", response_model=UserResponse)
async def renew_user(
    user_id: int,
    new_expire_time: datetime,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    core: CoreAdapter = Depends(get_core_adapter)
):
    """Renew user expiration time."""
    service = UserService(db, core)

    try:
        user = await service.renew_user(user_id, new_expire_time)
        return user
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
