# tests/test_use_cases.py

from fastapi import UploadFile
import pytest
from datetime import date, datetime
from decimal import Decimal
from typing import IO, List, Optional
from unittest.mock import MagicMock

from app import domains, models, interfaces
from app.use_cases import order as order_use_cases
from app.use_cases import service as service_use_cases

pytestmark = pytest.mark.asyncio

# --- Фейковые зависимости для изоляции ---

class InMemoryRepository(interfaces.AbstractDatabaseRepo):
    """
    Фейковый репозиторий, который хранит данные в словарях.
    Реализует ВСЕ абстрактные методы, чтобы быть полноценной заменой.
    """
    def __init__(self):
        self.users = {}
        self.services = {}
        self.orders = {}
        self.associations = []
        self._id_counter = 0

    def _next_id(self):
        self._id_counter += 1
        return self._id_counter

    async def get_user_by_id(self, user_id: int):
        return self.users.get(user_id)

    async def get_user_by_login(self, login: str):
        for user in self.users.values():
            if user.login == login:
                return user
        return None

    async def create_user(self, user_data: domains.UserCreate):
        new_id = self._next_id()
        user = models.User(id=new_id, login=user_data.login, password_hash="hashed_password")
        self.users[new_id] = user
        return user

    async def update_user(self, user_id: int, user_data: domains.UserUpdate):
        if user_id in self.users:
            if user_data.login:
                self.users[user_id].login = user_data.login
            return self.users[user_id]
        return None

    async def get_service_by_id(self, service_id: int):
        service_orm = self.services.get(service_id)
        return domains.Service.model_validate(service_orm) if service_orm else None

    async def get_services_with_filters(self, title: Optional[str], assessment_type: Optional[str]):
        return [domains.Service.model_validate(s) for s in self.services.values()]

    async def create_service(self, service_data: domains.ServiceCreate):
        new_id = self._next_id()
        service = models.Service(id=new_id, **service_data.model_dump())
        self.services[new_id] = service
        return domains.Service.model_validate(service)

    async def update_service(self, service_id: int, service_data: domains.ServiceUpdatePartial):
        if service_id in self.services:
            update_data = service_data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(self.services[service_id], key, value)
            return domains.Service.model_validate(self.services[service_id])
        return None

    async def delete_service(self, service_id: int) -> bool:
        if service_id in self.services:
            del self.services[service_id]
            return True
        return False

    async def get_draft_order_by_user_id(self, user_id: int) -> Optional[domains.OrderDetails]:
        """Находит ORM-модель заказа и конвертирует ее в Pydantic-модель."""
        for order_orm in self.orders.values():
            if order_orm.created_by == user_id and order_orm.status == models.OrderStatus.DRAFT:
                return await self.get_full_order_details(order_orm.id)
        return None

    async def create_draft_order(self, user_id: int) -> domains.OrderDetails:
        """Создает ORM-модель и сразу конвертирует ее в Pydantic-модель."""
        new_id = self._next_id()
        if not self.users.get(user_id):
            self.users[user_id] = models.User(id=user_id, login=f"user{user_id}")
            
        order = models.Order(id=new_id, created_by=user_id, status=models.OrderStatus.DRAFT, created_at=datetime.now())
        self.orders[new_id] = order
        return await self.get_full_order_details(new_id)

    async def add_service_to_order(self, order_id: int, service_id: int, price: Decimal):
        self.associations.append(models.OrdersServices(
            order_id=order_id, 
            service_id=service_id, 
            price_at_order_time=price,
            protection_level=models.ProtectionLevel.NONE
        ))

    async def get_association(self, order_id: int, service_id: int):
        for assoc in self.associations:
            if assoc.order_id == order_id and assoc.service_id == service_id:
                return assoc
        return None

    async def delete_service_from_order(self, order_id: int, service_id: int) -> bool:
        initial_len = len(self.associations)
        self.associations = [a for a in self.associations if not (a.order_id == order_id and a.service_id == service_id)]
        return len(self.associations) < initial_len

    async def get_orders_with_filters(self, user_id: int, status: Optional[str], date_from: Optional[date], date_to: Optional[date]):
        return []

    async def get_full_order_details(self, order_id: int) -> Optional[domains.OrderDetails]:
        """
        Главный метод-конвертер. Собирает ORM-объекты и преобразует их 
        в доменную модель `OrderDetails`, как это делает настоящий репозиторий.
        """
        order_orm = self.orders.get(order_id)
        if not order_orm: 
            return None
        
        creator_orm = self.users.get(order_orm.created_by)
        moderator_orm = self.users.get(order_orm.moderated_by) if order_orm.moderated_by else None
        
        order_associations = [a for a in self.associations if a.order_id == order_id]
        
        services_in_order = []
        for assoc in order_associations:
            service_orm = self.services.get(assoc.service_id)
            if service_orm:
                services_in_order.append(domains.ServiceInOrder(
                    service=domains.Service.model_validate(service_orm),
                    protection_level=assoc.protection_level,
                    comment=assoc.comment,
                    price_at_order_time=assoc.price_at_order_time
                ))
        
        return domains.OrderDetails(
            id=order_orm.id,
            status=order_orm.status,
            created_at=order_orm.created_at,
            created_by=order_orm.created_by,
            creator_login=creator_orm.login if creator_orm else "unknown",
            moderator_login=moderator_orm.login if moderator_orm else None,
            formation_date=order_orm.formation_date,
            completion_date=order_orm.completion_date,
            target_system_info=order_orm.target_system_info,
            risk_score=order_orm.risk_score,
            services=services_in_order
        )

    async def update_order(self, order_id: int, **kwargs):
        if order_id in self.orders:
            for key, value in kwargs.items():
                setattr(self.orders[order_id], key, value)

    async def update_association(self, order_id: int, service_id: int, **kwargs):
        assoc = await self.get_association(order_id, service_id)
        if assoc:
            for key, value in kwargs.items():
                setattr(assoc, key, value)

    async def get_cart_item_count(self, user_id: int) -> int:
        order_details = await self.get_draft_order_by_user_id(user_id)
        if not order_details: return 0
        return len(order_details.services)

