"""
API Key authentication for external system integration.
"""
import secrets
import hashlib
from datetime import datetime
from fastapi import Security, HTTPException, status, Depends
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import APIKey
from app.database import get_db

api_key_header = APIKeyHeader(name="auth", auto_error=False)


def generate_api_key() -> str:
    """Generate a secure random API key."""
    return f"pak_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def get_key_prefix(api_key: str) -> str:
    """Get the first 8 characters of the API key for identification."""
    return api_key[:12] if len(api_key) >= 12 else api_key


async def verify_api_key(
    api_key: str = Security(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> APIKey:
    """
    Verify API key and return the APIKey object.
    Raises HTTPException if invalid.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is missing"
        )

    # Hash the provided key
    key_hash = hash_api_key(api_key)

    # Query database
    result = await db.execute(
        select(APIKey).where(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True
        )
    )
    api_key_obj = result.scalar_one_or_none()

    if not api_key_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key"
        )

    # Check expiration
    if api_key_obj.expires_at and api_key_obj.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired"
        )

    # Update last used timestamp
    api_key_obj.last_used_at = datetime.utcnow()
    await db.commit()

    return api_key_obj


def require_permission(permission: str):
    """
    Dependency to check if API key has specific permission.
    Usage: require_permission("write")
    """
    async def check_permission(api_key: APIKey = Security(verify_api_key)):
        if permission == "read" and not api_key.can_read:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="API key does not have read permission"
            )
        elif permission == "write" and not api_key.can_write:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="API key does not have write permission"
            )
        elif permission == "delete" and not api_key.can_delete:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="API key does not have delete permission"
            )
        return api_key
    return check_permission
