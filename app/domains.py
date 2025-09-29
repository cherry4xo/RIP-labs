# app/domains.py

from datetime import datetime, date
import enum
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, Field

# --- Enums ---
class ProtectionLevel(enum.StrEnum):
    NONE = "none"
    BASIC = "basic"
    FULL = "full"

class ServiceAssessmentType(enum.StrEnum):
    NETWORK_SCAN = "network_scan"
    WEB_APP_PENTEST = "web_app_pentest"
    INFRASTRUCTURE_AUDIT = "infrastructure_audit"

class ServiceStatus(enum.StrEnum):
    DELETED = "deleted"
    AVAILABLE = "available"

class OrderStatus(enum.StrEnum):
    DRAFT = "draft"
    DELETED = "deleted"
    FORMED = "formed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# --- Service Schemas ---
class ServiceBase(BaseModel):
    title: str = Field(min_length=3, max_length=128)
    short_description: Optional[str] = None
    description: str
    price: Decimal = Field(gt=0)
    impact_level: int = Field(ge=1, le=3)
    assessment_type: ServiceAssessmentType

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(ServiceBase):
    pass

class Service(ServiceBase):
    id: int
    status: ServiceStatus
    image_url: Optional[str] = None
    class Config: from_attributes = True

# --- User & Auth Schemas ---
class UserCreate(BaseModel):
    login: str = Field(min_length=3)
    password: str = Field(min_length=4)

class UserUpdate(BaseModel):
    login: Optional[str] = Field(min_length=3, default=None)

class UserRead(BaseModel):
    id: int
    login: str
    is_moderator: bool
    class Config: from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: Optional[str] = None

# --- Order & Cart Schemas ---
class CartInfo(BaseModel):
    order_id: int
    item_count: int

class CartItemAdd(BaseModel):
    service_id: int

class CartItemUpdate(BaseModel):
    protection_level: ProtectionLevel
    comment: Optional[str] = None

class OrderUpdate(BaseModel):
    target_system_info: str = Field(min_length=5)

class OrderFormServicePayload(BaseModel):
    service_id: int
    protection_level: ProtectionLevel
    comment: Optional[str] = None

class OrderFormPayload(BaseModel):
    target_system_info: str = Field(min_length=5)
    services: List[OrderFormServicePayload]

class ServiceInOrder(BaseModel):
    service: Service
    protection_level: ProtectionLevel
    comment: Optional[str] = None
    price_at_order_time: Decimal

class OrderDetails(BaseModel):
    id: int
    status: OrderStatus
    created_at: datetime
    creator_login: str
    moderator_login: Optional[str] = None
    formation_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    target_system_info: Optional[str] = None
    risk_score: Optional[int] = None
    services: List[ServiceInOrder] = []
    class Config: from_attributes = True

class OrderSummary(BaseModel):
    id: int
    status: OrderStatus
    formation_date: Optional[datetime] = None
    risk_score: Optional[int] = None
    creator_login: str
    class Config: from_attributes = True