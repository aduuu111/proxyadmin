"""
Game Inventory API Routes
Provides endpoints for checking IP availability for each game.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.auth import get_current_admin
from app.models import Admin
from app.services.game_inventory_service import GameInventoryService
from app.schemas import GameInventoryResponse, GameInventory

router = APIRouter(
    prefix="/api/game-inventory",
    tags=["game-inventory"]
)


@router.get("/", response_model=GameInventoryResponse)
async def get_all_inventories(
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    Get inventory for all games.
    Shows available IPs for each game/rule.
    """
    service = GameInventoryService(db)
    inventories = await service.get_all_game_inventories()

    # Get total outbounds from first inventory or query
    from sqlalchemy import select, func
    from app.models import Outbound
    result = await db.execute(select(func.count(Outbound.id)))
    total_outbounds = result.scalar() or 0

    return {
        "games": inventories,
        "total_outbounds": total_outbounds
    }


@router.get("/{rule_id}", response_model=GameInventory)
async def get_game_inventory(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    Get inventory for a specific game/rule.
    """
    from app.models import Rule
    # Verify rule exists
    rule = await db.get(Rule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")

    service = GameInventoryService(db)
    inventory = await service.get_game_inventory(rule_id)

    return {
        "rule_id": rule_id,
        "rule_name": rule.name,
        "total_ips": inventory["total_ips"],
        "available_ips": inventory["available_ips"],
        "used_ips": inventory["used_ips"]
    }


@router.get("/outbound/{outbound_id}/usage")
async def get_outbound_usage(
    outbound_id: int,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    Get detailed usage information for a specific outbound/IP.
    Shows which games are using this IP and how many users.
    """
    service = GameInventoryService(db)
    try:
        usage = await service.get_outbound_usage(outbound_id)
        return usage
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
