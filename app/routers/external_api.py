"""
External API router for third-party integrations.
Uses API key authentication instead of JWT.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from datetime import datetime, timedelta
import os
from app.database import get_db
from app.models import User, Outbound, Rule, UserRule
from app.schemas import (
    UserResponse, UserProvisionRequest, UserRenewalRequest,
    BatchUserCreate, BatchUserUpdateRequest, BatchOperationResult,
    WebhookPayload, SuccessResponse, UserCreate, UserUpdate, BatchDeleteRequest
)
from app.api_key_auth import verify_api_key, require_permission
from app.services.user_service import UserService
from app.core_client import CoreAdapter

router = APIRouter(prefix="/api/external", tags=["External API"])


def get_core_adapter() -> CoreAdapter:
    """Dependency to get Core Adapter instance."""
    return CoreAdapter(
        base_url=os.getenv("CORE_API_URL"),
        api_key=os.getenv("CORE_API_KEY")
    )


@router.post("/users/provision", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def provision_user(
    request: UserProvisionRequest,
    db: AsyncSession = Depends(get_db),
    api_key = Depends(require_permission("write")),
    core: CoreAdapter = Depends(get_core_adapter)
):
    """
    Provision a new user from external system (e.g., after payment).
    Requires API key with write permission.
    """
    # Find outbound by name
    result = await db.execute(select(Outbound).where(Outbound.name == request.outbound_name))
    outbound = result.scalar_one_or_none()
    if not outbound:
        raise HTTPException(status_code=404, detail=f"Outbound '{request.outbound_name}' not found")

    # Find rules by names
    rule_ids = []
    for rule_name in request.rule_names:
        result = await db.execute(select(Rule).where(Rule.name == rule_name))
        rule = result.scalar_one_or_none()
        if not rule:
            raise HTTPException(status_code=404, detail=f"Rule '{rule_name}' not found")
        rule_ids.append(rule.id)

    # Calculate expiration
    expire_time = datetime.utcnow() + timedelta(days=request.expire_days)

    # Convert GB to bytes
    total_traffic = request.total_traffic_gb * 1024 * 1024 * 1024 if request.total_traffic_gb > 0 else 0

    # Create UserCreate schema
    user_data = UserCreate(
        username=request.username,
        password=request.password,
        port=request.port,
        protocol=request.protocol,
        total_traffic=total_traffic,
        expire_time=expire_time,
        outbound_id=outbound.id,
        rule_ids=rule_ids,
        email=request.email,
        remark=request.remark,
        enable=True
    )

    # Use UserService to create user (handles Core sync)
    user_service = UserService(db, core)
    user = await user_service.create(user_data)

    return user


@router.post("/users/port/{port}/renew", response_model=UserResponse)
async def renew_user(
    port: int,
    request: UserRenewalRequest,
    db: AsyncSession = Depends(get_db),
    api_key = Depends(require_permission("write")),
    core: CoreAdapter = Depends(get_core_adapter)
):
    """
    Renew a user's subscription by port number (extend expiration and add traffic).
    Requires API key with write permission.
    """
    result = await db.execute(
        select(User)
        .where(User.port == port)
        .options(selectinload(User.outbound), selectinload(User.rules))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail=f"User with port {port} not found")

    # Calculate new expiration
    if user.expire_time < datetime.utcnow():
        # If expired, start from now
        new_expire_time = datetime.utcnow() + timedelta(days=request.extend_days)
    else:
        # If not expired, extend from current expiration
        new_expire_time = user.expire_time + timedelta(days=request.extend_days)

    # Calculate new traffic
    new_total_traffic = user.total_traffic
    if request.add_traffic_gb > 0:
        add_bytes = request.add_traffic_gb * 1024 * 1024 * 1024
        new_total_traffic += add_bytes

    # Use UserService to update and sync
    user_service = UserService(db, core)
    update_data = UserUpdate(
        expire_time=new_expire_time,
        total_traffic=new_total_traffic,
        enable=True  # Re-enable if disabled
    )
    user = await user_service.update(user.id, update_data)

    return user


@router.post("/users/batch", response_model=BatchOperationResult)
async def batch_create_users(
    request: BatchUserCreate,
    db: AsyncSession = Depends(get_db),
    api_key = Depends(require_permission("write")),
    core: CoreAdapter = Depends(get_core_adapter)
):
    """
    Batch create multiple users.
    Requires API key with write permission.
    """
    results = []
    success_count = 0
    failure_count = 0

    user_service = UserService(db, core)

    for user_data in request.users:
        try:
            user = await user_service.create_user(user_data)
            results.append({
                "success": True,
                "user_id": user.id,
                "username": user.username,
                "port": user.port
            })
            success_count += 1
        except Exception as e:
            results.append({
                "success": False,
                "error": str(e),
                "username": user_data.username
            })
            failure_count += 1

    return BatchOperationResult(
        success_count=success_count,
        failure_count=failure_count,
        results=results
    )


@router.put("/users/batch", response_model=BatchOperationResult)
async def batch_update_users(
    request: BatchUserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    api_key = Depends(require_permission("write")),
    core: CoreAdapter = Depends(get_core_adapter)
):
    """
    Batch update multiple users.
    Requires API key with write permission.
    """
    results = []
    success_count = 0
    failure_count = 0

    user_service = UserService(db, core)

    for update_item in request.updates:
        try:
            user = await user_service.update_user(update_item.user_id, update_item.updates)
            results.append({
                "success": True,
                "user_id": user.id,
                "username": user.username
            })
            success_count += 1
        except Exception as e:
            results.append({
                "success": False,
                "error": str(e),
                "user_id": update_item.user_id
            })
            failure_count += 1

    return BatchOperationResult(
        success_count=success_count,
        failure_count=failure_count,
        results=results
    )


@router.delete("/users/batch", response_model=BatchOperationResult)
async def batch_delete_users(
    request: BatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
    api_key = Depends(require_permission("delete")),
    core: CoreAdapter = Depends(get_core_adapter)
):
    """
    Batch delete multiple users by port numbers.
    Requires API key with delete permission.
    """
    results = []
    success_count = 0
    failure_count = 0

    user_service = UserService(db, core)

    for port in request.ports:
        try:
            result = await db.execute(select(User).where(User.port == port))
            user = result.scalar_one_or_none()

            if not user:
                results.append({
                    "success": False,
                    "port": port,
                    "error": f"User with port {port} not found"
                })
                failure_count += 1
                continue

            await user_service.delete(user.id)
            results.append({
                "success": True,
                "port": port,
                "username": user.username
            })
            success_count += 1
        except Exception as e:
            results.append({
                "success": False,
                "port": port,
                "error": str(e)
            })
            failure_count += 1

    return BatchOperationResult(
        success_count=success_count,
        failure_count=failure_count,
        results=results
    )


@router.get("/users/port/{port}", response_model=UserResponse)
async def get_user_by_port(
    port: int,
    db: AsyncSession = Depends(get_db),
    api_key = Depends(require_permission("read"))
):
    """
    Get user by port number (external API).
    Requires API key with read permission.
    """
    result = await db.execute(
        select(User)
        .where(User.port == port)
        .options(selectinload(User.outbound), selectinload(User.rules))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail=f"User with port {port} not found")

    return user


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_external(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    api_key = Depends(require_permission("read"))
):
    """
    Get user by ID (external API).
    Requires API key with read permission.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.delete("/users/port/{port}", response_model=SuccessResponse)
