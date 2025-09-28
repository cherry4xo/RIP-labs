import abc
from datetime import datetime, timezone
from decimal import Decimal
import json
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import templates
from app import domains, models


class ServiceUnavailableError(Exception):
    pass

class OrderNotFoundError(Exception):
    pass


class AbstractDatabaseRepo:
    def __init__(self, session: AsyncSession):
        self._session = session

    @abc.abstractmethod
    async def get_services(self, query: Optional[str] = None) -> List[domains.Service]:
        raise NotImplementedError
    
    @abc.abstractmethod
    async def get_service_by_id(self, service_id: int) -> Optional[domains.Service]:
        raise NotImplementedError
    
    @abc.abstractmethod
    async def get_order_details(self, order_id: int) -> Optional[domains.OrderServices]:
        raise NotImplementedError
    
    @abc.abstractmethod
    async def get_draft_order_by_user_id(self, user_id: int) -> Optional[domains.Order]:
        raise NotImplementedError
    
    @abc.abstractmethod
    async def create_draft_order(self, user_id: int) -> domains.Order:
        raise NotImplementedError
    
    @abc.abstractmethod
    async def add_service_to_order(self, order_id: int, service_id: int, price: Decimal) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def is_service_in_order(self, order_id: int, service_id: int) -> bool:
        raise NotImplementedError
    
    @abc.abstractmethod
    async def logically_delete_order(self, order_id: int) -> None:
        raise NotImplementedError
    
    @abc.abstractmethod
    async def get_cart_item_count(self, user_id: int) -> None:
        raise NotImplementedError
    
    @abc.abstractmethod
    async def get_order_by_id(self, order_id: int) -> Optional[domains.Order]:
        raise NotImplementedError
    
    @abc.abstractmethod
    async def update_order_details(self, order_id: int, **kwargs) -> None:
        raise NotImplementedError
    
    @abc.abstractmethod
    async def update_service_in_order(self, order_id: int, service_id: int, **kwargs) -> None:
        raise NotImplementedError


async def view_services_list(
    repo: AbstractDatabaseRepo,
    query: Optional[str] = None
) -> List[domains.Service]:
    return await repo.get_services(query=query)


async def view_service_details(
    repo: AbstractDatabaseRepo,
    service_id: int
) -> Optional[domains.Service]:
    return await repo.get_service_by_id(service_id=service_id)


async def view_user_cart(
    repo: AbstractDatabaseRepo,
    user_id: int
) -> Optional[domains.OrderServices]:
    draft_order = await repo.get_draft_order_by_user_id(user_id=user_id)
    if not draft_order:
        return None
    
    return await repo.get_order_details(order_id=draft_order.id)


async def add_service_to_cart(
    repo: AbstractDatabaseRepo,
    user_id: int,
    service_id: int
) -> domains.OrderServices:
    service = await repo.get_service_by_id(service_id=service_id)
    if not service or service.status != "available":
        raise ServiceUnavailableError(f"Service with id={service_id} is unavailable")
    
    draft_order = await repo.get_draft_order_by_user_id(user_id=user_id)
    if not draft_order:
        draft_order = await repo.create_draft_order(user_id=user_id)

    is_present = await repo.is_service_in_order(order_id=draft_order.id, service_id=service_id)
    if is_present:
        return await repo.get_order_details(order_id=draft_order.id)
    
    await repo.add_service_to_order(
        order_id=draft_order.id,
        service_id=service_id,
        price=service.price
    )

    return await repo.get_order_details(order_id=draft_order.id)


async def delete_user_cart(
    repo: AbstractDatabaseRepo,
    user_id: int
) -> None:
    draft_order = await repo.get_draft_order_by_user_id(user_id=user_id)
    if draft_order:
        await repo.logically_delete_order(order_id=draft_order.id)


async def get_current_cart_item_count(
    repo: AbstractDatabaseRepo,
    user_id: int
) -> int:
    return await repo.get_cart_item_count(user_id=user_id)


async def form_user_order(
    repo: AbstractDatabaseRepo,
    user_id: int,
    form_data: domains.OrderFormationForm
) -> domains.Order:
    draft_order = await repo.get_draft_order_by_user_id(user_id=user_id)
    if not draft_order:
        raise OrderNotFoundError("Не найдена активная заявка для оформления.")

    # 1. Обновляем параметры для каждой услуги в заказе
    for service_data in form_data.services:
        await repo.update_service_in_order(
            order_id=draft_order.id,
            service_id=service_data.service_id,
            protection_level=service_data.protection_level,
            comment=service_data.comment
        )

    # 2. Получаем обновленные данные, чтобы выполнить расчет
    order_details = await repo.get_order_details(order_id=draft_order.id)
    if not order_details:
        raise OrderNotFoundError("Не удалось получить детали заказа после обновления.")

    # 3. --- ЛОГИКА РАСЧЕТА РИСКА ---
    protection_to_likelihood = {
        "none": 3,  # Высокая вероятность
        "basic": 2, # Средняя
        "full": 1,  # Низкая
    }
    max_risk_score = 0

    for item in order_details.services: # item - это уже ServiceInOrder
        service_full = await repo.get_service_by_id(item.service.id)
        
        likelihood = protection_to_likelihood.get(item.protection_level, 3)
        impact = service_full.impact_level
        
        risk_score = likelihood * impact
        if risk_score > max_risk_score:
            max_risk_score = risk_score
    
    # 4. Обновляем основную информацию о заказе с итоговым результатом
    await repo.update_order_details(
        order_id=draft_order.id,
        status=models.OrderStatus.FORMED,
        formation_date=datetime.now(timezone.utc).replace(tzinfo=None),
        target_system_info=form_data.target_system_info,
        risk_score=max_risk_score
    )
    
    return await repo.get_order_by_id(order_id=draft_order.id)