class InMemoryFileStorage(interfaces.AbstractFileStorage):
    """Фейковое файловое хранилище."""
    def __init__(self):
        self.files = set()

    def save(self, file: IO, filename: str, content_type: str) -> str:
        self.files.add(filename)
        return f"http://fake-storage.com/{filename}"
    
    def delete(self, file_url: str) -> None:
        filename = file_url.split('/')[-1]
        if filename in self.files:
            self.files.remove(filename)


class TestOrderUseCases:
    def _create_valid_service(self, **kwargs) -> models.Service:
        defaults = {
            "title": "Default Service",
            "short_description": "sd",
            "description": "d",
            "price": Decimal("100"),
            "impact_level": 1,
            "assessment_type": models.ServiceAssessmentType.NETWORK_SCAN,
            "status": models.ServiceStatus.AVAILABLE,
        }
        defaults.update(kwargs)
        return models.Service(**defaults)

    async def test_add_service_to_cart_creates_new_order(self):
        repo = InMemoryRepository()
        user_id = 1
        service_id = repo._next_id()
        repo.services[service_id] = self._create_valid_service(id=service_id)

        cart = await order_use_cases.add_service_to_cart(repo, user_id, service_id)

        assert len(repo.orders) == 1
        new_order_orm = list(repo.orders.values())[0]
        assert new_order_orm.created_by == user_id
        assert new_order_orm.status == models.OrderStatus.DRAFT
        
        assert len(repo.associations) == 1
        assert repo.associations[0].order_id == new_order_orm.id
        assert repo.associations[0].service_id == service_id
        
        assert isinstance(cart, domains.OrderDetails)
        assert len(cart.services) == 1

    async def test_form_order_success(self):
        repo = InMemoryRepository()
        user_id = 1
        service1_id = repo._next_id()
        repo.services[service1_id] = self._create_valid_service(id=service1_id, title="Crit Service", impact_level=3)
        
        draft_order = await repo.create_draft_order(user_id)
        await repo.add_service_to_order(draft_order.id, service1_id, Decimal("100.00"))

        form_data = domains.OrderFormPayload(
            target_system_info="test.com",
            services=[
                domains.OrderFormServicePayload(service_id=service1_id, protection_level=domains.ProtectionLevel.BASIC, comment=""),
            ]
        )
        
        await order_use_cases.form_order(repo, draft_order.id, user_id, form_data)

        formed_order = repo.orders[draft_order.id]
        assert formed_order.status == models.OrderStatus.FORMED
        assert formed_order.target_system_info == "test.com"
        assert formed_order.risk_score is None

    async def test_complete_order_calculates_risk_success(self):
        repo = InMemoryRepository()
        user_id = 1
        moderator_id = 99
        repo.users[user_id] = models.User(id=user_id, login=f"user{user_id}")
        repo.users[moderator_id] = models.User(id=moderator_id, login=f"mod{moderator_id}")
        
        order_id = repo._next_id()
        order = models.Order(id=order_id, created_by=user_id, created_at=datetime.now(), status=models.OrderStatus.FORMED)
        repo.orders[order_id] = order
        
        service1_id = repo._next_id()
        repo.services[service1_id] = self._create_valid_service(id=service1_id, impact_level=3)
        service2_id = repo._next_id()
        repo.services[service2_id] = self._create_valid_service(id=service2_id, impact_level=2)
        
        repo.associations.append(models.OrdersServices(
            order_id=order_id, service_id=service1_id, 
            protection_level=models.ProtectionLevel.BASIC, 
            price_at_order_time=Decimal("100")
        ))
        repo.associations.append(models.OrdersServices(
            order_id=order_id, service_id=service2_id, 
            protection_level=models.ProtectionLevel.FULL,
            price_at_order_time=Decimal("200")
        ))

        await order_use_cases.complete_order(repo, order_id, moderator_id)

        completed_order = repo.orders[order_id]
        assert completed_order.status == models.OrderStatus.COMPLETED
        assert completed_order.moderated_by == moderator_id
        assert completed_order.risk_score == 6

    async def test_complete_order_fails_if_not_formed(self):
        repo = InMemoryRepository()
        user_id = 1
        moderator_id = 2
        draft_order = await repo.create_draft_order(user_id)

        with pytest.raises(interfaces.OrderNotFoundError, match="A 'formed' order is required"):
            await order_use_cases.complete_order(repo, draft_order.id, moderator_id)

    async def test_delete_draft_order_success(self):
        repo = InMemoryRepository()
        user_id = 1
        draft_order = await repo.create_draft_order(user_id)

        await order_use_cases.delete_draft_order(repo, draft_order.id, user_id)

        deleted_order = repo.orders[draft_order.id]
        assert deleted_order.status == models.OrderStatus.DELETED
        
    async def test_delete_draft_order_fails_if_wrong_user(self):
        repo = InMemoryRepository()
        owner_user_id = 1
        other_user_id = 2
        draft_order = await repo.create_draft_order(owner_user_id)
        
        with pytest.raises(interfaces.OrderNotFoundError):
            await order_use_cases.delete_draft_order(repo, draft_order.id, other_user_id)


