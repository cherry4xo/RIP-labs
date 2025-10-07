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

    async def get_vulnerability_assessment_by_id(self, assessment_id: int):
        service_orm = self.services.get(assessment_id)
        return domains.VulnerabilityAssessment.model_validate(service_orm) if service_orm else None

    async def get_vulnerability_assessments_with_filters(self, title: Optional[str], assessment_type: Optional[str]):
        return [domains.VulnerabilityAssessment.model_validate(s) for s in self.services.values()]

    async def create_vulnerability_assessment(self, assessment_data: domains.VulnerabilityAssessmentCreate):
        new_id = self._next_id()
        assessment = models.VulnerabilityAssessment(id=new_id, **assessment_data.model_dump())
        self.services[new_id] = assessment
        return domains.VulnerabilityAssessment.model_validate(assessment)

    async def update_vulnerability_assessment(self, assessment_id: int, assessment_data: domains.VulnerabilityAssessmentUpdatePartial):
        if assessment_id in self.services:
            update_data = assessment_data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(self.services[assessment_id], key, value)
            return domains.VulnerabilityAssessment.model_validate(self.services[assessment_id])
        return None

    async def delete_vulnerability_assessment(self, assessment_id: int) -> bool:
        if assessment_id in self.services:
            del self.services[assessment_id]
            return True
        return False

    async def get_draft_report_by_user_id(self, user_id: int) -> Optional[domains.AssessmentReportDetails]:
        """Находит ORM-модель отчета и конвертирует ее в Pydantic-модель."""
        for report_orm in self.orders.values():
            if report_orm.created_by == user_id and report_orm.status == models.ReportStatus.DRAFT:
                return await self.get_full_report_details(report_orm.id)
        return None

    async def create_draft_report(self, user_id: int) -> domains.AssessmentReportDetails:
        """Создает ORM-модель и сразу конвертирует ее в Pydantic-модель."""
        new_id = self._next_id()
        if not self.users.get(user_id):
            self.users[user_id] = models.User(id=user_id, login=f"user{user_id}")
            
        report = models.AssessmentReport(id=new_id, created_by=user_id, status=models.ReportStatus.DRAFT, created_at=datetime.now())
        self.orders[new_id] = report
        return await self.get_full_report_details(new_id)

    async def add_assessment_to_report(self, report_id: int, assessment_id: int, price: Decimal):
        self.associations.append(models.AssessmentComponents(
            report_id=report_id, 
            vulnerability_id=assessment_id, 
            price_at_order_time=price,
            protection_level=models.ProtectionLevel.NONE
        ))

    async def get_component(self, report_id: int, assessment_id: int):
        for assoc in self.associations:
            if assoc.report_id == report_id and assoc.vulnerability_id == assessment_id:
                return assoc
        return None

    async def delete_assessment_from_report(self, report_id: int, assessment_id: int) -> bool:
        initial_len = len(self.associations)
        self.associations = [a for a in self.associations if not (a.report_id == report_id and a.vulnerability_id == assessment_id)]
        return len(self.associations) < initial_len

    async def get_reports_with_filters(self, user_id: int, status: Optional[str], date_from: Optional[date], date_to: Optional[date]):
        return []

    async def get_full_report_details(self, report_id: int) -> Optional[domains.AssessmentReportDetails]:
        """
        Главный метод-конвертер. Собирает ORM-объекты и преобразует их 
        в доменную модель `AssessmentReportDetails`, как это делает настоящий репозиторий.
        """
        report_orm = self.orders.get(report_id)
        if not report_orm: 
            return None
        
        creator_orm = self.users.get(report_orm.created_by)
        moderator_orm = self.users.get(report_orm.moderated_by) if report_orm.moderated_by else None
        
        report_associations = [a for a in self.associations if a.report_id == report_id]
        
        components_in_report = []
        for assoc in report_associations:
            assessment_orm = self.services.get(assoc.vulnerability_id)
            if assessment_orm:
                components_in_report.append(domains.AssessmentComponent(
                    vulnerability_assessment=domains.VulnerabilityAssessment.model_validate(assessment_orm),
                    protection_level=assoc.protection_level,
                    comment=assoc.comment,
                    price_at_order_time=assoc.price_at_order_time
                ))
        
        return domains.AssessmentReportDetails(
            id=report_orm.id,
            status=report_orm.status,
            created_at=report_orm.created_at,
            created_by=report_orm.created_by,
            creator_login=creator_orm.login if creator_orm else "unknown",
            moderator_login=moderator_orm.login if moderator_orm else None,
            formation_date=report_orm.formation_date,
            completion_date=report_orm.completion_date,
            target_system_info=report_orm.target_system_info,
            risk_score=report_orm.risk_score,
            components=components_in_report
        )

    async def update_report(self, report_id: int, **kwargs):
        if report_id in self.orders:
            for key, value in kwargs.items():
                setattr(self.orders[report_id], key, value)

    async def update_component(self, report_id: int, assessment_id: int, **kwargs):
        assoc = await self.get_component(report_id, assessment_id)
        if assoc:
            for key, value in kwargs.items():
                setattr(assoc, key, value)

    async def get_basket_item_count(self, user_id: int) -> int:
        report_details = await self.get_draft_report_by_user_id(user_id)
        if not report_details: return 0
        return len(report_details.components)

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
    def _create_valid_service(self, **kwargs) -> models.VulnerabilityAssessment:
        defaults = {
            "title": "Default Service",
            "short_description": "sd",
            "description": "d",
            "price": Decimal("100"),
            "impact_level": 1,
            "assessment_type": models.VulnerabilityAssessmentType.NETWORK_SCAN,
            "status": models.AssessmentStatus.AVAILABLE,
        }
        defaults.update(kwargs)
        return models.VulnerabilityAssessment(**defaults)

    async def test_add_service_to_cart_creates_new_order(self):
        repo = InMemoryRepository()
        user_id = 1
        service_id = repo._next_id()
        repo.services[service_id] = self._create_valid_service(id=service_id)

        cart = await order_use_cases.add_assessment_to_basket(repo, user_id, service_id)

        assert len(repo.orders) == 1
        new_order_orm = list(repo.orders.values())[0]
        assert new_order_orm.created_by == user_id
        assert new_order_orm.status == models.ReportStatus.DRAFT
        
        assert len(repo.associations) == 1
        assert repo.associations[0].report_id == new_order_orm.id
        assert repo.associations[0].vulnerability_id == service_id
        
        assert isinstance(cart, domains.AssessmentReportDetails)
        assert len(cart.components) == 1

    async def test_form_order_success(self):
        repo = InMemoryRepository()
        user_id = 1
        service1_id = repo._next_id()
        repo.services[service1_id] = self._create_valid_service(id=service1_id, title="Crit Service", impact_level=3)
        
        draft_order = await repo.create_draft_report(user_id)
        await repo.add_assessment_to_report(draft_order.id, service1_id, Decimal("100.00"))

        form_data = domains.AssessmentReportFormPayload(
            target_system_info="test.com",
            components=[
                domains.AssessmentReportFormComponentPayload(assessment_id=service1_id, protection_level=domains.ProtectionLevel.BASIC, comment=""),
            ]
        )
        
        await order_use_cases.form_report(repo, draft_order.id, user_id, form_data)

        formed_order = repo.orders[draft_order.id]
        assert formed_order.status == models.ReportStatus.FORMED
        assert formed_order.target_system_info == "test.com"
        assert formed_order.risk_score is None

    async def test_complete_order_calculates_risk_success(self):
        repo = InMemoryRepository()
        user_id = 1
        moderator_id = 99
        repo.users[user_id] = models.User(id=user_id, login=f"user{user_id}")
        repo.users[moderator_id] = models.User(id=moderator_id, login=f"mod{moderator_id}")
        
        order_id = repo._next_id()
        order = models.AssessmentReport(id=order_id, created_by=user_id, created_at=datetime.now(), status=models.ReportStatus.FORMED)
        repo.orders[order_id] = order
        
        service1_id = repo._next_id()
        repo.services[service1_id] = self._create_valid_service(id=service1_id, impact_level=3)
        service2_id = repo._next_id()
        repo.services[service2_id] = self._create_valid_service(id=service2_id, impact_level=2)
        
        repo.associations.append(models.AssessmentComponents(
            report_id=order_id, vulnerability_id=service1_id, 
            protection_level=models.ProtectionLevel.BASIC, 
            price_at_order_time=Decimal("100")
        ))
        repo.associations.append(models.AssessmentComponents(
            report_id=order_id, vulnerability_id=service2_id, 
            protection_level=models.ProtectionLevel.FULL,
            price_at_order_time=Decimal("200")
        ))

        await order_use_cases.complete_report(repo, order_id, moderator_id)

        completed_order = repo.orders[order_id]
        assert completed_order.status == models.ReportStatus.COMPLETED
        assert completed_order.moderated_by == moderator_id
        assert completed_order.risk_score == 6

    async def test_complete_order_fails_if_not_formed(self):
        repo = InMemoryRepository()
        user_id = 1
        moderator_id = 2
        draft_order = await repo.create_draft_report(user_id)

        with pytest.raises(interfaces.ReportNotFoundError, match="A 'formed' report is required"):
            await order_use_cases.complete_report(repo, draft_order.id, moderator_id)

    async def test_delete_draft_order_success(self):
        repo = InMemoryRepository()
        user_id = 1
        draft_order = await repo.create_draft_report(user_id)

        await order_use_cases.delete_draft_report(repo, draft_order.id, user_id)

        deleted_order = repo.orders[draft_order.id]
        assert deleted_order.status == models.ReportStatus.DELETED
        
    async def test_delete_draft_order_fails_if_wrong_user(self):
        repo = InMemoryRepository()
        owner_user_id = 1
        other_user_id = 2
        draft_order = await repo.create_draft_report(owner_user_id)
        
        with pytest.raises(interfaces.ReportNotFoundError):
            await order_use_cases.delete_draft_report(repo, draft_order.id, other_user_id)


