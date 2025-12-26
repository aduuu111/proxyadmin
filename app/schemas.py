"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


# ===========================
# Admin Schemas
# ===========================

class AdminBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)


class AdminCreate(AdminBase):
    password: str = Field(..., min_length=6)


class AdminUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=6)
    avatar: Optional[str] = None


class AdminResponse(AdminBase):
    id: int
    avatar: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ===========================
# Outbound Schemas
# ===========================

class OutboundBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    protocol: str = Field(default="direct")
    local_interface_ip: Optional[str] = None
    remark: Optional[str] = None
    max_users: int = Field(default=10, ge=1)  # Max users per IP


class OutboundCreate(OutboundBase):
    config: dict = Field(default_factory=dict)
    is_auto_generated: bool = False


class OutboundUpdate(BaseModel):
    name: Optional[str] = None
    protocol: Optional[str] = None
    config: Optional[dict] = None
    local_interface_ip: Optional[str] = None
    remark: Optional[str] = None
    max_users: Optional[int] = Field(None, ge=1)


class OutboundResponse(OutboundBase):
    id: int
    config: dict
    is_auto_generated: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OutboundWithStats(OutboundResponse):
    """Outbound with usage statistics"""
    active_user_count: int = 0  # Number of active users using this IP
    available_slots: int = 0  # Remaining slots (max_users - active_user_count)


# ===========================
# Rule Schemas
# ===========================

class RuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1)


class RuleCreate(RuleBase):
    priority: int = Field(default=0)
    remark: Optional[str] = None


class RuleUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None
    priority: Optional[int] = None
    remark: Optional[str] = None


class RuleResponse(RuleBase):
    id: int
    priority: int
    remark: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ===========================
# User Schemas
# ===========================