class TestServiceUseCases:
    def _create_valid_service(self, **kwargs) -> models.Service:
        defaults = {
            "title": "Default Service",
            "short_description": "sd",
            "description": "d",
            "price": Decimal("100"),
            "impact_level": 1,
            "assessment_type": models.ServiceAssessmentType.NETWORK_SCAN,
            "status": models.ServiceStatus.AVAILABLE,
        }
        defaults.update(kwargs)
        return models.Service(**defaults)

    async def test_delete_service_with_image(self):
        db_repo = InMemoryRepository()
        file_storage = InMemoryFileStorage()
        
        service_id = db_repo._next_id()
        image_url = "http://fake-storage.com/image.png"
        
        db_repo.services[service_id] = self._create_valid_service(id=service_id, image_url=image_url)
        file_storage.files.add("image.png")

        await service_use_cases.delete_service(db_repo, file_storage, service_id)

        assert service_id not in db_repo.services
        assert "image.png" not in file_storage.files

    async def test_update_service_image_deletes_old_one(self):
        db_repo = InMemoryRepository()
        file_storage = InMemoryFileStorage()
        
        service_id = db_repo._next_id()
        old_image_url = "http://fake-storage.com/old_image.png"
        
        db_repo.services[service_id] = self._create_valid_service(id=service_id, image_url=old_image_url)
        file_storage.files.add("old_image.png")

        mock_image = MagicMock(spec=UploadFile)
        mock_image.filename = "new_image.jpg"
        mock_image.content_type = "image/jpeg"
        mock_image.file = MagicMock(spec=IO)
        
        await service_use_cases.update_service_image(db_repo, file_storage, service_id, mock_image)

        assert "old_image.png" not in file_storage.files
        assert len(file_storage.files) == 1
        
        updated_service = await db_repo.get_service_by_id(service_id)
        assert ".jpg" in updated_service.image_url