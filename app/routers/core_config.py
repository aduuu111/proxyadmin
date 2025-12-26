"""
Core Service configuration management routes.
Allows runtime configuration of Core Service connection settings.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv, set_key, find_dotenv

from app.auth import get_current_admin
from app.models import Admin
from app.core_client import CoreAdapter

router = APIRouter(prefix="/api/core-config", tags=["Core Configuration"])


class CoreConfigModel(BaseModel):
    """Core Service configuration model."""
    api_url: str
    api_key: str


class CoreConfigResponse(BaseModel):
    """Core Service configuration response."""
    api_url: str
    api_key_masked: str
    is_configured: bool


class ConnectionTestResult(BaseModel):
    """Connection test result."""
    success: bool
    message: str
    api_url: str
    response_time_ms: Optional[float] = None
    interfaces: Optional[list] = None


def mask_api_key(key: str) -> str:
    """Mask API key for security (show first 4 and last 4 chars)."""
    if len(key) <= 8:
        return "*" * len(key)
    return key[:4] + "*" * (len(key) - 8) + key[-4:]


@router.get("/current", response_model=CoreConfigResponse)
async def get_core_config(admin: Admin = Depends(get_current_admin)):
    """
    Get current Core Service configuration.
    """
    load_dotenv(override=True)

    api_url = os.getenv("CORE_API_URL", "")
    api_key = os.getenv("CORE_API_KEY", "")

    is_configured = bool(api_url and api_key and api_key != "your_api_key_here")

    return CoreConfigResponse(
        api_url=api_url,
        api_key_masked=mask_api_key(api_key) if api_key else "",
        is_configured=is_configured
    )


@router.post("/update")
async def update_core_config(
    config: CoreConfigModel,
    admin: Admin = Depends(get_current_admin)
):
    """
    Update Core Service configuration.
    Updates the .env file with new settings.
    """
    try:
        # Find .env file
        env_file = find_dotenv()
        if not env_file:
            env_file = os.path.join(os.getcwd(), ".env")

        # Update .env file
        set_key(env_file, "CORE_API_URL", config.api_url)
        set_key(env_file, "CORE_API_KEY", config.api_key)

        # Reload environment variables
        load_dotenv(override=True)

        return {
            "success": True,
            "message": "Core Service configuration updated successfully",
            "api_url": config.api_url,
            "api_key_masked": mask_api_key(config.api_key)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update configuration: {str(e)}"
        )


@router.post("/test", response_model=ConnectionTestResult)
async def test_core_connection(
    config: Optional[CoreConfigModel] = None,
    admin: Admin = Depends(get_current_admin)
):
    """
    Test connection to Core Service.
    If config is provided, test with those settings.
    Otherwise, test with current settings from .env.
    """
    import time

    # Use provided config or load from .env
    if config:
        api_url = config.api_url
        api_key = config.api_key
    else:
        load_dotenv(override=True)
        api_url = os.getenv("CORE_API_URL", "")
        api_key = os.getenv("CORE_API_KEY", "")

    if not api_url or not api_key:
        return ConnectionTestResult(
            success=False,
            message="Core Service configuration is incomplete",
            api_url=api_url or "Not configured"
        )

    # Test connection
    core = CoreAdapter(base_url=api_url, api_key=api_key)

    try:
        start_time = time.time()

        # Try to get interfaces (simple test endpoint)
        interfaces = await core.get_interfaces()

        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to ms

        await core.close()

        return ConnectionTestResult(
            success=True,
            message=f"Successfully connected to Core Service. Found {len(interfaces)} network interface(s).",
            api_url=api_url,
            response_time_ms=round(response_time, 2),
            interfaces=interfaces
        )

    except Exception as e:
        await core.close()

        error_message = str(e)

        # Provide helpful error messages
        if "Connection refused" in error_message or "Failed to connect" in error_message:
            message = f"Cannot connect to {api_url}. Please check if Core Service is running and the URL is correct."
        elif "401" in error_message or "Unauthorized" in error_message:
            message = "Authentication failed. Please check if the API Key is correct."
        elif "timeout" in error_message.lower():
            message = f"Connection timeout. The server at {api_url} is not responding."
        else:
            message = f"Connection failed: {error_message}"

        return ConnectionTestResult(
            success=False,
            message=message,
            api_url=api_url
        )
