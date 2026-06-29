"""
task_models.py — Generieke takenlijst / workflow (geport vanuit Datavalidatie).

App-onafhankelijk: één `tasks`-tabel, tenant-gescoped, toewijzen binnen de eigen
organisatie. Koppeling naar de bron (bv. een CRM-organisatie) via
source_type/source_ref/source_label, zonder harde FK — model identiek over apps.
CRM-variant: gebruikt het dialect-neutrale GUID-type uit app.database (SQLite-test + Postgres).
"""
import enum
import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base, GUID


class TaskStatus(str, enum.Enum):
    OPEN           = "OPEN"
    IN_BEHANDELING = "IN_BEHANDELING"
    KLAAR          = "KLAAR"
    GEANNULEERD    = "GEANNULEERD"


class TaskPriority(str, enum.Enum):
    LAAG    = "LAAG"
    NORMAAL = "NORMAAL"
    HOOG    = "HOOG"


class Task(Base):
    """Een taak op gebruikersniveau, altijd binnen één tenant (organisatie)."""
    __tablename__ = "tasks"

    id          = Column(GUID(), primary_key=True, default=uuid.uuid4)
    tenant_id   = Column(GUID(), ForeignKey("tenants.id", ondelete="CASCADE"),
                         nullable=False, index=True)

    title       = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    status      = Column(Enum(TaskStatus,   name="task_status",   native_enum=False), nullable=False, default=TaskStatus.OPEN)
    priority    = Column(Enum(TaskPriority, name="task_priority", native_enum=False), nullable=False, default=TaskPriority.NORMAAL)
    due_date    = Column(DateTime(timezone=True), nullable=True)

    assignee_id   = Column(GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by_id = Column(GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    app_slug     = Column(String(40),  nullable=True)
    source_type  = Column(String(40),  nullable=True)
    source_ref   = Column(String(255), nullable=True)
    source_label = Column(String(255), nullable=True)

    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    assignee   = relationship("User", foreign_keys=[assignee_id])
    created_by = relationship("User", foreign_keys=[created_by_id])


Index("ix_tasks_tenant_status", Task.tenant_id, Task.status)
Index("ix_tasks_assignee_status", Task.assignee_id, Task.status)
