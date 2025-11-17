"""Schemas aligned with MAA remote control protocol."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.task import TaskStatus


class MaaBaseModel(BaseModel):
    """Pydantic base model with shared configuration."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class TaskEnvelope(MaaBaseModel):
    """Task descriptor returned to or received from an agent."""

    id: str = Field(description="Task identifier shared with the agent.")
    type: str = Field(description="Task type following Maa schema, e.g., LinkStart.")
    params: dict[str, Any] = Field(
        default_factory=dict, description="Task parameters/payload."
    )
    priority: int = Field(default=0, description="Optional task priority hint.")


class GetTaskRequest(MaaBaseModel):
    """Request payload from agent when pulling tasks."""

    user: str = Field(description="User key associated with the agent.")
    device: str = Field(description="Unique identifier for the agent device.")
    agentVersion: str | None = Field(
        default=None,
        description="Agent software version string.",
    )
    capabilities: dict[str, Any] | None = Field(
        default=None,
        description="Optional capability advertisement.",
    )
    status: dict[str, Any] | None = Field(
        default=None,
        description="Optional heartbeat status sent alongside polling.",
    )


class GetTaskResponse(MaaBaseModel):
    """Response to agent with queued tasks."""

    tasks: list[TaskEnvelope] = Field(default_factory=list)
    pollInterval: float | None = Field(
        default=None,
        description="Optional override for agent polling interval (seconds).",
    )


class TaskReportPayload(MaaBaseModel):
    """Supplemental result payload inside report status."""

    status: TaskStatus = Field(description="Execution status reported by agent.")
    log: str | None = Field(default=None, description="Execution log snippet.")
    result: dict[str, Any] | None = Field(
        default=None,
        description="Optional structured result data.",
    )
    stats: dict[str, Any] | None = Field(
        default=None,
        description="Optional structured statistics data.",
    )


class ReportStatusRequest(MaaBaseModel):
    """Report status payload received from agent."""

    user: str = Field(description="User key associated with the agent.")
    device: str = Field(description="Unique identifier for the agent device.")
    taskId: str = Field(description="Task identifier to update.")
    status: TaskStatus = Field(description="Execution status.")
    log: str | None = Field(default=None, description="Execution log snippet.")
    result: dict[str, Any] | None = Field(
        default=None, description="Structured result payload."
    )
    stats: dict[str, Any] | None = Field(
        default=None, description="Run statistics for the task."
    )

