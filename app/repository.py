# app/repository.py

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select, func, text, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import models, domains
from app.auth.security import get_password_hash
from app.interfaces import AbstractDatabaseRepo

class SqlAlchemyDatabaseRepo(AbstractDatabaseRepo):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # --- User Methods ---
    async def get_user_by_id(self, user_id: int) -> Optional[models.User]:
        # Внутренние методы могут возвращать ORM, но публичные - нет.
        # Этот метод нужен для get_current_user, который вернет UserRead.
        return await self._session.get(models.User, user_id)

    async def get_user_by_login(self, login: str) -> Optional[models.User]:
        stmt = select(models.User).where(models.User.login == login)
        return await self._session.scalar(stmt)

    async def create_user(self, user_data: domains.UserCreate) -> domains.UserRead:
        hashed_password = get_password_hash(user_data.password)
        new_user = models.User(login=user_data.login, password_hash=hashed_password)
        self._session.add(new_user)
        await self._session.flush()
        return domains.UserRead.model_validate(new_user)

    async def update_user(self, user_id: int, user_data: domains.UserUpdate) -> Optional[domains.UserRead]:
        user_orm = await self._session.get(models.User, user_id)
        if not user_orm:
            return None
        if user_data.login:
            user_orm.login = user_data.login
        await self._session.flush()
        return domains.UserRead.model_validate(user_orm)

    # --- Service Methods ---
    async def get_service_by_id(self, service_id: int) -> Optional[domains.Service]:
        service_orm = await self._session.get(models.Service, service_id)
        return domains.Service.model_validate(service_orm) if service_orm else None

    async def get_services_with_filters(self, title: Optional[str], assessment_type: Optional[str]) -> List[domains.Service]:
        stmt = select(models.Service).where(models.Service.status != models.ServiceStatus.DELETED).order_by(models.Service.title)
        if title:
            stmt = stmt.where(models.Service.title.ilike(f"%{title}%"))
        if assessment_type:
            stmt = stmt.where(models.Service.assessment_type == assessment_type)
        result = await self._session.scalars(stmt)
        return [domains.Service.model_validate(s) for s in result.all()]

    async def create_service(self, service_data: domains.ServiceCreate) -> domains.Service:
        new_service_orm = models.Service(**service_data.model_dump())
        self._session.add(new_service_orm)
        await self._session.flush()
        return domains.Service.model_validate(new_service_orm)

    async def update_service(self, service_id: int, service_data: domains.ServiceUpdate, image_url: Optional[str] = None) -> Optional[domains.Service]:
        service_orm = await self._session.get(models.Service, service_id)
        if not service_orm:
            return None
        
        for key, value in service_data.model_dump(exclude_unset=True).items():
            setattr(service_orm, key, value)
        
        if image_url is not None:
            service_orm.image_url = image_url

        await self._session.flush()
        return domains.Service.model_validate(service_orm)

    async def delete_service(self, service_id: int) -> bool:
        service_orm = await self._session.get(models.Service, service_id)
        if not service_orm:
            return False
        await self._session.delete(service_orm)
        await self._session.flush()
        return True

    # --- Order & Cart Methods ---
    async def get_draft_order_by_user_id(self, user_id: int) -> Optional[models.Order]:
        # Этот метод является внутренним для use cases, поэтому может возвращать ORM
        stmt = select(models.Order).where(
            models.Order.created_by == user_id,
            models.Order.status == models.OrderStatus.DRAFT
        )
        return await self._session.scalar(stmt)

    async def create_draft_order(self, user_id: int) -> models.Order:
        # Аналогично, внутренний метод
        new_order = models.Order(created_by=user_id, created_at=datetime.now(timezone.utc))
        self._session.add(new_order)
        await self._session.flush()
        return new_order

    async def add_service_to_order(self, order_id: int, service_id: int, price: Decimal) -> None:
        new_assoc = models.OrdersServices(
            order_id=order_id, service_id=service_id, price_at_order_time=price
        )
        self._session.add(new_assoc)
        await self._session.flush()

    async def get_association(self, order_id: int, service_id: int) -> Optional[models.OrdersServices]:
        stmt = select(models.OrdersServices).where(
            models.OrdersServices.order_id == order_id,
            models.OrdersServices.service_id == service_id
        )
        return await self._session.scalar(stmt)
    
    async def delete_service_from_order(self, order_id: int, service_id: int) -> bool:
        stmt = delete(models.OrdersServices).where(
            models.OrdersServices.order_id == order_id,
            models.OrdersServices.service_id == service_id
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0

    async def get_orders_with_filters(self, status: Optional[str], date_from: Optional[date], date_to: Optional[date]) -> List[domains.OrderSummary]:
        stmt = (
            select(models.Order, models.User.login)
            .join(models.User, models.Order.created_by == models.User.id)
            .where(models.Order.status.notin_([models.OrderStatus.DRAFT, models.OrderStatus.DELETED]))
            .order_by(models.Order.created_at.desc())
        )
        if status:
            stmt = stmt.where(models.Order.status == status)
        if date_from:
            stmt = stmt.where(models.Order.formation_date >= date_from)
        if date_to:
            stmt = stmt.where(models.Order.formation_date <= date_to)
        
        result = await self._session.execute(stmt)
        summaries = []
        for order_orm, login in result.all():
            summary = domains.OrderSummary.model_validate(order_orm)
            summary.creator_login = login
            summaries.append(summary)
        return summaries

    async def get_full_order_details(self, order_id: int) -> Optional[domains.OrderDetails]:
        stmt = (
            select(models.Order)
            .where(models.Order.id == order_id)
            .options(
                selectinload(models.Order.service_associations).selectinload(models.OrdersServices.service),
                selectinload(models.Order.creator),
                selectinload(models.Order.moderator)
            )
        )
        order_orm = await self._session.scalar(stmt)
        if not order_orm or order_orm.status == models.OrderStatus.DELETED:
            return None
        
        services_in_order = [
            domains.ServiceInOrder(
                service=domains.Service.model_validate(assoc.service),
                protection_level=assoc.protection_level,
                comment=assoc.comment,
                price_at_order_time=assoc.price_at_order_time
            ) for assoc in order_orm.service_associations
        ]

        details = domains.OrderDetails(
            id=order_orm.id,
            status=order_orm.status,
            created_at=order_orm.created_at,
            creator_login=order_orm.creator.login,
            moderator_login=order_orm.moderator.login if order_orm.moderator else None,
            formation_date=order_orm.formation_date,
            completion_date=order_orm.completion_date,
            target_system_info=order_orm.target_system_info,
            risk_score=order_orm.risk_score,
            services=services_in_order
        )
        return details

    async def update_order(self, order_id: int, **kwargs) -> None:
        stmt = update(models.Order).where(models.Order.id == order_id).values(**kwargs)
        await self._session.execute(stmt)
        
    async def update_association(self, order_id: int, service_id: int, **kwargs) -> None:
        stmt = (
            update(models.OrdersServices)
            .where(models.OrdersServices.order_id == order_id, models.OrdersServices.service_id == service_id)
            .values(**kwargs)
        )
        await self._session.execute(stmt)

    async def get_cart_item_count(self, user_id: int) -> int:
        draft_order = await self.get_draft_order_by_user_id(user_id)
        if not draft_order:
            return 0
        stmt = select(func.count()).select_from(models.OrdersServices).where(
            models.OrdersServices.order_id == draft_order.id
        )
        return await self._session.scalar(stmt) or 0