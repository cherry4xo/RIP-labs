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
    VulnerabilityAssessment, AssessmentReport, AssessmentComponents, User,
    ReportStatus, AssessmentStatus, VulnerabilityAssessmentType, ProtectionLevel
)
from app.repository import SqlAlchemyDatabaseRepo
from app.domains import AssessmentReportDetails, AssessmentReportSummary, UserCreate, UserRead, UserUpdate, VulnerabilityAssessmentCreate, VulnerabilityAssessmentUpdate


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
    service_data = VulnerabilityAssessmentCreate(
        title="Test Service", short_description="A test", description="A test service",
        price=Decimal("100.00"), impact_level=2, assessment_type=VulnerabilityAssessmentType.NETWORK_SCAN
    )
    created_service = await repo.create_vulnerability_assessment(assessment_data=service_data)
    await db_session.commit()
    assert created_service.id is not None
    assert created_service.title == "Test Service"

    found_service = await repo.get_vulnerability_assessment_by_id(assessment_id=created_service.id)
    assert found_service is not None
    assert found_service.title == "Test Service"

    update_data = VulnerabilityAssessmentUpdate(
        title="Updated Title", price=Decimal("150.00"), 
        description="Updated desc", impact_level=3, 
        assessment_type=VulnerabilityAssessmentType.WEB_APP_PENTEST, short_description="updated"
    )
    updated_service = await repo.update_vulnerability_assessment(created_service.id, assessment_data=update_data)
    await db_session.commit()
    assert updated_service.title == "Updated Title"
    assert updated_service.price == Decimal("150.00")

    deleted = await repo.delete_vulnerability_assessment(assessment_id=created_service.id)
    await db_session.commit()
    assert deleted is True
    not_found_service = await repo.get_vulnerability_assessment_by_id(assessment_id=created_service.id)
    assert not_found_service is None


@pytest.mark.asyncio
async def test_get_services_with_filters(db_session):
    repo = SqlAlchemyDatabaseRepo(db_session)

    s1 = VulnerabilityAssessment(title="Web Scan", price=100, impact_level=1, assessment_type=VulnerabilityAssessmentType.NETWORK_SCAN, short_description="", description="")
    s2 = VulnerabilityAssessment(title="Web Pentest", price=200, impact_level=2, assessment_type=VulnerabilityAssessmentType.WEB_APP_PENTEST, short_description="", description="")
    s3 = VulnerabilityAssessment(title="Mobile Scan", price=300, impact_level=3, assessment_type=VulnerabilityAssessmentType.NETWORK_SCAN, short_description="", description="")
    s4 = VulnerabilityAssessment(title="Deleted Service", price=50, status=AssessmentStatus.DELETED, impact_level=1, assessment_type=VulnerabilityAssessmentType.NETWORK_SCAN, short_description="", description="")
    db_session.add_all([s1, s2, s3, s4])
    await db_session.commit()

    all_services = await repo.get_vulnerability_assessments_with_filters(title=None, assessment_type=None)
    assert len(all_services) == 3
    
    web_services = await repo.get_vulnerability_assessments_with_filters(title="Web", assessment_type=None)
    assert len(web_services) == 2
    assert {s.title for s in web_services} == {"Web Scan", "Web Pentest"}

    scan_services = await repo.get_vulnerability_assessments_with_filters(title=None, assessment_type=VulnerabilityAssessmentType.NETWORK_SCAN)
    assert len(scan_services) == 2
    assert {s.title for s in scan_services} == {"Web Scan", "Mobile Scan"}


@pytest_asyncio.fixture
async def setup_orders(db_session):
    """Фикстура для создания набора пользователей и отчетов для тестов."""
    user1 = User(id=1, login="user1", password_hash="hash")
    user2 = User(id=2, login="user2", password_hash="hash")
    
    # Отчеты для user1
    draft_order = AssessmentReport(id=1, created_by=1, status=ReportStatus.DRAFT, created_at=datetime.now())
    formed_order = AssessmentReport(id=2, created_by=1, status=ReportStatus.FORMED, created_at=datetime.now(), formation_date=datetime.now() - timedelta(days=2))
    completed_order = AssessmentReport(id=3, created_by=1, status=ReportStatus.COMPLETED, created_at=datetime.now(), formation_date=datetime.now() - timedelta(days=5))
    deleted_order = AssessmentReport(id=4, created_by=1, status=ReportStatus.DELETED, created_at=datetime.now())

    # Отчет для user2
    other_user_order = AssessmentReport(id=5, created_by=2, status=ReportStatus.FORMED, created_at=datetime.now(), formation_date=datetime.now() - timedelta(days=3))
    
    db_session.add_all([user1, user2, draft_order, formed_order, completed_order, deleted_order, other_user_order])
    await db_session.commit()
    yield


