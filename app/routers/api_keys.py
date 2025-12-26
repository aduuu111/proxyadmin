"""
API Key management router.
Allows admins to create and manage API keys for external integrations.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.models import APIKey
from app.schemas import APIKeyCreate, APIKeyResponse, APIKeyWithSecret
from app.auth import get_current_admin
from app.api_key_auth import generate_api_key, hash_api_key, get_key_prefix

router = APIRouter(prefix="/api/api-keys", tags=["API Keys"])


@router.post("/", response_model=APIKeyWithSecret, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Create a new API key for external system integration.
    Returns the full API key - save it securely as it won't be shown again.
    """
    # Generate API key
    api_key = generate_api_key()
    key_hash = hash_api_key(api_key)
    key_prefix = get_key_prefix(api_key)

    # Create database record
    db_key = APIKey(
        name=key_data.name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        can_read=key_data.can_read,
        can_write=key_data.can_write,
        can_delete=key_data.can_delete,
        rate_limit_per_minute=key_data.rate_limit_per_minute,
        expires_at=key_data.expires_at,
        is_active=True
    )

    db.add(db_key)
    await db.commit()
    await db.refresh(db_key)

    # Return response with full API key
    response = APIKeyWithSecret.model_validate(db_key)
    response.api_key = api_key
    return response


@router.get("/", response_model=List[APIKeyResponse])
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    List all API keys.
    """
    result = await db.execute(select(APIKey).order_by(APIKey.created_at.desc()))
    keys = result.scalars().all()
    return keys


@router.get("/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Get API key by ID.
    """
    result = await db.execute(select(APIKey).where(APIKey.id == key_id))
    key = result.scalar_one_or_none()

    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    return key


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Delete an API key.
    """
    result = await db.execute(select(APIKey).where(APIKey.id == key_id))
    key = result.scalar_one_or_none()

    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    await db.delete(key)
    await db.commit()


@router.post("/{key_id}/toggle", response_model=APIKeyResponse)
async def toggle_api_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Toggle API key active status.
    """
    result = await db.execute(select(APIKey).where(APIKey.id == key_id))
    key = result.scalar_one_or_none()

    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    key.is_active = not key.is_active
    await db.commit()
    await db.refresh(key)

    return key
