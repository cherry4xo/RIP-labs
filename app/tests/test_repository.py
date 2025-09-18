import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from decimal import Decimal

from app.models import (
    Base, Service, Order, OrdersServices, User,
    OrderStatus, ServiceStatus, ServiceAssessmentType
)
from app.repository import SqlAlchemyDatabaseRepo


ASYNC_SQLITE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(ASYNC_SQLITE_URL)
AsyncSessionFactory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncSession:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionFactory() as session:
        yield session
        await session.rollback()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_get_services(db_session: AsyncSession):
    service1 = Service(title="Web Development", price=Decimal("100"), assessment_type=ServiceAssessmentType.WEB_APP_PENTEST)
    service2 = Service(title="Mobile App", price=Decimal("200"), assessment_type=ServiceAssessmentType.WEB_APP_PENTEST)
    service3 = Service(title="Old Service", price=Decimal("50"), assessment_type=ServiceAssessmentType.NETWORK_SCAN, status=ServiceStatus.DELETED)
    db_session.add_all([service1, service2, service3])
    await db_session.commit()
    repo = SqlAlchemyDatabaseRepo(db_session)

    all_active_services = await repo.get_services()
    assert len(all_active_services) == 2
    assert {s.title for s in all_active_services} == {"Web Development", "Mobile App"}

    found_services = await repo.get_services(query="Web")
    assert len(found_services) == 1
    assert found_services[0].title == "Web Development"


@pytest.mark.asyncio
async def test_get_service_by_id(db_session: AsyncSession):
    service = Service(id=10, title="SEO", price=Decimal("150"), assessment_type=ServiceAssessmentType.NETWORK_SCAN)
    db_session.add(service)
    await db_session.commit()
    repo = SqlAlchemyDatabaseRepo(db_session)

    found_service = await repo.get_service_by_id(service_id=10)
    not_found_service = await repo.get_service_by_id(service_id=99)

    assert found_service is not None
    assert found_service.id == 10
    assert found_service.title == "SEO"
    assert not_found_service is None


@pytest.mark.asyncio
async def test_get_order_details(db_session: AsyncSession):
    user = User(id=1, login="test")
    order = Order(id=5, status=OrderStatus.COMPLETED, created_at=datetime.now(), created_by=user.id)
    service1 = Service(title="Service A", price=Decimal("100.00"), assessment_type=ServiceAssessmentType.WEB_APP_PENTEST)
    service2 = Service(title="Service B", price=Decimal("200.00"), assessment_type=ServiceAssessmentType.NETWORK_SCAN)
    db_session.add_all([user, order, service1, service2])
    await db_session.flush()

    assoc1 = OrdersServices(order_id=order.id, service_id=service1.id, price_at_order_time=Decimal("95.00"))
    assoc2 = OrdersServices(order_id=order.id, service_id=service2.id, price_at_order_time=Decimal("210.50"))
    db_session.add_all([assoc1, assoc2])
    await db_session.commit()
    repo = SqlAlchemyDatabaseRepo(db_session)
    
    order_details = await repo.get_order_details(order_id=5)
    
    assert order_details is not None
    assert order_details.id == 5
    assert len(order_details.services) == 2
    assert order_details.total_price == float(Decimal("95.00") + Decimal("210.50")) # 305.50
    assert order_details.status == "completed"


@pytest.mark.asyncio
async def test_get_draft_order_by_user_id(db_session: AsyncSession):
    user1 = User(id=1, login="user_with_draft")
    user2 = User(id=2, login="user_without_draft")
    draft_order = Order(created_by=user1.id, status=OrderStatus.DRAFT, created_at=datetime.now())
    completed_order = Order(created_by=user2.id, status=OrderStatus.COMPLETED, created_at=datetime.now())
    db_session.add_all([user1, user2, draft_order, completed_order])
    await db_session.commit()
    repo = SqlAlchemyDatabaseRepo(db_session)

    found_order = await repo.get_draft_order_by_user_id(user_id=1)
    not_found_order = await repo.get_draft_order_by_user_id(user_id=2)

    assert found_order is not None
    assert found_order.id == draft_order.id
    assert not_found_order is None


@pytest.mark.asyncio
async def test_create_and_add_service_to_order(db_session: AsyncSession):
    user = User(id=1, login="test")
    service = Service(title="Test Service", price=Decimal("99.99"), assessment_type=ServiceAssessmentType.INFRASTRUCTURE_AUDIT)
    db_session.add_all([user, service])
    await db_session.commit()
    repo = SqlAlchemyDatabaseRepo(db_session)

    new_draft_order = await repo.create_draft_order(user_id=user.id)
    await db_session.commit()

    assert new_draft_order is not None
    assert new_draft_order.status == "draft"

    await repo.add_service_to_order(
        order_id=new_draft_order.id,
        service_id=service.id,
        price=service.price
    )
    await db_session.commit()

    stmt = select(OrdersServices).where(OrdersServices.order_id == new_draft_order.id)
    assoc = await db_session.scalar(stmt)
    assert assoc is not None
    assert assoc.service_id == service.id
    assert assoc.price_at_order_time == service.price


@pytest.mark.asyncio
async def test_logically_delete_order(db_session: AsyncSession):
    user = User(id=1, login="test")
    order = Order(id=1, created_by=user.id, status=OrderStatus.DRAFT, created_at=datetime.now())
    db_session.add_all([user, order])
    await db_session.commit()
    repo = SqlAlchemyDatabaseRepo(db_session)

    await repo.logically_delete_order(order_id=order.id)
    await db_session.commit()

    await db_session.refresh(order)

    assert order.status == OrderStatus.DELETED


@pytest.mark.asyncio
async def test_get_cart_item_count(db_session: AsyncSession):
    user1 = User(id=1, login="user1")
    user2 = User(id=2, login="user2")
    order = Order(created_by=user1.id, status=OrderStatus.DRAFT, created_at=datetime.now())
    service1 = Service(title="S1", price=1, assessment_type=ServiceAssessmentType.NETWORK_SCAN)
    service2 = Service(title="S2", price=2, assessment_type=ServiceAssessmentType.NETWORK_SCAN)
    db_session.add_all([user1, user2, order, service1, service2])
    await db_session.flush()
    assoc1 = OrdersServices(order_id=order.id, service_id=service1.id, price_at_order_time=1)
    assoc2 = OrdersServices(order_id=order.id, service_id=service2.id, price_at_order_time=2)
    db_session.add_all([assoc1, assoc2])
    await db_session.commit()
    repo = SqlAlchemyDatabaseRepo(db_session)

    count_user1 = await repo.get_cart_item_count(user_id=1)
    count_user2 = await repo.get_cart_item_count(user_id=2)

    assert count_user1 == 2
    assert count_user2 == 0