"""
Database migration script for adding game management features.
Adds max_users column to outbounds table and creates system_settings table.
"""
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

# Get database path
db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./proxy_admin.db")
db_path = db_url.split("///")[1] if ":///" in db_url else "./proxy_admin.db"

print(f"Migrating database: {db_path}")

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # 1. Add max_users column to outbounds table if it doesn't exist
    print("Adding max_users column to outbounds table...")
    try:
        cursor.execute("ALTER TABLE outbounds ADD COLUMN max_users INTEGER DEFAULT 10 NOT NULL")
        print("[OK] Added max_users column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("[OK] max_users column already exists")
        else:
            raise

    # 2. Create system_settings table if it doesn't exist
    print("Creating system_settings table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            default_protocol VARCHAR(20) DEFAULT 'socks5' NOT NULL,
            default_expiration_days INTEGER DEFAULT 30 NOT NULL,
            default_max_send_byte BIGINT DEFAULT 0 NOT NULL,
            default_max_receive_byte BIGINT DEFAULT 0 NOT NULL,
            default_send_limit INTEGER DEFAULT 0 NOT NULL,
            default_receive_limit INTEGER DEFAULT 0 NOT NULL,
            default_max_conn_count INTEGER DEFAULT 0 NOT NULL,
            username_pattern VARCHAR(50) DEFAULT 'LLL###' NOT NULL,
            password_pattern VARCHAR(50) DEFAULT 'LLL###' NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        )
    """)
    print("[OK] system_settings table created")

    # 3. Insert default system settings if table is empty
    print("Checking system_settings...")
    cursor.execute("SELECT COUNT(*) FROM system_settings")
    count = cursor.fetchone()[0]

    if count == 0:
        print("Inserting default system settings...")
        cursor.execute("""
            INSERT INTO system_settings (
                default_protocol,
                default_expiration_days,
                default_max_send_byte,
                default_max_receive_byte,
                default_send_limit,
                default_receive_limit,
                default_max_conn_count,
                username_pattern,
                password_pattern
            ) VALUES (
                'socks5',
                30,
                0,
                0,
                0,
                0,
                0,
                'LLL###',
                'LLL###'
            )
        """)
        print("[OK] Default system settings inserted")
    else:
        print(f"[OK] System settings already exist ({count} rows)")

    # Commit all changes
    conn.commit()
    print("\n[SUCCESS] Migration completed successfully!")

except Exception as e:
    conn.rollback()
    print(f"\n[ERROR] Migration failed: {str(e)}")
    raise

finally:
    conn.close()
