"""
SQLAlchemy models for the proxy management system.
All models include created_at and updated_at timestamps.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Admin(Base):
    """
    Administrator table for panel access control.
    """
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    avatar = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Outbound(Base):
    """
    Outbound proxy configuration table.
    Supports both local network interfaces and external proxy chains.
    Represents a machine IP that can serve multiple games.
    """
    __tablename__ = "outbounds"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)  # Unique outbound name
    protocol = Column(String(20), nullable=False, default="direct")  # direct/socks5/http/ss

    # Core configuration stored as JSON
    # For direct: {"eh": "192.168.1.1"}
    # For proxy: {"eh": "192.168.1.1", "proxyUrl": "socks5://user:pass@ip:port"}
    config = Column(JSON, nullable=False)

    local_interface_ip = Column(String(50), nullable=True)  # The 'eh' field - local interface IP
    remark = Column(Text, nullable=True)  # UI field for notes
    is_auto_generated = Column(Boolean, default=False)  # Flag for auto-scanned local IPs

    # Game management
    max_users = Column(Integer, default=10, nullable=False)  # Max concurrent users per IP (default 10)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship
    users = relationship("User", back_populates="outbound")


class Rule(Base):
    """
    Traffic routing rules table.
    Rules define which domains/IPs are allowed or blocked.
    """
    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)  # Unique rule name
    content = Column(Text, nullable=False)  # The 'data' field in API - rule content
    priority = Column(Integer, default=0)  # UI field for sorting
    remark = Column(Text, nullable=True)  # UI field for notes

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship
    users = relationship("User", secondary="user_rules", back_populates="rules")


class User(Base):
    """
    Proxy user/account table.
    This is the core table that defines proxy service accounts.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False)  # For socks5/http auth
    password = Column(String(255), nullable=False)  # For authentication
    port = Column(Integer, unique=True, nullable=False, index=True)  # Listen port (from listenAddr)
    protocol = Column(String(20), nullable=False, default="socks5")  # socks5/ss

    # Traffic limits (in bytes)
    total_traffic = Column(BigInteger, default=0)  # 0 = unlimited
    up_traffic = Column(BigInteger, default=0)  # Used upload traffic
    down_traffic = Column(BigInteger, default=0)  # Used download traffic

    # Time management
    expire_time = Column(DateTime(timezone=True), nullable=False)
    last_seen = Column(DateTime(timezone=True), nullable=True)  # Last activity time

    # State management
    enable = Column(Boolean, default=True, nullable=False)
    status = Column(String(20), default="active")  # active/expired/disabled

    # Bandwidth limits (kb/s, 0 = unlimited)
    send_limit = Column(Integer, default=0)  # Upload bandwidth limit
    receive_limit = Column(Integer, default=0)  # Download bandwidth limit
    max_conn_count = Column(Integer, default=0)  # Max concurrent connections, 0 = unlimited

    # Foreign keys
    outbound_id = Column(Integer, ForeignKey("outbounds.id"), nullable=False)

    # Additional configuration stored as JSON
    # For socks5/http: {"username": "user", "password": "pass"}
    # For ss: {"method": "aes-256-gcm", "password": "pass"}
    config = Column(JSON, nullable=True)

    # UI fields
    remark = Column(Text, nullable=True)
    email = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    outbound = relationship("Outbound", back_populates="users")
    rules = relationship("Rule", secondary="user_rules", back_populates="users")


class UserRule(Base):
    """
    Many-to-many relationship table between users and rules.
    """
    __tablename__ = "user_rules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rule_id = Column(Integer, ForeignKey("rules.id", ondelete="CASCADE"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class SystemSettings(Base):
    """
    System-wide default settings for user creation.
    This is a singleton table (only one row).
    """
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)

    # Default user parameters
    default_protocol = Column(String(20), default="socks5", nullable=False)
    default_expiration_days = Column(Integer, default=30, nullable=False)
    default_max_send_byte = Column(BigInteger, default=0, nullable=False)  # 0 = unlimited
    default_max_receive_byte = Column(BigInteger, default=0, nullable=False)  # 0 = unlimited
    default_send_limit = Column(Integer, default=0, nullable=False)  # KB/s, 0 = unlimited
    default_receive_limit = Column(Integer, default=0, nullable=False)  # KB/s, 0 = unlimited
    default_max_conn_count = Column(Integer, default=0, nullable=False)  # 0 = unlimited

    # Username/Password generation pattern
    # Default: 3 letters + 3 numbers (e.g., abc123)
    username_pattern = Column(String(50), default="LLL###", nullable=False)  # L=letter, #=digit
    password_pattern = Column(String(50), default="LLL###", nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class APIKey(Base):
    """
    API keys for external system integration.
    Allows machine-to-machine authentication without JWT.
    """
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # Descriptive name for the key
    key_hash = Column(String(255), unique=True, nullable=False, index=True)  # Hashed API key
    key_prefix = Column(String(10), nullable=False)  # First 8 chars for identification
    is_active = Column(Boolean, default=True, nullable=False)

    # Permissions
    can_read = Column(Boolean, default=True, nullable=False)
    can_write = Column(Boolean, default=False, nullable=False)
    can_delete = Column(Boolean, default=False, nullable=False)

    # Rate limiting
    rate_limit_per_minute = Column(Integer, default=60, nullable=False)

    # Metadata
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
