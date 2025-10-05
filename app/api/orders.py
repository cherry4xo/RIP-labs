# app/api/orders.py

from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app import domains
from app import interfaces
from app.use_cases import order as order_use_cases
from app.auth.dependencies import CurrentUserDep, ModeratorDep
from app.core.database import DBSessionDep
from app.repository import SqlAlchemyDatabaseRepo
from app.interfaces import ReportNotFoundError, VulnerabilityAssessmentNotFoundError

router = APIRouter(tags=["Orders & Cart"])

@router.get("/basket/info", response_model=domains.AssessmentBasketInfo)
async def get_basket_info_endpoint(user: CurrentUserDep, db: DBSessionDep):
    """Получение ID и количества оценок уязвимости в корзине текущего пользователя."""
    repo = SqlAlchemyDatabaseRepo(db)
    try:
        basket_info = await order_use_cases.get_basket_info(repo, user.id)
        return basket_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/basket/assessments", response_model=domains.AssessmentReportDetails)
async def add_to_basket(item: domains.AssessmentBasketItemAdd, user: CurrentUserDep, db: DBSessionDep):
    """Добавление оценки уязвимости в корзину (создает корзину, если ее нет)."""
    repo = SqlAlchemyDatabaseRepo(db)
    try:
        updated_basket = await order_use_cases.add_assessment_to_basket(repo, user.id, item.assessment_id)
        await db.commit()
        return updated_basket
    except VulnerabilityAssessmentNotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.delete("/basket/assessments/{assessment_id}", response_model=domains.AssessmentReportDetails)
async def remove_from_basket(assessment_id: int, user: CurrentUserDep, db: DBSessionDep):
    """Удаление оценки уязвимости из корзины."""
    repo = SqlAlchemyDatabaseRepo(db)
    try:
        updated_basket = await order_use_cases.remove_assessment_from_basket(repo, user.id, assessment_id)
        await db.commit()
        return updated_basket
    except (ReportNotFoundError, VulnerabilityAssessmentNotFoundError) as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.put("/basket/assessments/{assessment_id}", response_model=domains.AssessmentReportDetails)
async def update_basket_item(assessment_id: int, item_data: domains.AssessmentBasketItemUpdate, user: CurrentUserDep, db: DBSessionDep):
    """Изменение полей м-м (уровня защиты, комментария) для оценки уязвимости в корзине."""
    repo = SqlAlchemyDatabaseRepo(db)
    try:
        updated_basket = await order_use_cases.update_basket_item_details(repo, user.id, assessment_id, item_data)
        await db.commit()
        return updated_basket
    except ReportNotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/reports", response_model=List[domains.AssessmentReportSummary])
async def get_reports_endpoint(
    user: CurrentUserDep,
    db: DBSessionDep,
    status: Optional[domains.ReportStatus] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
):
    """Получение списка оформленных отчетов с фильтрацией."""
    repo = SqlAlchemyDatabaseRepo(db)
    try:
        reports = await order_use_cases.get_reports_list(
            repo, user.id, status.value if status else None, date_from, date_to
        )
        return reports
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/{report_id}", response_model=domains.AssessmentReportDetails)
async def get_report_endpoint(report_id: int, user: CurrentUserDep, db: DBSessionDep):
    """Получение детальной информации об отчете."""
    repo = SqlAlchemyDatabaseRepo(db)
    try:
        report = await order_use_cases.get_report_details(repo, report_id, user.login, user.is_moderator)
        return report
    except ReportNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/reports/{report_id}", response_model=domains.AssessmentReportDetails)
async def update_report(report_id: int, report_data: domains.AssessmentReportUpdate, user: CurrentUserDep, db: DBSessionDep):
    """Изменение полей отчета (например, целевой системы)."""
    repo = SqlAlchemyDatabaseRepo(db)
    try:
        await order_use_cases.update_report_info(repo, report_id, user.id, report_data)
        await db.commit()
        return await repo.get_full_report_details(report_id)
    except ReportNotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(report_id: int, user: CurrentUserDep, db: DBSessionDep):
    """Удаление отчета-черновика (логическое)."""
    repo = SqlAlchemyDatabaseRepo(db)
    try:
        await order_use_cases.delete_draft_report(repo, report_id, user.id)
        await db.commit()
    except ReportNotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(e))
    return None

@router.put("/reports/{report_id}/form", response_model=domains.AssessmentReportDetails)
async def form_report(report_id: int, payload: domains.AssessmentReportFormPayload, user: CurrentUserDep, db: DBSessionDep):
    """Сформировать отчет (создателем)."""
    repo = SqlAlchemyDatabaseRepo(db)
    try:
        await order_use_cases.form_report(repo, report_id, user.id, payload)
        await db.commit()
        return await repo.get_full_report_details(report_id)
    except ReportNotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/reports/{report_id}/complete", response_model=domains.AssessmentReportDetails, dependencies=[ModeratorDep])
async def complete_report(report_id: int, moderator: CurrentUserDep, db: DBSessionDep):
    """Завершить отчет (модератором)."""
    repo = SqlAlchemyDatabaseRepo(db)
    try:
        await order_use_cases.complete_report(repo, report_id, moderator.id)
        await db.commit()
        return await repo.get_full_report_details(report_id)
    except ReportNotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/reports/{report_id}/cancel", response_model=domains.AssessmentReportDetails, dependencies=[ModeratorDep])
async def cancel_report(report_id: int, moderator: CurrentUserDep, db: DBSessionDep):
    """Отклонить отчет (модератором)."""
    repo = SqlAlchemyDatabaseRepo(db)
    try:
        await order_use_cases.cancel_report(repo, report_id, moderator.id)
        await db.commit()
        return await repo.get_full_report_details(report_id)
    except ReportNotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(e))
