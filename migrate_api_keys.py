"""
Database migration script to add APIKey table.
Run this script to update the database schema.
"""
import asyncio
from sqlalchemy import text
from app.database import engine, Base
from app.models import APIKey  # Import to ensure table is registered


async def migrate():
    """Add APIKey table to database."""
    print("Starting database migration...")

    async with engine.begin() as conn:
        # Create APIKey table
        await conn.run_sync(Base.metadata.create_all)

    print("Migration completed successfully!")
    print("APIKey table has been created.")


if __name__ == "__main__":
    asyncio.run(migrate())
