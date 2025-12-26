"""
Rule Service Layer
Handles traffic routing rules business logic.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime

from app.models import Rule
from app.schemas import RuleCreate, RuleUpdate
from app.core_client import CoreAdapter, CoreConnectionError


class RuleService:
    """
    Business logic for rule management.
    """

    def __init__(self, db: AsyncSession, core_adapter: CoreAdapter):
        self.db = db
        self.core = core_adapter

    async def get_all(self) -> List[Rule]:
        """Get all rules ordered by priority."""
        result = await self.db.execute(
            select(Rule).order_by(Rule.priority.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, rule_id: int) -> Optional[Rule]:
        """Get rule by ID."""
        result = await self.db.execute(
            select(Rule).where(Rule.id == rule_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Rule]:
        """Get rule by name."""
        result = await self.db.execute(
            select(Rule).where(Rule.name == name)
        )
        return result.scalar_one_or_none()

    async def create(self, rule_data: RuleCreate) -> Rule:
        """
        Create new rule.
        Saves to database and syncs to Core Service.
        """
        # Check if name already exists
        existing = await self.get_by_name(rule_data.name)
        if existing:
            raise ValueError(f"Rule with name '{rule_data.name}' already exists")

        # Create database record
        rule = Rule(
            name=rule_data.name,
            content=rule_data.content,
            priority=rule_data.priority,
            remark=rule_data.remark
        )

        self.db.add(rule)
        await self.db.flush()

        # Sync to Core Service
        try:
            await self.core.add_rule(name=rule_data.name, data=rule_data.content)
        except CoreConnectionError as e:
            print(f"Warning: Failed to sync rule to Core: {str(e)}")

        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def update(self, rule_id: int, rule_data: RuleUpdate) -> Rule:
        """
        Update existing rule.
        Updates database and syncs to Core Service.
        """
        rule = await self.get_by_id(rule_id)
        if not rule:
            raise ValueError(f"Rule with ID {rule_id} not found")

        # Update fields
        if rule_data.name is not None:
            rule.name = rule_data.name
        if rule_data.content is not None:
            rule.content = rule_data.content
        if rule_data.priority is not None:
            rule.priority = rule_data.priority
        if rule_data.remark is not None:
            rule.remark = rule_data.remark

        rule.updated_at = datetime.utcnow()

        # Sync to Core Service
        try:
            await self.core.edit_rule(name=rule.name, data=rule.content)
        except CoreConnectionError as e:
            print(f"Warning: Failed to sync rule update to Core: {str(e)}")

        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def delete(self, rule_id: int) -> bool:
        """
        Delete rule.
        Removes from database and Core Service.
        """
        rule = await self.get_by_id(rule_id)
        if not rule:
            raise ValueError(f"Rule with ID {rule_id} not found")

        # Delete from Core Service first
        try:
            await self.core.delete_rule(rule.name)
        except CoreConnectionError as e:
            print(f"Warning: Failed to delete rule from Core: {str(e)}")

        # Delete from database
        await self.db.delete(rule)
        await self.db.commit()
        return True
