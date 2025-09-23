from datetime import datetime
from decimal import Decimal
import enum
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, update
from sqlalchemy.orm import selectinload

from app import models
from app import domains
from app.use_cases import AbstractDatabaseRepo


def as_dict(model_instance):
    """
    Converts a SQLAlchemy model instance to a dictionary.
    Handles Enum objects by converting them to their values.
    """
    if not model_instance:
        return None
    
    data = {}
    for column in model_instance.__table__.columns:
        value = getattr(model_instance, column.name)
        if isinstance(value, enum.Enum):
            data[column.name] = value.value
        else:
            data[column.name] = value
    return data


class SqlAlchemyDatabaseRepo(AbstractDatabaseRepo):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_services(self, query: Optional[str] = None) -> List[domains.Service]:
        like_query = f"%{query or ''}%"
        stmt = (
            select(models.Service)
            .where(
                models.Service.status == models.ServiceStatus.AVAILABLE,
                models.Service.title.ilike(like_query)
            )
            .order_by(models.Service.title)
        )

        result = await self._session.scalars(stmt)

        return [domains.Service(**s.as_dict()) for s in result.all()]
    
    async def get_service_by_id(self, service_id: int) -> Optional[domains.Service]:
        service_orm = await self._session.get(models.Service, service_id)
        return domains.Service(**service_orm.as_dict()) if service_orm else None
    
    async def get_order_details(self, order_id: int) -> Optional[domains.OrderServices]:
        stmt = (
            select(models.Order)
            .where(models.Order.id == order_id)
            .options(selectinload(models.Order.service_associations).selectinload(models.OrdersServices.service))
        )
        order_orm = await self._session.scalar(stmt)
        if not order_orm:
            return None

        services = [domains.Service(**assoc.service.as_dict()) for assoc in order_orm.service_associations]
        total_price = sum(assoc.price_at_order_time for assoc in order_orm.service_associations)

        return domains.OrderServices(
            id=order_orm.id,
            status=order_orm.status.value,
            services=services,
            total_price=float(total_price),
            created_by=order_orm.created_by,
            target_system_info=order_orm.target_system_info,
            parameters_and_comments=order_orm.parameters_and_comments,
            risk_score=order_orm.risk_score
        )
    
    async def get_draft_order_by_user_id(self, user_id: int) -> Optional[domains.Order]:
        stmt = select(models.Order).where(
            models.Order.created_by == user_id,
            models.Order.status == models.OrderStatus.DRAFT
        )
        order_orm = await self._session.scalar(stmt)
        return domains.Order(**order_orm.as_dict()) if order_orm else None
    
    async def create_draft_order(self, user_id: int) -> domains.Order:
        new_order = models.Order(created_by=user_id, created_at=datetime.now())
        self._session.add(new_order)
        await self._session.flush()
        return domains.Order(**new_order.as_dict())

    async def add_service_to_order(self, order_id: int, service_id: int, price: Decimal) -> None:
        new_association = models.OrdersServices(
            order_id=order_id,
            service_id=service_id,
            price_at_order_time=price
        )
        self._session.add(new_association)
        await self._session.flush()

    async def is_service_in_order(self, order_id: int, service_id: int) -> bool:
        stmt = select(models.OrdersServices).where(
            models.OrdersServices.order_id == order_id,
            models.OrdersServices.service_id == service_id
        )
        result = await self._session.scalar(stmt)
        return result is not None

    async def logically_delete_order(self, order_id: int) -> None:
        stmt = text(
            """
            UPDATE orders
            SET status = :new_status
            WHERE id = :order_id AND status = :old_status
            """
        )
        await self._session.execute(
            stmt,
            {
                "new_status": models.OrderStatus.DELETED.value,
                "order_id": order_id,
                "old_status": models.OrderStatus.DRAFT.value
            }
        )

    async def get_cart_item_count(self, user_id: int) -> int:
        draft_order = await self.get_draft_order_by_user_id(user_id=user_id)
        if not draft_order:
            return 0
        
        stmt = select(func.count()).select_from(models.OrdersServices).where(
            models.OrdersServices.order_id == draft_order.id
        )
        count = await self._session.scalar(stmt)
        return count or 0
    
    async def get_order_by_id(self, order_id: int) -> Optional[domains.Order]:
        order_orm = await self._session.get(models.Order, order_id)
        return domains.Order(**order_orm.as_dict()) if order_orm else None

    async def update_order_details(self, order_id: int, **kwargs) -> None:
        stmt = update(models.Order).where(models.Order.id == order_id).values(**kwargs)
        await self._session.execute(stmt)

    async def update_service_in_order(self, order_id: int, service_id: int, **kwargs) -> None:
        stmt = (
            update(models.OrdersServices)
            .where(
                models.OrdersServices.order_id == order_id,
                models.OrdersServices.service_id == service_id
            )
            .values(**kwargs)
        )
        await self._session.execute(stmt)