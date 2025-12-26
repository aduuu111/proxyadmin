"""
System management routes.
Handles dashboard stats, database backup, and admin settings.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
import os

from app.database import get_db
from app.models import Admin
from app.auth import get_current_admin, get_password_hash
from app.schemas import DashboardStats, AdminUpdate, AdminResponse, SuccessResponse
from app.services.system_service import SystemService
from app.core_client import CoreAdapter

router = APIRouter(prefix="/api/system", tags=["System"])


def get_core_adapter() -> CoreAdapter:
    """Dependency to get Core Adapter instance."""
    return CoreAdapter(
        base_url=os.getenv("CORE_API_URL"),
        api_key=os.getenv("CORE_API_KEY")
    )


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    core: CoreAdapter = Depends(get_core_adapter)
):
    """
    Get dashboard statistics.
    Returns CPU, memory, bandwidth, user counts, and system info.
    """
    service = SystemService(db, core)
    stats = await service.get_dashboard_stats()
    return stats


@router.get("/backup")
async def backup_database(
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    core: CoreAdapter = Depends(get_core_adapter)
):
    """
    Download database backup.
    Returns the SQLite database file for download.
    """
    service = SystemService(db, core)
    db_path = await service.get_database_path()

    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="Database file not found")

    # Generate filename with timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"proxy_admin_backup_{timestamp}.db"

    return FileResponse(
        path=db_path,
        filename=filename,
        media_type="application/octet-stream"
    )


@router.post("/sync-traffic", response_model=SuccessResponse)
async def sync_traffic(
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    core: CoreAdapter = Depends(get_core_adapter)
):
    """
    Manually trigger traffic sync from Core Service.
    Updates traffic statistics for all users.
    """
    service = SystemService(db, core)
    count = await service.sync_traffic_from_core()

    return SuccessResponse(
        message=f"Successfully synced traffic for {count} users",
        data={"count": count}
    )


@router.post("/check-expired", response_model=SuccessResponse)
async def check_expired_users(
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    core: CoreAdapter = Depends(get_core_adapter)
):
    """
    Manually check and disable expired users.
    """
    service = SystemService(db, core)
    count = await service.check_expired_users()

    return SuccessResponse(
        message=f"Processed {count} expired users",
        data={"count": count}
    )


@router.get("/admin/profile", response_model=AdminResponse)
async def get_admin_profile(
    admin: Admin = Depends(get_current_admin)
):
    """Get current admin profile."""
    return admin


@router.put("/admin/profile", response_model=AdminResponse)
async def update_admin_profile(
    admin_data: AdminUpdate,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    Update admin profile (username, password, avatar).
    """
    # Update fields
    if admin_data.username is not None:
        admin.username = admin_data.username

    if admin_data.password is not None:
        admin.password_hash = get_password_hash(admin_data.password)

    if admin_data.avatar is not None:
        admin.avatar = admin_data.avatar

    await db.commit()
    await db.refresh(admin)

    return admin
