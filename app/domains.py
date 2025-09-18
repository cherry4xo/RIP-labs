from datetime import datetime
from typing import List, Optional
from decimal import Decimal

from pydantic import BaseModel

class Service(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str
    image_url: Optional[str] = None
    price: Decimal

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
    services: List[Service] = []
    total_price: float