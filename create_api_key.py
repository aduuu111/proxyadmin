"""
直接在数据库中创建API密钥的脚本
运行: python create_api_key.py
"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db, engine
from app.models import APIKey
from app.api_key_auth import generate_api_key, hash_api_key, get_key_prefix


async def create_api_key(
    name: str = "Default API Key",
    can_read: bool = True,
    can_write: bool = True,
    can_delete: bool = False,
    rate_limit_per_minute: int = 60,
    expires_days: int = 365
):
    """创建API密钥并保存到数据库"""

    # 生成API密钥
    api_key = generate_api_key()
    key_hash = hash_api_key(api_key)
    key_prefix = get_key_prefix(api_key)

    # 计算过期时间
    expires_at = datetime.utcnow() + timedelta(days=expires_days)

    # 创建数据库记录
    async with AsyncSession(engine) as db:
        db_key = APIKey(
            name=name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            can_read=can_read,
            can_write=can_write,
            can_delete=can_delete,
            rate_limit_per_minute=rate_limit_per_minute,
            expires_at=expires_at,
            is_active=True
        )

        db.add(db_key)
        await db.commit()
        await db.refresh(db_key)

        return api_key, db_key


async def main():
    print("=" * 60)
    print("API密钥生成工具")
    print("=" * 60)

    # 创建默认API密钥
    api_key, db_key = await create_api_key(
        name="Production API Key with Delete",
        can_read=True,
        can_write=True,
        can_delete=True,
        rate_limit_per_minute=60,
        expires_days=365
    )

    print("\n[OK] API密钥创建成功！")
    print("\n" + "=" * 60)
    print("API密钥信息")
    print("=" * 60)
    print(f"ID: {db_key.id}")
    print(f"名称: {db_key.name}")
    print(f"密钥: {api_key}")
    print(f"密钥前缀: {db_key.key_prefix}")
    print(f"读权限: {db_key.can_read}")
    print(f"写权限: {db_key.can_write}")
    print(f"删除权限: {db_key.can_delete}")
    print(f"速率限制: {db_key.rate_limit_per_minute} 请求/分钟")
    print(f"过期时间: {db_key.expires_at}")
    print(f"创建时间: {db_key.created_at}")
    print("=" * 60)

    print("\n[!] 重要提示:")
    print("1. 请立即保存上面的完整API密钥")
    print("2. 密钥只显示一次，无法再次查看")
    print("3. 在Apifox中使用此密钥进行测试")
    print("\n使用方式:")
    print(f"  curl -H 'auth: {api_key}' http://localhost:8000/api/external/users/1")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
