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
        user_orm = await self._session.get(models.User, user_id)
        return domains.UserRead.model_validate(user_orm) if user_orm else None

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

    # --- Vulnerability Assessment Methods ---
    async def get_vulnerability_assessment_by_id(self, assessment_id: int) -> Optional[domains.VulnerabilityAssessment]:
        assessment_orm = await self._session.get(models.VulnerabilityAssessment, assessment_id)
        return domains.VulnerabilityAssessment.model_validate(assessment_orm) if assessment_orm else None

    async def get_vulnerability_assessments_with_filters(self, title: Optional[str], assessment_type: Optional[str]) -> List[domains.VulnerabilityAssessment]:
        stmt = select(models.VulnerabilityAssessment).where(models.VulnerabilityAssessment.status != models.AssessmentStatus.DELETED).order_by(models.VulnerabilityAssessment.title)
        if title:
            stmt = stmt.where(models.VulnerabilityAssessment.title.ilike(f"%{title}%"))
        if assessment_type:
            stmt = stmt.where(models.VulnerabilityAssessment.assessment_type == assessment_type)
        result = await self._session.scalars(stmt)
        return [domains.VulnerabilityAssessment.model_validate(s) for s in result.all()]

    async def create_vulnerability_assessment(self, assessment_data: domains.VulnerabilityAssessmentCreate) -> domains.VulnerabilityAssessment:
        new_assessment_orm = models.VulnerabilityAssessment(**assessment_data.model_dump())
        self._session.add(new_assessment_orm)
        await self._session.flush()
        return domains.VulnerabilityAssessment.model_validate(new_assessment_orm)

    async def update_vulnerability_assessment(self, assessment_id: int, assessment_data: domains.VulnerabilityAssessmentUpdatePartial, image_url: Optional[str] = None) -> Optional[domains.VulnerabilityAssessment]:
        assessment_orm = await self._session.get(models.VulnerabilityAssessment, assessment_id)
        if not assessment_orm:
            return None
        
        for key, value in assessment_data.model_dump(exclude_unset=True).items():
            setattr(assessment_orm, key, value)
        
        if image_url is not None:
            assessment_orm.image_url = image_url

        await self._session.flush()
        return domains.VulnerabilityAssessment.model_validate(assessment_orm)

    async def delete_vulnerability_assessment(self, assessment_id: int) -> bool:
        assessment_orm = await self._session.get(models.VulnerabilityAssessment, assessment_id)
        if not assessment_orm:
            return False
        await self._session.delete(assessment_orm)
        await self._session.flush()
        return True

    # --- Assessment Report & Basket Methods ---
    async def get_draft_report_by_user_id(self, user_id: int) -> Optional[domains.AssessmentReportDetails]:
        stmt = select(models.AssessmentReport).where(
            models.AssessmentReport.created_by == user_id,
            models.AssessmentReport.status == models.ReportStatus.DRAFT
        )
        report_orm = await self._session.scalar(stmt)
        if not report_orm:
            return None
        return await self.get_full_report_details(report_orm.id)

    async def create_draft_report(self, user_id: int) -> domains.AssessmentReportDetails:
        new_report = models.AssessmentReport(created_by=user_id, created_at=datetime.now())
        self._session.add(new_report)
        await self._session.flush()
        return await self.get_full_report_details(new_report.id)

    async def add_assessment_to_report(self, report_id: int, assessment_id: int, price: Decimal) -> None:
        new_assoc = models.AssessmentComponents(
            order_id=report_id, service_id=assessment_id, price_at_order_time=price
        )
        self._session.add(new_assoc)
        await self._session.flush()

    async def get_component(self, report_id: int, assessment_id: int) -> Optional[models.AssessmentComponents]:
        stmt = select(models.AssessmentComponents).where(
            models.AssessmentComponents.order_id == report_id,
            models.AssessmentComponents.service_id == assessment_id
        )
        return await self._session.scalar(stmt)
    
    async def delete_assessment_from_report(self, report_id: int, assessment_id: int) -> bool:
        stmt = delete(models.AssessmentComponents).where(
            models.AssessmentComponents.order_id == report_id,
            models.AssessmentComponents.service_id == assessment_id
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0

    async def get_reports_with_filters(self, user_id: int, status: Optional[str], date_from: Optional[date], date_to: Optional[date]) -> List[domains.AssessmentReportSummary]:
        stmt = (
            select(models.AssessmentReport)
            .where(
                models.AssessmentReport.created_by == user_id,
                models.AssessmentReport.status.notin_([models.ReportStatus.DRAFT, models.ReportStatus.DELETED])
            )
            .options(selectinload(models.AssessmentReport.creator))
            .order_by(models.AssessmentReport.created_at.desc())
        )
        if status:
            stmt = stmt.where(models.AssessmentReport.status == status)
        if date_from:
            stmt = stmt.where(models.AssessmentReport.formation_date >= date_from)
        if date_to:
            stmt = stmt.where(models.AssessmentReport.formation_date <= date_to)
        
        result = await self._session.scalars(stmt)
        summaries = [
            domains.AssessmentReportSummary(
                id=report_orm.id,
                status=report_orm.status,
                formation_date=report_orm.formation_date,
                risk_score=report_orm.risk_score,
                creator_login=report_orm.creator.login
            )
            for report_orm in result.all()
        ]
        return summaries

    async def get_full_report_details(self, report_id: int) -> Optional[domains.AssessmentReportDetails]:
        stmt = (
            select(models.AssessmentReport)
            .where(models.AssessmentReport.id == report_id)
            .options(
                selectinload(models.AssessmentReport.component_associations).selectinload(models.AssessmentComponents.vulnerability_assessment),
                selectinload(models.AssessmentReport.creator),
                selectinload(models.AssessmentReport.moderator)
            )
        )
        report_orm = await self._session.scalar(stmt)
        if not report_orm or report_orm.status == models.ReportStatus.DELETED:
            return None
        
        components_in_report = [
            domains.AssessmentComponent(
                vulnerability_assessment=domains.VulnerabilityAssessment.model_validate(assoc.vulnerability_assessment),
                protection_level=assoc.protection_level,
                comment=assoc.comment,
                price_at_order_time=assoc.price_at_order_time
            ) for assoc in report_orm.component_associations
        ]

        details = domains.AssessmentReportDetails(
            id=report_orm.id,
            status=report_orm.status,
            created_at=report_orm.created_at,
            created_by=report_orm.created_by,
            creator_login=report_orm.creator.login,
            moderator_login=report_orm.moderator.login if report_orm.moderator else None,
            formation_date=report_orm.formation_date,
            completion_date=report_orm.completion_date,
            target_system_info=report_orm.target_system_info,
            risk_score=report_orm.risk_score,
            components=components_in_report
        )
        return details

    async def update_report(self, report_id: int, **kwargs) -> None:
        stmt = update(models.AssessmentReport).where(models.AssessmentReport.id == report_id).values(**kwargs)
        await self._session.execute(stmt)
        
    async def update_component(self, report_id: int, assessment_id: int, **kwargs) -> None:
        stmt = (
            update(models.AssessmentComponents)
            .where(models.AssessmentComponents.order_id == report_id, models.AssessmentComponents.service_id == assessment_id)
            .values(**kwargs)
        )
        await self._session.execute(stmt)

    async def get_basket_item_count(self, user_id: int) -> int:
        draft_report = await self.get_draft_report_by_user_id(user_id)
        if not draft_report:
            return 0
        stmt = select(func.count()).select_from(models.AssessmentComponents).where(
            models.AssessmentComponents.order_id == draft_report.id
        )
        return await self._session.scalar(stmt) or 0
