"""Schemas for admin REST API and frontend consumption."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.task import TaskStatus


class AdminBaseModel(BaseModel):
    """Shared configuration for admin API schemas."""

    model_config = ConfigDict(from_attributes=True)


class DeviceOut(AdminBaseModel):
    """Serialized device information."""

    id: int
    user_key: str
    device_id: str
    display_name: str | None = None
    status: str
    agent_version: str | None = None
    last_seen_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class TaskCreate(AdminBaseModel):
    """Payload for creating a new task."""

    type: str = Field(description="Task type identifier.")
    params: dict[str, Any] = Field(
        default_factory=dict, description="Task parameter payload."
    )
    priority: int = Field(default=0, ge=0, description="Task priority ordering.")


class TaskUpdateStatus(AdminBaseModel):
    """Payload for updating a task state from admin interfaces."""

    status: TaskStatus
    log: str | None = None
    error_message: str | None = None


class TaskOut(AdminBaseModel):
    """Serialized task information for API responses."""

    id: int
    task_uuid: str
    user_key: str
    device_identifier: str
    type: str
    payload: dict[str, Any]
    status: TaskStatus
    priority: int
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    log: str | None = None
    error_message: str | None = None


class TaskLogOut(AdminBaseModel):
    """Serialized task log entry."""

    id: int
    level: str
    message: str
    created_at: datetime