class UserBase(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    port: int = Field(..., ge=1, le=65535)
    protocol: str = Field(default="socks5")


class UserCreate(UserBase):
    password: str = Field(..., min_length=1)
    total_traffic: int = Field(default=0, ge=0)
    expire_time: datetime
    enable: bool = Field(default=True)
    send_limit: int = Field(default=0, ge=0)
    receive_limit: int = Field(default=0, ge=0)
    max_conn_count: int = Field(default=0, ge=0)
    outbound_id: int
    rule_ids: List[int] = Field(default_factory=list)
    config: Optional[dict] = None
    remark: Optional[str] = None
    email: Optional[str] = None


class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    port: Optional[int] = Field(None, ge=1, le=65535)
    protocol: Optional[str] = None
    total_traffic: Optional[int] = Field(None, ge=0)
    expire_time: Optional[datetime] = None
    enable: Optional[bool] = None
    send_limit: Optional[int] = Field(None, ge=0)
    receive_limit: Optional[int] = Field(None, ge=0)
    max_conn_count: Optional[int] = Field(None, ge=0)
    outbound_id: Optional[int] = None
    rule_ids: Optional[List[int]] = None
    config: Optional[dict] = None
    remark: Optional[str] = None
    email: Optional[str] = None


class UserResponse(UserBase):
    id: int
    password: str  # Add password field to response
    total_traffic: int
    up_traffic: int
    down_traffic: int
    expire_time: datetime
    last_seen: Optional[datetime] = None
    enable: bool
    status: str
    send_limit: int
    receive_limit: int
    max_conn_count: int
    outbound_id: int
    config: Optional[dict] = None
    remark: Optional[str] = None
    email: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Related data
    outbound: Optional[OutboundResponse] = None
    rules: List[RuleResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# ===========================
# Authentication Schemas
# ===========================

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


# ===========================
# Dashboard Schemas
# ===========================

class DashboardStats(BaseModel):
    cpu_usage: float
    memory_usage: float
    total_memory: int
    used_memory: int
    bandwidth_up: int
    bandwidth_down: int
    online_users: int
    total_users: int
    system_version: str
    uptime: str


# ===========================
# Response Wrappers
# ===========================

class SuccessResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[dict] = None


class ErrorResponse(BaseModel):
    code: int
    message: str
    detail: Optional[str] = None


# ===========================
# System Settings Schemas
# ===========================

class SystemSettingsBase(BaseModel):
    default_protocol: str = Field(default="socks5")
    default_expiration_days: int = Field(default=30, ge=1)
    default_max_send_byte: int = Field(default=0, ge=0)
    default_max_receive_byte: int = Field(default=0, ge=0)
    default_send_limit: int = Field(default=0, ge=0)
    default_receive_limit: int = Field(default=0, ge=0)
    default_max_conn_count: int = Field(default=0, ge=0)
    username_pattern: str = Field(default="LLL###")
    password_pattern: str = Field(default="LLL###")


class SystemSettingsUpdate(SystemSettingsBase):
    pass


class SystemSettingsResponse(SystemSettingsBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ===========================
# Game/Rule Inventory Schemas
# ===========================

class GameInventory(BaseModel):
    """Inventory information for a game (rule)"""
    rule_id: int
    rule_name: str
    total_ips: int  # Total number of IPs (outbounds)
    available_ips: int  # Number of IPs available for this game
    used_ips: int  # Number of IPs already used for this game


class GameInventoryResponse(BaseModel):
    """Response with all game inventories"""
    games: List[GameInventory]
    total_outbounds: int


class QuickUserCreate(BaseModel):
    """Quick user creation with game selection"""
    rule_id: int  # Selected game
    count: int = Field(default=1, ge=1, le=100)  # Number of users to create
    protocol: Optional[str] = None  # If None, use system default
    expiration_days: Optional[int] = None  # If None, use system default


# ===========================
# API Key Schemas
# ===========================

class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    can_read: bool = True
    can_write: bool = False
    can_delete: bool = False
    rate_limit_per_minute: int = Field(default=60, ge=1, le=1000)
    expires_at: Optional[datetime] = None


class APIKeyResponse(BaseModel):
    id: int
    name: str
    key_prefix: str
    is_active: bool
    can_read: bool
    can_write: bool
    can_delete: bool
    rate_limit_per_minute: int
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class APIKeyWithSecret(APIKeyResponse):
    """Response when creating a new API key - includes the full key"""
    api_key: str


# ===========================
# External API Schemas
# ===========================

class BatchUserCreate(BaseModel):
    """Batch create multiple users"""
    users: List[UserCreate] = Field(..., min_length=1, max_length=100)


class BatchUserUpdate(BaseModel):
    """Batch update multiple users"""
    user_id: int
    updates: UserUpdate


class BatchUserUpdateRequest(BaseModel):
    updates: List[BatchUserUpdate] = Field(..., min_length=1, max_length=100)


class BatchDeleteRequest(BaseModel):
    """Batch delete users by port numbers"""
    ports: List[int] = Field(..., min_length=1, max_length=100, description="List of port numbers to delete")


class BatchOperationResult(BaseModel):
    """Result of a batch operation"""
    success_count: int
    failure_count: int
    results: List[dict]


class WebhookPayload(BaseModel):
    """Generic webhook payload"""
    event: str
    data: dict
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class UserProvisionRequest(BaseModel):
    """Request to provision a user from external system"""
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1)
    port: int = Field(..., ge=1, le=65535)
    protocol: str = "socks5"
    expire_days: int = Field(default=30, ge=1)
    total_traffic_gb: int = Field(default=0, ge=0)
    outbound_name: str
    rule_names: List[str] = Field(default_factory=list)
    email: Optional[str] = None
    remark: Optional[str] = None


class UserRenewalRequest(BaseModel):
    """Request to renew a user from external system"""
    user_id: Optional[int] = None  # Optional since we can use port instead
    extend_days: int = Field(..., ge=1)
    add_traffic_gb: int = Field(default=0, ge=0)
