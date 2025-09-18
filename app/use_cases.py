import abc
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import templates
from app import domains


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