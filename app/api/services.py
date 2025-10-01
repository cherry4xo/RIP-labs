# app/api/services.py

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from app.auth.dependencies import ModeratorDep, CurrentUserDep
from app.core.database import DBSessionDep
from app.file_storage.minio_storage import FileStorageDep
from app.repository import SqlAlchemyDatabaseRepo
from app import domains, interfaces, use_cases

router = APIRouter(prefix="/services", tags=["Services"])


@router.get("/", response_model=List[domains.Service])
async def get_services(
    db: DBSessionDep,
    title: Optional[str] = None,
    assessment_type: Optional[domains.ServiceAssessmentType] = None
):
    """Получение списка услуг с возможностью фильтрации."""
    repo = SqlAlchemyDatabaseRepo(db)
    services_orm = await repo.get_services_with_filters(title, assessment_type)
    return [domains.Service.model_validate(s) for s in services_orm]


@router.get("/{service_id}", response_model=domains.Service)
async def get_service(service_id: int, db: DBSessionDep):
    """Получение детальной информации об одной услуге."""
    repo = SqlAlchemyDatabaseRepo(db)
    service_orm = await repo.get_service_by_id(service_id)
    if not service_orm:
        raise HTTPException(status_code=404, detail="Service not found")
    return domains.Service.model_validate(service_orm)


@router.post("/", response_model=domains.Service, status_code=201, dependencies=[ModeratorDep])
async def create_service(service_data: domains.ServiceCreate, db: DBSessionDep):
    """Создание новой услуги (только для модераторов)."""
    repo = SqlAlchemyDatabaseRepo(db)
    new_service_orm = await repo.create_service(service_data)
    await db.commit()
    return domains.Service.model_validate(new_service_orm)


@router.put("/{service_id}", response_model=domains.Service, dependencies=[ModeratorDep])
async def update_service(service_id: int, service_data: domains.ServiceUpdate, db: DBSessionDep):
    """Обновление существующей услуги (только для модераторов)."""
    repo = SqlAlchemyDatabaseRepo(db)
    updated_service_orm = await repo.update_service(service_id, service_data)
    if not updated_service_orm:
        raise HTTPException(status_code=404, detail="Service not found")
    await db.commit()
    return domains.Service.model_validate(updated_service_orm)


@router.delete("/{service_id}", status_code=204, dependencies=[ModeratorDep])
async def delete_service(service_id: int, db: DBSessionDep, storage: FileStorageDep):
    """Удаление услуги и связанного с ней изображения (только для модераторов)."""
    repo = SqlAlchemyDatabaseRepo(db)
    try:
        await use_cases.service.delete_service(repo, storage, service_id)
        await db.commit()
    except interfaces.ServiceNotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(e))
    return None


@router.post("/{service_id}/image", response_model=domains.Service, dependencies=[ModeratorDep])
async def upload_image(service_id: int, db: DBSessionDep, storage: FileStorageDep, image: UploadFile = File(...)):
    """Загрузка/обновление изображения для услуги (только для модераторов)."""
    repo = SqlAlchemyDatabaseRepo(db)
    try:
        updated_service_orm = await use_cases.service.update_service_image(repo, storage, service_id, image)
        await db.commit()
        return domains.Service.model_validate(updated_service_orm)
    except interfaces.ServiceNotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        await db.rollback()
        print(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail="File upload failed.")