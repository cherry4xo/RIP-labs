from enum import Enum
from typing import Optional, List

from tortoise import Model, fields
from tortoise.exceptions import DoesNotExist, IntegrityError
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, PrimaryKeyConstraint, Enum, DateTime


class OrderStatus(Enum, str):
    DRAFT = "draft"
    DELETED = "deleted"
    FORMED = "formed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ServiceStatus(Enum, str):
    DELETED = "deleted"
    AVAILABLE = "available"


Base = declarative_base()


class Service(Base):
    __tablename__ = "services"

    id = Column("id", Integer, primary_key=True)
    title = Column("title", String(128))
    description = Column("description", String)
    status = Column("status", Enum(ServiceStatus), default=ServiceStatus.AVAILABLE)
    image_url = Column("image_url", String(256), nullable=True)

    orders = relationship("Order", secondary="orders_services", back_populates="services")


class User(Base):
    __tablename__ = "users"

    id = Column("id", Integer, primary_key=True)
    login = Column("login", String(64), unique=True)
    password_hash = Column("password_hash", String(255), nullable=True)
    is_moderator = Column("is_moderator", Boolean, default=False)

    created_orders = relationship(
        "Order",
        back_populates="creator",
        foreign_keys="Order.created_by"
    )

    moderated_orders = relationship(
        "Order",
        back_populates="moderator",
        foreign_keys="Order.moderated_by"
    )


class Order(Base):
    __tablename__ = "orders"

    id = Column("id", Integer, primary_key=True)
    status = Column("status", Enum(OrderStatus), default=OrderStatus.DRAFT)
    created_at = Column("created_at", DateTime)
    created_by = Column("created_by", Integer, ForeignKey("users.id"))
    formation_date = Column("formation_date", DateTime, nullable=True)
    completion_date = Column("completion_date", DateTime, nullable=True)
    moderated_by = Column("moderated_by", ForeignKey("users.id"), nullable=True)

    creator = relationship(
        "User",
        back_populates="created_orders",
        foreign_keys=[created_by]
    )

    moderator = relationship(
        "User",
        back_populates="moderated_orders",
        foreign_keys=[moderated_by]
    )

    services = relationship("Service", secondary="orders_services", back_populates="orders")


class OrdersServices(Base):
    __tablename__ = "orders_services"

    service_id = Column("service_id", ForeignKey("services.id"), primary_key=True)
    order_id = Column("order_id", ForeignKey("orders.id"), primary_key=True)
