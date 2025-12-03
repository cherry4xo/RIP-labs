# app/use_cases/order.py

from datetime import datetime, timezone, date
from typing import List, Optional
import httpx
import os

from app.interfaces import AbstractDatabaseRepo, AbstractFileStorage, VulnerabilityAssessmentNotFoundError, ReportNotFoundError, ReportBadRequest
from app import domains, models


ASYNC_SERVICE_URL = os.getenv("ASYNC_SERVICE_URL", "http://localhost:8082")


async def get_basket_info(repo: AbstractDatabaseRepo, user_id: int) -> domains.AssessmentBasketInfo:
    """
    Get basket information for a user.
    Returns AssessmentBasketInfo with report_id and item_count.
    """
    draft_report = await repo.get_draft_report_by_user_id(user_id)
    if not draft_report:
        return domains.AssessmentBasketInfo(report_id=-1, item_count=0)
    count = len(draft_report.components)
    return domains.AssessmentBasketInfo(report_id=draft_report.id, item_count=count)


async def get_draft_report_status_info(repo: AbstractDatabaseRepo, user_id: int) -> domains.DraftReportStatusInfo:
    """
    Get draft report status information for a user.
    Returns DraftReportStatusInfo with is_active status and item_count.
    """
    draft_report = await repo.get_draft_report_by_user_id(user_id)
    if not draft_report:
        return domains.DraftReportStatusInfo(is_active=False, item_count=0)
    count = len(draft_report.components)
    return domains.DraftReportStatusInfo(is_active=True, item_count=count)


async def get_reports_list(
    repo: AbstractDatabaseRepo,
    user_id: int,
    status: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None
) -> List[domains.AssessmentReportSummary]:
    """
    Get list of reports for a user with optional filtering.
    """
    return await repo.get_reports_with_filters(user_id, status, date_from, date_to)


async def get_report_details(
    repo: AbstractDatabaseRepo,
    report_id: int,
    user_login: str,
    is_moderator: bool
) -> domains.AssessmentReportDetails:
    """
    Get details of a specific report.
    Validates user access permissions.
    """
    report = await repo.get_full_report_details(report_id)
    if not report or (report.creator_login != user_login and not is_moderator):
        raise ReportNotFoundError("Report not found")
    return report


async def add_assessment_to_basket(repo: AbstractDatabaseRepo, user_id: int, assessment_id: int) -> domains.AssessmentReportDetails:
    assessment = await repo.get_vulnerability_assessment_by_id(assessment_id)
    if not assessment:
        raise VulnerabilityAssessmentNotFoundError("Vulnerability assessment not found")
    
    draft_report = await repo.get_draft_report_by_user_id(user_id)
    if not draft_report:
        draft_report = await repo.create_draft_report(user_id)
    
    is_present = any(item.vulnerability_assessment.id == assessment_id for item in draft_report.components)
    
    if not is_present:
        await repo.add_assessment_to_report(draft_report.id, assessment_id, assessment.price)
        return await repo.get_full_report_details(draft_report.id)

    return draft_report


async def remove_assessment_from_basket(repo: AbstractDatabaseRepo, user_id: int, assessment_id: int) -> domains.AssessmentReportDetails:
    """
    Удаляет оценку уязвимости из корзины пользователя.
    Возвращает актуальное состояние корзины.
    """
    draft_report = await repo.get_draft_report_by_user_id(user_id)
    if not draft_report:
        raise ReportNotFoundError("Basket not found")
    
    deleted = await repo.delete_assessment_from_report(draft_report.id, assessment_id)
    if not deleted:
        raise VulnerabilityAssessmentNotFoundError("Vulnerability assessment not found in basket")
    
    return await repo.get_full_report_details(draft_report.id)


async def update_basket_item_details(repo: AbstractDatabaseRepo, user_id: int, assessment_id: int, item_data: domains.AssessmentBasketItemUpdate) -> domains.AssessmentReportDetails:
    """
    Обновляет детали (уровень защиты, комментарий) для оценки уязвимости в корзине.
    Возвращает актуальное состояние корзины.
    """
    draft_report = await repo.get_draft_report_by_user_id(user_id)
    if not draft_report:
        raise ReportNotFoundError("Basket not found")
        
    await repo.update_component(draft_report.id, assessment_id, **item_data.model_dump())
    return await repo.get_full_report_details(draft_report.id)