async def delete_user_by_port(
    port: int,
    db: AsyncSession = Depends(get_db),
    api_key = Depends(require_permission("delete")),
    core: CoreAdapter = Depends(get_core_adapter)
):
    """
    Delete user by port number (external API).
    Requires API key with delete permission.
    """
    result = await db.execute(select(User).where(User.port == port))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail=f"User with port {port} not found")

    user_service = UserService(db, core)
    await user_service.delete(user.id)

    return SuccessResponse(message=f"User on port {port} deleted successfully")


@router.post("/users/port/{port}/toggle", response_model=UserResponse)
async def toggle_user_by_port(
    port: int,
    db: AsyncSession = Depends(get_db),
    api_key = Depends(require_permission("write")),
    core: CoreAdapter = Depends(get_core_adapter)
):
    """
    Toggle user enable/disable status by port number (external API).
    Requires API key with write permission.
    """
    result = await db.execute(select(User).where(User.port == port))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail=f"User with port {port} not found")

    user_service = UserService(db, core)
    user = await user_service.toggle_enable(user.id)

    return user


@router.get("/users/username/{username}", response_model=UserResponse)
async def get_user_by_username(
    username: str,
    db: AsyncSession = Depends(get_db),
    api_key = Depends(require_permission("read"))
):
    """
    Get user by username (external API).
    Requires API key with read permission.
    """
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.post("/webhooks/payment", response_model=SuccessResponse)
async def payment_webhook(
    payload: WebhookPayload,
    db: AsyncSession = Depends(get_db),
    api_key = Depends(require_permission("write"))
):
    """
    Webhook endpoint for payment notifications.
    Requires API key with write permission.

    Expected events:
    - payment.success: Create or renew user
    - payment.refund: Disable user
    """
    if payload.event == "payment.success":
        # Handle successful payment
        # Extract user data from payload.data
        user_data = payload.data.get("user")
        if user_data:
            # Create or renew user based on payload
            pass

    elif payload.event == "payment.refund":
        # Handle refund
        user_id = payload.data.get("user_id")
        if user_id:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                user.enable = False
                user.status = "disabled"
                await db.commit()

    return SuccessResponse(message="Webhook processed successfully")


@router.post("/webhooks/user-event", response_model=SuccessResponse)
async def user_event_webhook(
    payload: WebhookPayload,
    db: AsyncSession = Depends(get_db),
    api_key = Depends(require_permission("write"))
):
    """
    Webhook endpoint for user events from external systems.
    Requires API key with write permission.

    Expected events:
    - user.created: Notification that user was created
    - user.updated: Notification that user was updated
    - user.deleted: Notification that user was deleted
    """
    # Process webhook payload
    # This is a placeholder for custom webhook logic

    return SuccessResponse(message="Webhook processed successfully")
