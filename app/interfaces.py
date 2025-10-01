import abc
from typing import List, Optional, IO
from decimal import Decimal
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app import domains, models


class ServiceUnavailableError(Exception):
    pass

class OrderNotFoundError(Exception):
    pass

class ServiceNotFoundError(Exception):
    pass


class AbstractFileStorage(abc.ABC):
    @abc.abstractmethod
    def save(self, file: IO, filename: str, content_type: str) -> str: ...
    @abc.abstractmethod
    def delete(self, file_url: str) -> None: ...

class AbstractDatabaseRepo(abc.ABC):
    # User methods
    @abc.abstractmethod
    async def get_user_by_id(self, user_id: int) -> Optional[models.User]: ...
    @abc.abstractmethod
    async def get_user_by_login(self, login: str) -> Optional[models.User]: ...
    @abc.abstractmethod
    async def create_user(self, user_data: domains.UserCreate) -> models.User: ...
    @abc.abstractmethod
    async def update_user(self, user_id: int, user_data: domains.UserUpdate) -> Optional[models.User]: ...

    # Service methods
    @abc.abstractmethod
    async def get_service_by_id(self, service_id: int) -> Optional[models.Service]: ...
    @abc.abstractmethod
    async def get_services_with_filters(self, title: Optional[str], assessment_type: Optional[str]) -> List[models.Service]: ...
    @abc.abstractmethod
    async def create_service(self, service_data: domains.ServiceCreate) -> models.Service: ...
    @abc.abstractmethod
    async def update_service(self, service_id: int, service_data: domains.ServiceUpdatePartial) -> Optional[models.Service]: ...
    @abc.abstractmethod
    async def delete_service(self, service_id: int) -> bool: ...

    # Order & Cart methods
    @abc.abstractmethod
    async def get_draft_order_by_user_id(self, user_id: int) -> Optional[domains.OrderDetails]: ...
    @abc.abstractmethod
    async def create_draft_order(self, user_id: int) -> domains.OrderDetails: ...
    @abc.abstractmethod
    async def add_service_to_order(self, order_id: int, service_id: int, price: Decimal) -> None: ...
    @abc.abstractmethod
    async def get_association(self, order_id: int, service_id: int) -> Optional[models.OrdersServices]: ...
    @abc.abstractmethod
    async def delete_service_from_order(self, order_id: int, service_id: int) -> bool: ...
    @abc.abstractmethod
    async def get_orders_with_filters(self, user_id: int, status: Optional[str], date_from: Optional[date], date_to: Optional[date]) -> List: ...
    @abc.abstractmethod
    async def get_full_order_details(self, order_id: int) -> Optional[models.Order]: ...
    @abc.abstractmethod
    async def update_order(self, order_id: int, **kwargs) -> None: ...
    @abc.abstractmethod
    async def update_association(self, order_id: int, service_id: int, **kwargs) -> None: ...
    @abc.abstractmethod
    async def get_cart_item_count(self, user_id: int) -> int: ...