import abc
from typing import List, Optional, IO
from decimal import Decimal
from datetime import date

from app import domains, models


class ServiceUnavailableError(Exception):
    pass

class ReportNotFoundError(Exception):
    pass

class ReportBadRequest(Exception):
    pass

class VulnerabilityAssessmentNotFoundError(Exception):
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

    # Vulnerability Assessment methods
    @abc.abstractmethod
    async def get_vulnerability_assessment_by_id(self, assessment_id: int) -> Optional[models.VulnerabilityAssessment]: ...
    @abc.abstractmethod
    async def get_vulnerability_assessments_with_filters(self, title: Optional[str], assessment_type: Optional[str]) -> List[models.VulnerabilityAssessment]: ...
    @abc.abstractmethod
    async def create_vulnerability_assessment(self, assessment_data: domains.VulnerabilityAssessmentCreate) -> models.VulnerabilityAssessment: ...
    @abc.abstractmethod
    async def update_vulnerability_assessment(self, assessment_id: int, assessment_data: domains.VulnerabilityAssessmentUpdatePartial) -> Optional[models.VulnerabilityAssessment]: ...
    @abc.abstractmethod
    async def delete_vulnerability_assessment(self, assessment_id: int) -> bool: ...

    # Assessment Report & Basket methods
    @abc.abstractmethod
    async def get_draft_report_by_user_id(self, user_id: int) -> Optional[domains.AssessmentReportDetails]: ...
    @abc.abstractmethod
    async def create_draft_report(self, user_id: int) -> domains.AssessmentReportDetails: ...
    @abc.abstractmethod
    async def add_assessment_to_report(self, report_id: int, assessment_id: int, price: Decimal) -> None: ...
    @abc.abstractmethod
    async def get_component(self, report_id: int, assessment_id: int) -> Optional[models.AssessmentComponents]: ...
    @abc.abstractmethod
    async def delete_assessment_from_report(self, report_id: int, assessment_id: int) -> bool: ...
    @abc.abstractmethod
    async def get_reports_with_filters(self, user_id: int, status: Optional[str], date_from: Optional[date], date_to: Optional[date]) -> List: ...
    @abc.abstractmethod
    async def get_full_report_details(self, report_id: int) -> Optional[models.AssessmentReport]: ...
    @abc.abstractmethod
    async def update_report(self, report_id: int, **kwargs) -> None: ...
    @abc.abstractmethod
    async def update_component(self, report_id: int, assessment_id: int, **kwargs) -> None: ...
    @abc.abstractmethod
    async def get_basket_item_count(self, user_id: int) -> int: ...
