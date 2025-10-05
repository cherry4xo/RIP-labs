from typing import Optional, List
import uuid

from fastapi import UploadFile

from app import domains
from app.interfaces import AbstractDatabaseRepo, AbstractFileStorage, VulnerabilityAssessmentNotFoundError


async def get_vulnerability_assessments_list(
    repo: AbstractDatabaseRepo,
    title: Optional[str] = None,
    assessment_type: Optional[str] = None
) -> List[domains.VulnerabilityAssessment]:
    """Get list of vulnerability assessments with optional filtering."""
    return await repo.get_vulnerability_assessments_with_filters(title, assessment_type)


async def get_vulnerability_assessment_details(
    repo: AbstractDatabaseRepo,
    assessment_id: int
) -> domains.VulnerabilityAssessment:
    """Get details of a specific vulnerability assessment."""
    assessment = await repo.get_vulnerability_assessment_by_id(assessment_id)
    if not assessment:
        raise VulnerabilityAssessmentNotFoundError("Vulnerability assessment not found")
    return assessment


async def create_new_vulnerability_assessment(
    repo: AbstractDatabaseRepo,
    assessment_data: domains.VulnerabilityAssessmentCreate
) -> domains.VulnerabilityAssessment:
    """Create a new vulnerability assessment."""
    return await repo.create_vulnerability_assessment(assessment_data)


async def update_existing_vulnerability_assessment(
    repo: AbstractDatabaseRepo,
    assessment_id: int,
    assessment_data: domains.VulnerabilityAssessmentUpdate
) -> domains.VulnerabilityAssessment:
    """Update an existing vulnerability assessment."""
    updated_assessment = await repo.update_vulnerability_assessment(assessment_id, assessment_data)
    if not updated_assessment:
        raise VulnerabilityAssessmentNotFoundError("Vulnerability assessment not found")
    return updated_assessment


async def delete_vulnerability_assessment(
    db_repo: AbstractDatabaseRepo, 
    file_storage: AbstractFileStorage, 
    assessment_id: int
):
    """Delete a vulnerability assessment and its associated image."""
    assessment = await db_repo.get_vulnerability_assessment_by_id(assessment_id)
    if not assessment:
        raise VulnerabilityAssessmentNotFoundError("Vulnerability assessment not found")
    
    if assessment.image_url:
        file_storage.delete(assessment.image_url)
        
    await db_repo.delete_vulnerability_assessment(assessment_id)


async def update_vulnerability_assessment_image(
    db_repo: AbstractDatabaseRepo, 
    file_storage: AbstractFileStorage, 
    assessment_id: int, 
    image: UploadFile
):
    """Update the image for a vulnerability assessment."""
    assessment = await db_repo.get_vulnerability_assessment_by_id(assessment_id)
    if not assessment:
        raise VulnerabilityAssessmentNotFoundError("Vulnerability assessment not found")

    if assessment.image_url:
        file_storage.delete(assessment.image_url)

    file_extension = image.filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    image_url = file_storage.save(image.file, unique_filename, image.content_type)
    
    update_data = domains.VulnerabilityAssessmentUpdatePartial(image_url=image_url)
    return await db_repo.update_vulnerability_assessment(assessment_id, update_data)
