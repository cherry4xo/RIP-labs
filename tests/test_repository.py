import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from decimal import Decimal

from app import domains
from app import models
from app.models import (
    Service, Order, OrdersServices, User,
    OrderStatus, ServiceStatus, ServiceAssessmentType, ProtectionLevel
)
from app.repository import SqlAlchemyDatabaseRepo
from app.domains import OrderDetails, OrderSummary, UserCreate, UserRead, UserUpdate, ServiceCreate, ServiceUpdate


@pytest.mark.asyncio
async def test_user_operations(db_session):
    """Тестирует полный CRUD-цикл для пользователя."""
    repo = SqlAlchemyDatabaseRepo(db_session)
    
    user_data = UserCreate(login="testuser", password="password")
    created_user = await repo.create_user(user_data=user_data)
    await db_session.commit()
    assert created_user.login == "testuser"
    assert created_user.id is not None

    user_orm = await repo.get_user_by_login("testuser")
    assert user_orm is not None
    assert user_orm.login == "testuser"

    user_domain = await repo.get_user_by_id(user_orm.id)
    assert user_domain is not None
    assert user_domain.login == "testuser"
    assert isinstance(user_domain, UserRead)

    update_data = UserUpdate(login="updated_user")
    updated_user = await repo.update_user(user_orm.id, user_data=update_data)
    await db_session.commit()
    assert updated_user.login == "updated_user"


@pytest.mark.asyncio
async def test_service_crud_operations(db_session):
    repo = SqlAlchemyDatabaseRepo(db_session)
    service_data = ServiceCreate(
        title="Test Service", short_description="A test", description="A test service",
        price=Decimal("100.00"), impact_level=2, assessment_type=ServiceAssessmentType.NETWORK_SCAN
    )
    created_service = await repo.create_service(service_data=service_data)
    await db_session.commit()
    assert created_service.id is not None
    assert created_service.title == "Test Service"

    found_service = await repo.get_service_by_id(service_id=created_service.id)
    assert found_service is not None
    assert found_service.title == "Test Service"

    update_data = ServiceUpdate(
        title="Updated Title", price=Decimal("150.00"), 
        description="Updated desc", impact_level=3, 
        assessment_type=ServiceAssessmentType.WEB_APP_PENTEST, short_description="updated"
    )
    updated_service = await repo.update_service(created_service.id, service_data=update_data)
    await db_session.commit()
    assert updated_service.title == "Updated Title"
    assert updated_service.price == Decimal("150.00")

    deleted = await repo.delete_service(service_id=created_service.id)
    await db_session.commit()
    assert deleted is True
    not_found_service = await repo.get_service_by_id(service_id=created_service.id)
    assert not_found_service is None


@pytest.mark.asyncio
async def test_get_services_with_filters(db_session):
    repo = SqlAlchemyDatabaseRepo(db_session)

    s1 = Service(title="Web Scan", price=100, impact_level=1, assessment_type=ServiceAssessmentType.NETWORK_SCAN, short_description="", description="")
    s2 = Service(title="Web Pentest", price=200, impact_level=2, assessment_type=ServiceAssessmentType.WEB_APP_PENTEST, short_description="", description="")
    s3 = Service(title="Mobile Scan", price=300, impact_level=3, assessment_type=ServiceAssessmentType.NETWORK_SCAN, short_description="", description="")
    s4 = Service(title="Deleted Service", price=50, status=ServiceStatus.DELETED, impact_level=1, assessment_type=ServiceAssessmentType.NETWORK_SCAN, short_description="", description="")
    db_session.add_all([s1, s2, s3, s4])
    await db_session.commit()

    all_services = await repo.get_services_with_filters(title=None, assessment_type=None)
    assert len(all_services) == 3
    
    web_services = await repo.get_services_with_filters(title="Web", assessment_type=None)
    assert len(web_services) == 2
    assert {s.title for s in web_services} == {"Web Scan", "Web Pentest"}

    scan_services = await repo.get_services_with_filters(title=None, assessment_type=ServiceAssessmentType.NETWORK_SCAN)
    assert len(scan_services) == 2
    assert {s.title for s in scan_services} == {"Web Scan", "Mobile Scan"}