class TestServiceUseCases:
    def _create_valid_service(self, **kwargs) -> models.VulnerabilityAssessment:
        defaults = {
            "title": "Default Service",
            "short_description": "sd",
            "description": "d",
            "price": Decimal("100"),
            "impact_level": 1,
            "assessment_type": models.VulnerabilityAssessmentType.NETWORK_SCAN,
            "status": models.AssessmentStatus.AVAILABLE,
        }
        defaults.update(kwargs)
        return models.VulnerabilityAssessment(**defaults)

    async def test_delete_service_with_image(self):
        db_repo = InMemoryRepository()
        file_storage = InMemoryFileStorage()
        
        service_id = db_repo._next_id()
        image_url = "http://fake-storage.com/image.png"
        
        db_repo.services[service_id] = self._create_valid_service(id=service_id, image_url=image_url)
        file_storage.files.add("image.png")

        await service_use_cases.delete_vulnerability_assessment(db_repo, file_storage, service_id)

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
        
        await service_use_cases.update_vulnerability_assessment_image(db_repo, file_storage, service_id, mock_image)

        assert "old_image.png" not in file_storage.files
        assert len(file_storage.files) == 1
        
        updated_service = await db_repo.get_vulnerability_assessment_by_id(service_id)
        assert ".jpg" in updated_service.image_url