async def form_report(repo: AbstractDatabaseRepo, report_id: int, user_id: int, payload: domains.AssessmentReportFormPayload):
    report = await repo.get_full_report_details(report_id)
    if not report or report.created_by != user_id or report.status != models.ReportStatus.DRAFT:
        raise ReportNotFoundError("Draft report not found for this user")

    # for item in payload.components:
    #     await repo.update_component(
    #         report_id=report.id,
    #         assessment_id=item.assessment_id,
    #         protection_level=item.protection_level,
    #         comment=item.comment
    #     )

    await repo.update_report(
        report_id=report.id,
        target_system_info=payload.target_system_info,
        status=models.ReportStatus.FORMED,
        formation_date=datetime.now()
    )

    # Вызываем асинхронный сервис для расчета risk_score
    await trigger_risk_calculation(report)


async def trigger_risk_calculation(report: domains.AssessmentReportDetails):
    """Отправка запроса в асинхронный Go-сервис для расчета risk_score."""
    components_data = []
    for component in report.components:
        components_data.append({
            "protection_level": component.protection_level.value,
            "impact_level": component.vulnerability_assessment.impact_level
        })

    payload = {
        "report_id": report.id,
        "components": components_data
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{ASYNC_SERVICE_URL}/calculate-risk",
                json=payload
            )
            if response.status_code == 202:
                print(f"Risk calculation triggered for report {report.id}")
            else:
                print(f"Failed to trigger risk calculation: {response.status_code}")
    except Exception as e:
        print(f"Error calling async service: {e}")
        # Не прерываем выполнение, даже если асинхронный сервис недоступен


async def complete_report(repo: AbstractDatabaseRepo, report_id: int, moderator_id: int):
    report_details = await repo.get_full_report_details(report_id)
    if not report_details or report_details.status != models.ReportStatus.FORMED:
        raise ReportBadRequest("A 'formed' report is required to complete")

    protection_to_likelihood = {"none": 3, "basic": 2, "full": 1}
    max_risk_score = 0
    
    for item in report_details.components:
        likelihood = protection_to_likelihood.get(item.protection_level.value, 3)
        impact = item.vulnerability_assessment.impact_level
        risk_score = likelihood * impact
        if risk_score > max_risk_score:
            max_risk_score = risk_score
    
    await repo.update_report(
        report_id=report_details.id,
        status=models.ReportStatus.COMPLETED,
        completion_date=datetime.now(),
        moderated_by=moderator_id,
        risk_score=max_risk_score
    )


async def cancel_report(repo: AbstractDatabaseRepo, report_id: int, moderator_id: int):
    report = await repo.get_full_report_details(report_id)
    if not report or report.status != models.ReportStatus.FORMED:
        raise ReportNotFoundError("A 'formed' report is required to cancel")

    await repo.update_report(
        report_id=report.id,
        status=models.ReportStatus.CANCELLED,
        completion_date=datetime.now(timezone.utc),
        moderated_by=moderator_id
    )


async def delete_draft_report(repo: AbstractDatabaseRepo, report_id: int, user_id: int):
    report = await repo.get_full_report_details(report_id)
    if not report or report.created_by != user_id or report.status != models.ReportStatus.DRAFT:
        raise ReportNotFoundError("Draft report not found for this user")
    
    await repo.update_report(report_id=report.id, status=models.ReportStatus.DELETED)


async def update_report_info(repo: AbstractDatabaseRepo, report_id: int, user_id: int, report_data: domains.AssessmentReportUpdate):
    report = await repo.get_full_report_details(report_id)
    if not report or report.created_by != user_id:
        raise ReportNotFoundError("Report not found")

    await repo.update_report(report_id=report.id, target_system_info=report_data.target_system_info)


async def update_risk_score(repo: AbstractDatabaseRepo, report_id: int, risk_score: int):
    """Обновление risk_score заявки (вызывается асинхронным сервисом)."""
    report = await repo.get_full_report_details(report_id)
    if not report:
        raise ReportNotFoundError("Report not found")

    await repo.update_report(report_id=report.id, risk_score=risk_score)
