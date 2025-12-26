"""
Database initialization script.
Creates all tables and sets up default admin account.
Run this script before starting the application for the first time.
"""
import asyncio
import os
from dotenv import load_dotenv
from passlib.context import CryptContext

from app.database import init_database, async_session_maker
from app.models import Admin

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_default_admin():
    """
    Create default admin user if not exists.
    """
    default_username = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
    default_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin")

    async with async_session_maker() as session:
        # Check if admin already exists
        from sqlalchemy import select
        result = await session.execute(
            select(Admin).where(Admin.username == default_username)
        )
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            print(f"Admin user '{default_username}' already exists.")
            return

        # Create default admin
        hashed_password = pwd_context.hash(default_password)
        admin = Admin(
            username=default_username,
            password_hash=hashed_password,
            avatar=None
        )

        session.add(admin)
        await session.commit()

        print(f"Default admin created successfully!")
        print(f"Username: {default_username}")
        print(f"Password: {default_password}")
        print("Please change the default password after first login.")


async def main():
    """
    Main initialization function.
    """
    print("Initializing database...")

    # Create all tables
    await init_database()
    print("Database tables created successfully.")

    # Create default admin
    await create_default_admin()

    print("\nDatabase initialization completed!")


if __name__ == "__main__":
    asyncio.run(main())
