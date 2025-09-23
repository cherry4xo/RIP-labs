import enum
from typing import Optional, List

from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import (Boolean, 
                        Column, Index, 
                        Integer, Numeric, 
                        String, 
                        ForeignKey, 
                        PrimaryKeyConstraint, 
                        Enum, 
                        DateTime, 
                        Float, 
                        Text, 
                        UniqueConstraint,
                        JSON
)


class OrderStatus(enum.StrEnum):
    DRAFT = "draft"
    DELETED = "deleted"
    FORMED = "formed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ServiceStatus(enum.StrEnum):
    DELETED = "deleted"
    AVAILABLE = "available"


class ServiceAssessmentType(enum.StrEnum):
    NETWORK_SCAN = "network_scan"
    WEB_APP_PENTEST = "web_app_pentest"
    INFRASTRUCTURE_AUDIT = "infrastructure_audit"


class Base:
    def as_dict(self):
        data = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, enum.Enum):
                data[column.name] = value.value
            else:
                data[column.name] = value
        return data

Base = declarative_base(cls=Base)


class Service(Base):
    __tablename__ = "services"

    id = Column("id", Integer, primary_key=True)
    title = Column("title", String(128))
    short_description = Column("short_description", String)
    description = Column("description", String)
    status = Column("status", Enum(ServiceStatus, values_callable=lambda e: [x.value for x in e]), default=ServiceStatus.AVAILABLE)
    image_url = Column("image_url", String(256), nullable=True)
    price = Column("price", Numeric(10, 2), nullable=False)
    
    impact_level = Column(Integer, nullable=False, server_default='1')

    assessment_type = Column("assessment_type", Enum(ServiceAssessmentType), nullable=False)

    order_associations = relationship("OrdersServices", back_populates="service")


class User(Base):
    __tablename__ = "users"

    id = Column("id", Integer, primary_key=True)
    login = Column("login", String(64), unique=True)
    password_hash = Column("password_hash", String(255), nullable=True)
    is_moderator = Column("is_moderator", Boolean, default=False)
    is_deleted = Column("is_deleted", Boolean, default=False)

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
    status = Column("status", Enum(OrderStatus, values_callable=lambda e: [x.value for x in e]), default=OrderStatus.DRAFT)
    created_at = Column("created_at", DateTime, nullable=False)
    created_by = Column("created_by", Integer, ForeignKey("users.id"))

    formation_date = Column("formation_date", DateTime, nullable=True)
    completion_date = Column("completion_date", DateTime, nullable=True)
    moderated_by = Column("moderated_by", ForeignKey("users.id"), nullable=True)

    target_system_info = Column(Text, nullable=True)
    parameters_and_comments = Column(Text, nullable=True)
    total_cost = Column(Integer, nullable=True)

    risk_score = Column(Integer, nullable=True)

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

    service_associations = relationship("OrdersServices", back_populates="order")

    __table_args__ = (
        Index(
            'uq_user_draft_order',
            'created_by', 'status',
            unique=True,
            postgresql_where=(status == 'draft')
        ),
    )


class OrdersServices(Base):
    __tablename__ = "orders_services"

    service_id = Column("service_id", ForeignKey("services.id"), primary_key=True)
    order_id = Column("order_id", ForeignKey("orders.id"), primary_key=True)

    price_at_order_time = Column(Numeric(10, 2), nullable=False)

    order = relationship("Order", back_populates="service_associations")
    service = relationship("Service", back_populates="order_associations")