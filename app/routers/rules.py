"""
Rule management routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import os

from app.database import get_db
from app.models import Admin
from app.auth import get_current_admin
from app.schemas import RuleCreate, RuleUpdate, RuleResponse
from app.services.rule_service import RuleService
from app.core_client import CoreAdapter

router = APIRouter(prefix="/api/rules", tags=["Rules"])


def get_core_adapter() -> CoreAdapter:
    """Dependency to get Core Adapter instance."""
    return CoreAdapter(
        base_url=os.getenv("CORE_API_URL"),
        api_key=os.getenv("CORE_API_KEY")
    )


@router.get("", response_model=List[RuleResponse])
async def get_all_rules(
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    core: CoreAdapter = Depends(get_core_adapter)
):
    """Get all routing rules."""
    service = RuleService(db, core)
    rules = await service.get_all()
    return rules


@router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    core: CoreAdapter = Depends(get_core_adapter)
):
    """Get rule by ID."""
    service = RuleService(db, core)
    rule = await service.get_by_id(rule_id)

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    return rule


@router.post("", response_model=RuleResponse, status_code=201)
async def create_rule(
    rule_data: RuleCreate,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    core: CoreAdapter = Depends(get_core_adapter)
):
    """Create new routing rule."""
    service = RuleService(db, core)

    try:
        rule = await service.create(rule_data)
        return rule
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: int,
    rule_data: RuleUpdate,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    core: CoreAdapter = Depends(get_core_adapter)
):
    """Update existing rule."""
    service = RuleService(db, core)

    try:
        rule = await service.update(rule_id, rule_data)
        return rule
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{rule_id}", status_code=204)
async def delete_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    core: CoreAdapter = Depends(get_core_adapter)
):
    """Delete rule."""
    service = RuleService(db, core)

    try:
        await service.delete(rule_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
