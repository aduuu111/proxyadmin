"""
System Settings API Routes
Manages system-wide default settings.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import get_current_admin
from app.models import Admin
from app.services.settings_service import SettingsService
from app.schemas import SystemSettingsResponse, SystemSettingsUpdate

router = APIRouter(
    prefix="/api/settings",
    tags=["settings"]
)


@router.get("/", response_model=SystemSettingsResponse)
async def get_system_settings(
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    Get current system settings.
    """
    service = SettingsService(db)
    settings = await service.get_settings()
    return settings


@router.put("/", response_model=SystemSettingsResponse)
async def update_system_settings(
    settings_data: SystemSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    Update system settings.
    """
    service = SettingsService(db)
    settings = await service.update_settings(settings_data)
    return settings


@router.post("/generate-credentials")
async def generate_test_credentials(
    protocol: str = "socks5",  # Add protocol parameter
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    Test endpoint to generate username/password based on current patterns.
    For shadowsocks (ss), returns an encryption method as username.
    For socks5/http, generates username based on pattern.

    Query parameter:
    - protocol: "socks5", "http", or "ss" (default: "socks5")
    """
    service = SettingsService(db)
    username = await service.generate_username(protocol)
    password = await service.generate_password()

    return {
        "username": username,
        "password": password
    }
