"""Check API keys in database"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import engine
from app.models import APIKey

async def check():
    async with AsyncSession(engine) as db:
        result = await db.execute(select(APIKey))
        keys = result.scalars().all()
        print(f'Total keys: {len(keys)}')
        for k in keys:
            print(f'ID: {k.id}, Name: {k.name}, Prefix: {k.key_prefix}, Active: {k.is_active}, Expires: {k.expires_at}')

asyncio.run(check())