@pytest_asyncio.fixture
async def setup_orders(db_session):
    """Фикстура для создания набора пользователей и заказов для тестов."""
    user1 = User(id=1, login="user1", password_hash="hash")
    user2 = User(id=2, login="user2", password_hash="hash")
    
    # Заказы для user1
    draft_order = Order(id=1, created_by=1, status=OrderStatus.DRAFT, created_at=datetime.now())
    formed_order = Order(id=2, created_by=1, status=OrderStatus.FORMED, created_at=datetime.now(), formation_date=datetime.now() - timedelta(days=2))
    completed_order = Order(id=3, created_by=1, status=OrderStatus.COMPLETED, created_at=datetime.now(), formation_date=datetime.now() - timedelta(days=5))
    deleted_order = Order(id=4, created_by=1, status=OrderStatus.DELETED, created_at=datetime.now())

    # Заказ для user2
    other_user_order = Order(id=5, created_by=2, status=OrderStatus.FORMED, created_at=datetime.now(), formation_date=datetime.now() - timedelta(days=3))
    
    db_session.add_all([user1, user2, draft_order, formed_order, completed_order, deleted_order, other_user_order])
    await db_session.commit()
    yield


@pytest.mark.asyncio
async def test_cart_creation_and_manipulation(db_session, setup_orders):
    """Тестирует создание корзины, добавление/удаление из нее."""
    repo = SqlAlchemyDatabaseRepo(db_session)
    user_id_with_draft = 1
    
    service = Service(id=10, title="Test S1", price=100, impact_level=1, assessment_type=ServiceAssessmentType.NETWORK_SCAN, short_description="", description="")
    db_session.add(service)
    await db_session.commit()

    # 1. Проверяем, что у юзера есть черновик (из фикстуры)
    draft1 = await repo.get_draft_order_by_user_id(user_id_with_draft)
    assert draft1 is not None
    
    # 2. Добавляем услугу в существующий черновик
    await repo.add_service_to_order(draft1.id, service.id, service.price)
    await db_session.commit()
    count1 = await repo.get_cart_item_count(user_id_with_draft)
    assert count1 == 1

    # 3. Удаляем услугу из черновика
    deleted = await repo.delete_service_from_order(draft1.id, service.id)
    await db_session.commit()
    assert deleted is True
    count1_after_delete = await repo.get_cart_item_count(user_id_with_draft)
    assert count1_after_delete == 0


@pytest.mark.asyncio
async def test_get_orders_with_filters(db_session, setup_orders): # Убедитесь, что фикстура вызывается
    """Тестирует фильтрацию списка оформленных заказов."""
    repo = SqlAlchemyDatabaseRepo(db_session)
    user_id = 1
    
    # 1. Получаем все (не должно быть draft и deleted)
    all_orders = await repo.get_orders_with_filters(user_id=user_id, status=None, date_from=None, date_to=None)
    assert len(all_orders) == 2
    assert {o.status for o in all_orders} == {models.OrderStatus.FORMED, models.OrderStatus.COMPLETED}
    assert all(isinstance(o, domains.OrderSummary) for o in all_orders)
    # Проверяем, что логин создателя был добавлен
    assert all_orders[0].creator_login == "user1"

    # 2. Фильтруем по статусу
    formed_orders = await repo.get_orders_with_filters(user_id=user_id, status=models.OrderStatus.FORMED, date_from=None, date_to=None)
    assert len(formed_orders) == 1
    assert formed_orders[0].status == models.OrderStatus.FORMED

    # 3. Фильтруем по дате
    recent_orders = await repo.get_orders_with_filters(user_id=user_id, status=None, date_from=datetime.now().date() - timedelta(days=4), date_to=None)
    assert len(recent_orders) == 1
    assert recent_orders[0].id == 2 # Только formed_order
    
    
@pytest.mark.asyncio
async def test_get_full_order_details(db_session):
    """Тестирует, что get_full_order_details возвращает правильную доменную модель."""
    repo = SqlAlchemyDatabaseRepo(db_session)
    # Arrange
    user = User(id=1, login="details_user", password_hash="hash")
    service = Service(id=1, title="Test S1", price=100, impact_level=2, assessment_type=ServiceAssessmentType.NETWORK_SCAN, short_description="", description="")
    order = Order(id=1, created_by=user.id, status=OrderStatus.FORMED, created_at=datetime.now())
    assoc = OrdersServices(order_id=order.id, service_id=service.id, price_at_order_time=99, protection_level=ProtectionLevel.BASIC)
    db_session.add_all([user, service, order, assoc])
    await db_session.commit()
    
    # Act
    details = await repo.get_full_order_details(order.id)
    
    # Assert
    assert isinstance(details, OrderDetails)
    assert details.creator_login == "details_user"
    assert len(details.services) == 1
    service_in_order = details.services[0]
    assert isinstance(service_in_order, domains.ServiceInOrder)
    assert service_in_order.service.title == "Test S1"
    assert service_in_order.protection_level == ProtectionLevel.BASIC