@pytest.mark.asyncio
async def test_cart_creation_and_manipulation(db_session, setup_orders):
    """Тестирует создание корзины, добавление/удаление из нее."""
    repo = SqlAlchemyDatabaseRepo(db_session)
    user_id_with_draft = 1
    
    service = VulnerabilityAssessment(id=10, title="Test S1", price=100, impact_level=1, assessment_type=VulnerabilityAssessmentType.NETWORK_SCAN, short_description="", description="")
    db_session.add(service)
    await db_session.commit()

    # 1. Проверяем, что у юзера есть черновик (из фикстуры)
    draft1 = await repo.get_draft_report_by_user_id(user_id_with_draft)
    assert draft1 is not None
    
    # 2. Добавляем оценку уязвимости в существующий черновик
    await repo.add_assessment_to_report(draft1.id, service.id, service.price)
    await db_session.commit()
    count1 = await repo.get_basket_item_count(user_id_with_draft)
    assert count1 == 1

    # 3. Удаляем оценку уязвимости из черновика
    deleted = await repo.delete_assessment_from_report(draft1.id, service.id)
    await db_session.commit()
    assert deleted is True
    count1_after_delete = await repo.get_basket_item_count(user_id_with_draft)
    assert count1_after_delete == 0


@pytest.mark.asyncio
async def test_get_orders_with_filters(db_session, setup_orders): # Убедитесь, что фикстура вызывается
    """Тестирует фильтрацию списка оформленных отчетов."""
    repo = SqlAlchemyDatabaseRepo(db_session)
    user_id = 1
    
    # 1. Получаем все (не должно быть draft и deleted)
    all_orders = await repo.get_reports_with_filters(user_id=user_id, status=None, date_from=None, date_to=None)
    assert len(all_orders) == 2
    assert {o.status for o in all_orders} == {models.ReportStatus.FORMED, models.ReportStatus.COMPLETED}
    assert all(isinstance(o, domains.AssessmentReportSummary) for o in all_orders)
    # Проверяем, что логин создателя был добавлен
    assert all_orders[0].creator_login == "user1"

    # 2. Фильтруем по статусу
    formed_orders = await repo.get_reports_with_filters(user_id=user_id, status=models.ReportStatus.FORMED, date_from=None, date_to=None)
    assert len(formed_orders) == 1
    assert formed_orders[0].status == models.ReportStatus.FORMED

    # 3. Фильтруем по дате
    recent_orders = await repo.get_reports_with_filters(user_id=user_id, status=None, date_from=datetime.now().date() - timedelta(days=4), date_to=None)
    assert len(recent_orders) == 1
    assert recent_orders[0].id == 2 # Только formed_order
    
    
@pytest.mark.asyncio
async def test_get_full_order_details(db_session):
    """Тестирует, что get_full_order_details возвращает правильную доменную модель."""
    repo = SqlAlchemyDatabaseRepo(db_session)
    # Arrange
    user = User(id=1, login="details_user", password_hash="hash")
    service = VulnerabilityAssessment(id=1, title="Test S1", price=100, impact_level=2, assessment_type=VulnerabilityAssessmentType.NETWORK_SCAN, short_description="", description="")
    order = AssessmentReport(id=1, created_by=user.id, status=ReportStatus.FORMED, created_at=datetime.now())
    assoc = AssessmentComponents(order_id=order.id, service_id=service.id, price_at_order_time=99, protection_level=ProtectionLevel.BASIC)
    db_session.add_all([user, service, order, assoc])
    await db_session.commit()
    
    # Act
    details = await repo.get_full_report_details(order.id)
    
    # Assert
    assert isinstance(details, AssessmentReportDetails)
    assert details.creator_login == "details_user"
    assert len(details.components) == 1
    service_in_order = details.components[0]
    assert isinstance(service_in_order, domains.AssessmentComponent)
    assert service_in_order.vulnerability_assessment.title == "Test S1"
    assert service_in_order.protection_level == ProtectionLevel.BASIC
