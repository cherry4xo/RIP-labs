from typing import Optional, List
import uuid

from fastapi import UploadFile

from app import domains
from app.interfaces import AbstractDatabaseRepo, AbstractFileStorage, ServiceNotFoundError


async def get_services_list(
    repo: AbstractDatabaseRepo,
    title: Optional[str] = None,
    assessment_type: Optional[str] = None
) -> List[domains.Service]:
    """Get list of services with optional filtering."""
    return await repo.get_services_with_filters(title, assessment_type)


async def get_service_details(
    repo: AbstractDatabaseRepo,
    service_id: int
) -> domains.Service:
    """Get details of a specific service."""
    service = await repo.get_service_by_id(service_id)
    if not service:
        raise ServiceNotFoundError("Service not found")
    return service


async def create_new_service(
    repo: AbstractDatabaseRepo,
    service_data: domains.ServiceCreate
) -> domains.Service:
    """Create a new service."""
    return await repo.create_service(service_data)


async def update_existing_service(
    repo: AbstractDatabaseRepo,
    service_id: int,
    service_data: domains.ServiceUpdate
) -> domains.Service:
    """Update an existing service."""
    updated_service = await repo.update_service(service_id, service_data)
    if not updated_service:
        raise ServiceNotFoundError("Service not found")
    return updated_service


async def delete_service(
    db_repo: AbstractDatabaseRepo, 
    file_storage: AbstractFileStorage, 
    service_id: int
):
    """Delete a service and its associated image."""
    service = await db_repo.get_service_by_id(service_id)
    if not service:
        raise ServiceNotFoundError("Service not found")
    
    if service.image_url:
        file_storage.delete(service.image_url)
        
    await db_repo.delete_service(service_id)


async def update_service_image(
    db_repo: AbstractDatabaseRepo, 
    file_storage: AbstractFileStorage, 
    service_id: int, 
    image: UploadFile
):
    """Update the image for a service."""
    service = await db_repo.get_service_by_id(service_id)
    if not service:
        raise ServiceNotFoundError("Service not found")

    if service.image_url:
        file_storage.delete(service.image_url)

    file_extension = image.filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    image_url = file_storage.save(image.file, unique_filename, image.content_type)
    
    update_data = domains.ServiceUpdatePartial(image_url=image_url)
    return await db_repo.update_service(service_id, update_data)
