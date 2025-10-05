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


@router.get("/", response_model=List[domains.Service])
async def get_services(
    db: DBSessionDep,
    title: Optional[str] = None,
    assessment_type: Optional[domains.ServiceAssessmentType] = None
):
    """Получение списка услуг с возможностью фильтрации."""
    repo = SqlAlchemyDatabaseRepo(db)
    try:
        services = await service_use_cases.get_services_list(repo, title, assessment_type.value if assessment_type else None)
        return services
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{service_id}", response_model=domains.Service)
async def get_service(service_id: int, db: DBSessionDep):
    """Получение детальной информации об одной услуге."""
    repo = SqlAlchemyDatabaseRepo(db)
    try:
        service = await service_use_cases.get_service_details(repo, service_id)
        return service
    except interfaces.ServiceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=domains.Service, status_code=201, dependencies=[ModeratorDep])
async def create_service(service_data: domains.ServiceCreate, db: DBSessionDep):
    """Создание новой услуги (только для модераторов)."""
    repo = SqlAlchemyDatabaseRepo(db)
    try:
        new_service = await service_use_cases.create_new_service(repo, service_data)
        await db.commit()
        return new_service
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{service_id}", response_model=domains.Service, dependencies=[ModeratorDep])
async def update_service(service_id: int, service_data: domains.ServiceUpdate, db: DBSessionDep):
    """Обновление существующей услуги (только для модераторов)."""
    repo = SqlAlchemyDatabaseRepo(db)
    try:
        updated_service = await service_use_cases.update_existing_service(repo, service_id, service_data)
        await db.commit()
        return updated_service
    except interfaces.ServiceNotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{service_id}", status_code=204, dependencies=[ModeratorDep])
async def delete_service(service_id: int, db: DBSessionDep, storage: FileStorageDep):
    """Удаление услуги и связанного с ней изображения (только для модераторов)."""
    repo = SqlAlchemyDatabaseRepo(db)
    try:
        await service_use_cases.delete_service(repo, storage, service_id)
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
        updated_service_orm = await service_use_cases.update_service_image(repo, storage, service_id, image)
        await db.commit()
        return domains.Service.model_validate(updated_service_orm)
    except interfaces.ServiceNotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        await db.rollback()
        print(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail="File upload failed.")
