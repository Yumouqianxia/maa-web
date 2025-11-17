"""Task and task log model definitions."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.session import Base

_PAYLOAD_TYPE = JSON().with_variant(SQLiteJSON(), "sqlite")


class TaskStatus(str, Enum):
    """Enumeration of task lifecycle states."""

    PENDING = "Pending"
    RUNNING = "Running"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


class Task(Base):
    """Represents a remote execution task assigned to an agent device."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_uuid: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, default=lambda: uuid4().hex
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user_key: Mapped[str] = mapped_column(String(64), index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), nullable=False)
    device_identifier: Mapped[str] = mapped_column(String(128), index=True)
    type: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict[str, Any]] = mapped_column(_PAYLOAD_TYPE, default=dict)
    status: Mapped[TaskStatus] = mapped_column(
        SAEnum(TaskStatus, native_enum=False, length=16), default=TaskStatus.PENDING
    )
    priority: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    log: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="tasks")
    device: Mapped["Device"] = relationship(back_populates="tasks")
    logs: Mapped[list["TaskLog"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )


class TaskLog(Base):
    """Fine-grained logging entries associated with a task."""

    __tablename__ = "task_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    level: Mapped[str] = mapped_column(String(16), default="INFO")
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    task: Mapped[Task] = relationship(back_populates="logs")


__all__ = ["Task", "TaskLog", "TaskStatus"]

