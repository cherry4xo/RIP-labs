# app/domains.py

from datetime import datetime, date
import enum
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

# --- Enums ---
class ProtectionLevel(enum.StrEnum):
    NONE = "none"
    BASIC = "basic"
    FULL = "full"

class VulnerabilityAssessmentType(enum.StrEnum):
    NETWORK_SCAN = "network_scan"
    WEB_APP_PENTEST = "web_app_pentest"
    INFRASTRUCTURE_AUDIT = "infrastructure_audit"

class AssessmentStatus(enum.StrEnum):
    DELETED = "deleted"
    AVAILABLE = "available"

class ReportStatus(enum.StrEnum):
    DRAFT = "draft"
    DELETED = "deleted"
    FORMED = "formed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# --- Vulnerability Assessment Schemas ---
class VulnerabilityAssessmentBase(BaseModel):
    title: str = Field(min_length=3, max_length=128)
    short_description: Optional[str] = None
    description: str
    price: Decimal = Field(gt=0)
    impact_level: int = Field(ge=1, le=3)
    assessment_type: VulnerabilityAssessmentType

class VulnerabilityAssessmentCreate(VulnerabilityAssessmentBase):
    pass

class VulnerabilityAssessmentUpdatePartial(BaseModel):
    title: Optional[str] = Field(min_length=3, max_length=128, default=None)
    short_description: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = Field(gt=0, default=None)
    impact_level: Optional[int] = Field(ge=1, le=3, default=None)
    assessment_type: Optional[VulnerabilityAssessmentType] = None
    image_url: Optional[str] = None

class VulnerabilityAssessmentUpdate(VulnerabilityAssessmentBase):
    title: Optional[str] = Field(None, min_length=3, max_length=128)
    short_description: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0)
    impact_level: Optional[int] = Field(None, ge=1, le=3)
    assessment_type: Optional[VulnerabilityAssessmentType] = None

class VulnerabilityAssessment(VulnerabilityAssessmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: AssessmentStatus
    image_url: Optional[str] = None

# --- User & Auth Schemas ---
class UserCreate(BaseModel):
    login: str = Field(min_length=3)
    password: str = Field(min_length=4)

class UserUpdate(BaseModel):
    login: Optional[str] = Field(min_length=3, default=None)

class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    login: str
    is_moderator: bool

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: Optional[str] = None

# --- Assessment Report & Basket Schemas ---
class AssessmentBasketInfo(BaseModel):
    report_id: int
    item_count: int

class AssessmentBasketItemAdd(BaseModel):
    assessment_id: int

class AssessmentBasketItemUpdate(BaseModel):
    protection_level: ProtectionLevel
    comment: Optional[str] = None

class AssessmentReportUpdate(BaseModel):
    target_system_info: str = Field("", min_length=5)

class AssessmentReportFormComponentPayload(BaseModel):
    assessment_id: int
    protection_level: ProtectionLevel
    comment: Optional[str] = None

class AssessmentReportFormPayload(BaseModel):
    target_system_info: str = Field(min_length=5)
    # components: List[AssessmentReportFormComponentPayload]

class AssessmentComponent(BaseModel):
    vulnerability_assessment: VulnerabilityAssessment
    protection_level: ProtectionLevel
    comment: Optional[str] = None
    price_at_order_time: Decimal

class AssessmentReportDetails(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: ReportStatus
    created_at: datetime
    creator_login: str
    created_by: int
    moderator_login: Optional[str] = None
    formation_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    target_system_info: Optional[str] = None
    risk_score: Optional[int] = None
    components: List[AssessmentComponent] = []

class AssessmentReportSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: ReportStatus
    formation_date: Optional[datetime] = None
    risk_score: Optional[int] = None
    creator_login: str
