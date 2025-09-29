from typing import Optional, List
import uuid

from fastapi import UploadFile

from app import domains
from app.interfaces import AbstractDatabaseRepo, AbstractFileStorage, ServiceNotFoundError


async def view_services_list(
    repo: AbstractDatabaseRepo,
    query: Optional[str] = None
) -> List[domains.Service]:
    return await repo.get_services(query=query)


async def view_service_details(
    repo: AbstractDatabaseRepo,
    service_id: int
) -> Optional[domains.Service]:
    return await repo.get_service_by_id(service_id=service_id)


async def delete_service(db_repo: AbstractDatabaseRepo, file_storage: AbstractFileStorage, service_id: int):
    service = await db_repo.get_service_by_id(service_id)
    if not service:
        raise ServiceNotFoundError("Service not found")
    
    if service.image_url:
        file_storage.delete(service.image_url)
        
    await db_repo.delete_service(service_id)


async def update_service_image(db_repo: AbstractDatabaseRepo, file_storage: AbstractFileStorage, service_id: int, image: UploadFile):
    service = await db_repo.get_service_by_id(service_id)
    if not service:
        raise ServiceNotFoundError("Service not found")

    if service.image_url:
        file_storage.delete(service.image_url)

    file_extension = image.filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    image_url = file_storage.save(image.file, unique_filename, image.content_type)
    
    return await db_repo.update_service(service_id, domains.ServiceUpdate(image_url=image_url))