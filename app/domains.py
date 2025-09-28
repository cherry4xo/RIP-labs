from datetime import datetime
import enum
from typing import List, Optional
from decimal import Decimal

from pydantic import BaseModel, Field


class ProtectionLevel(enum.StrEnum):
    NONE = "none"
    BASIC = "basic"
    FULL = "full"


class Service(BaseModel):
    id: int
    title: str
    short_description: Optional[str] = None
    description: Optional[str] = None
    status: str
    image_url: Optional[str] = None
    price: Decimal
    impact_level: int


class ServiceInOrder(BaseModel):
    service: Service
    protection_level: str
    comment: Optional[str] = None


class User(BaseModel):
    id: int
    login: str
    password_hash: Optional[str] = None
    is_moderator: bool


class Order(BaseModel):
    id: int
    status: str
    created_at: datetime
    formation_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None


class OrderServices(BaseModel):
    id: int
    status: str
    services: List[ServiceInOrder] = []
    total_price: float
    created_by: int
    target_system_info: Optional[str] = None
    risk_score: Optional[int] = None


class ServiceInForm(BaseModel):
    service_id: int
    protection_level: ProtectionLevel
    comment: Optional[str] = None


class OrderFormationForm(BaseModel):
    target_system_info: str = Field(min_length=5)
    services: List[ServiceInForm]