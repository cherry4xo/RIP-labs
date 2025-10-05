# app/api/services.py

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from app.auth.dependencies import ModeratorDep, CurrentUserDep
from app.core.database import DBSessionDep
from app.file_storage.minio_storage import FileStorageDep
from app.repository import SqlAlchemyDatabaseRepo
from app import domains, interfaces
from app.use_cases import service as service_use_cases

router = APIRouter(prefix="/services", tags=["Services"])


@router.get("/", response_model=List[domains.VulnerabilityAssessment])
async def get_vulnerability_assessments(
    db: DBSessionDep,
    title: Optional[str] = None,
    assessment_type: Optional[domains.VulnerabilityAssessmentType] = None
):
    """Получение списка оценок уязвимости с возможностью фильтрации."""
    repo = SqlAlchemyDatabaseRepo(db)
    try:
        assessments = await service_use_cases.get_vulnerability_assessments_list(repo, title, assessment_type.value if assessment_type else None)
        return assessments
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{assessment_id}", response_model=domains.VulnerabilityAssessment)
async def get_vulnerability_assessment(assessment_id: int, db: DBSessionDep):
    """Получение детальной информации об одной оценке уязвимости."""
    repo = SqlAlchemyDatabaseRepo(db)
    try:
        assessment = await service_use_cases.get_vulnerability_assessment_details(repo, assessment_id)
        return assessment
    except interfaces.VulnerabilityAssessmentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=domains.VulnerabilityAssessment, status_code=201, dependencies=[ModeratorDep])
async def create_vulnerability_assessment(assessment_data: domains.VulnerabilityAssessmentCreate, db: DBSessionDep):
    """Создание новой оценки уязвимости (только для модераторов)."""
    repo = SqlAlchemyDatabaseRepo(db)
    try:
        new_assessment = await service_use_cases.create_new_vulnerability_assessment(repo, assessment_data)
        await db.commit()
        return new_assessment
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{assessment_id}", response_model=domains.VulnerabilityAssessment, dependencies=[ModeratorDep])
async def update_vulnerability_assessment(assessment_id: int, assessment_data: domains.VulnerabilityAssessmentUpdate, db: DBSessionDep):
    """Обновление существующей оценки уязвимости (только для модераторов)."""
    repo = SqlAlchemyDatabaseRepo(db)
    try:
        updated_assessment = await service_use_cases.update_existing_vulnerability_assessment(repo, assessment_id, assessment_data)
        await db.commit()
        return updated_assessment
    except interfaces.VulnerabilityAssessmentNotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{assessment_id}", status_code=204, dependencies=[ModeratorDep])
async def delete_vulnerability_assessment(assessment_id: int, db: DBSessionDep, storage: FileStorageDep):
    """Удаление оценки уязвимости и связанного с ней изображения (только для модераторов)."""
    repo = SqlAlchemyDatabaseRepo(db)
    try:
        await service_use_cases.delete_vulnerability_assessment(repo, storage, assessment_id)
        await db.commit()
    except interfaces.VulnerabilityAssessmentNotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(e))
    return None


@router.post("/{assessment_id}/image", response_model=domains.VulnerabilityAssessment, dependencies=[ModeratorDep])
async def upload_image(assessment_id: int, db: DBSessionDep, storage: FileStorageDep, image: UploadFile = File(...)):
    """Загрузка/обновление изображения для оценки уязвимости (только для модераторов)."""
    repo = SqlAlchemyDatabaseRepo(db)
    try:
        updated_assessment_orm = await service_use_cases.update_vulnerability_assessment_image(repo, storage, assessment_id, image)
        await db.commit()
        return domains.VulnerabilityAssessment.model_validate(updated_assessment_orm)
    except interfaces.VulnerabilityAssessmentNotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        await db.rollback()
        print(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail="File upload failed.")
