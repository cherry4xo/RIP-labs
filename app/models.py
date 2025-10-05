import enum
from typing import Optional, List

from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import (Boolean, 
                        Column, Index, 
                        Integer, Numeric, 
                        String, 
                        ForeignKey, 
                        PrimaryKeyConstraint, 
                        Enum, 
                        DateTime, 
                        Float, 
                        Text, 
                        UniqueConstraint,
                        JSON
)

from app.domains import ProtectionLevel, VulnerabilityAssessmentType, AssessmentStatus, ReportStatus


class Base:
    def as_dict(self):
        data = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, enum.Enum):
                data[column.name] = value.value
            else:
                data[column.name] = value
        return data

Base = declarative_base(cls=Base)


class VulnerabilityAssessment(Base):
    __tablename__ = "vulnerability_assessments"

    id = Column("id", Integer, primary_key=True)
    title = Column("title", String(128))
    short_description = Column("short_description", String)
    description = Column("description", String)
    status = Column("status", Enum(AssessmentStatus, values_callable=lambda e: [x.value for x in e]), default=AssessmentStatus.AVAILABLE)
    image_url = Column("image_url", String(256), nullable=True)
    price = Column("price", Numeric(10, 2), nullable=False)
    
    impact_level = Column(Integer, nullable=False, server_default='1')

    assessment_type = Column("assessment_type", Enum(VulnerabilityAssessmentType), nullable=False)

    report_associations = relationship("AssessmentComponents", back_populates="vulnerability_assessment")


class User(Base):
    __tablename__ = "users"

    id = Column("id", Integer, primary_key=True)
    login = Column("login", String(64), unique=True)
    password_hash = Column("password_hash", String(255), nullable=True)
    is_moderator = Column("is_moderator", Boolean, default=False)
    is_deleted = Column("is_deleted", Boolean, default=False)

    created_reports = relationship(
        "AssessmentReport",
        back_populates="creator",
        foreign_keys="AssessmentReport.created_by"
    )

    moderated_reports = relationship(
        "AssessmentReport",
        back_populates="moderator",
        foreign_keys="AssessmentReport.moderated_by"
    )


class AssessmentReport(Base):
    __tablename__ = "assessment_reports"

    id = Column("id", Integer, primary_key=True)
    status = Column("status", Enum(ReportStatus, values_callable=lambda e: [x.value for x in e]), default=ReportStatus.DRAFT)
    created_at = Column("created_at", DateTime, nullable=False)
    created_by = Column("created_by", Integer, ForeignKey("users.id"))

    formation_date = Column("formation_date", DateTime, nullable=True)
    completion_date = Column("completion_date", DateTime, nullable=True)
    moderated_by = Column("moderated_by", ForeignKey("users.id"), nullable=True)

    target_system_info = Column(Text, nullable=True)
    total_cost = Column(Integer, nullable=True)

    risk_score = Column(Integer, nullable=True)

    creator = relationship(
        "User",
        back_populates="created_reports",
        foreign_keys=[created_by]
    )

    moderator = relationship(
        "User",
        back_populates="moderated_reports",
        foreign_keys=[moderated_by]
    )

    component_associations = relationship("AssessmentComponents", back_populates="report")

    __table_args__ = (
        Index(
            'uq_user_draft_report',
            'created_by', 'status',
            unique=True,
            postgresql_where=(status == 'draft')
        ),
    )


class AssessmentComponents(Base):
    __tablename__ = "assessment_components"

    service_id = Column("service_id", ForeignKey("vulnerability_assessments.id"), primary_key=True)
    order_id = Column("order_id", ForeignKey("assessment_reports.id"), primary_key=True)

    price_at_order_time = Column(Numeric(10, 2), nullable=False)

    protection_level = Column("protection_level", Enum(ProtectionLevel, values_callable=lambda e: [x.value for x in e]), default=ProtectionLevel.NONE, nullable=False)
    comment = Column(Text, nullable=True)

    report = relationship("AssessmentReport", back_populates="component_associations")
    vulnerability_assessment = relationship("VulnerabilityAssessment", back_populates="report_associations")
