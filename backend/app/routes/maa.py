"""Routes implementing the Maa remote-control protocol."""

from __future__ import annotations

import logging
from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Task
from app.schemas.maa import (
    GetTaskRequest,
    GetTaskResponse,
    ReportStatusRequest,
    TaskEnvelope,
)
from app.services import DeviceService, TaskService

logger = logging.getLogger(__name__)

MAX_LOG_CHARS = 4000

router = APIRouter(prefix="/maa", tags=["maa"])


def _serialize_tasks(tasks: Sequence[Task]) -> list[TaskEnvelope]:
    envelopes: list[TaskEnvelope] = []
    for task in tasks:
        envelopes.append(
            TaskEnvelope(
                id=task.task_uuid,
                type=task.type,
                params=task.payload or {},
                priority=task.priority,
            )
        )
    return envelopes


@router.post("/getTask", response_model=GetTaskResponse)
def get_task(
    payload: GetTaskRequest,
    db: Session = Depends(get_db),
) -> GetTaskResponse:
    """Agent polling endpoint fetching pending tasks."""

    device_service = DeviceService(db)
    task_service = TaskService(db)

    user = device_service.ensure_user(payload.user)
    device = device_service.register_or_touch_device(
        user=user,
        device_identifier=payload.device,
        agent_version=payload.agentVersion,
    )

    task = task_service.fetch_next_pending_task(
        user_key=user.user_key,
        device_identifier=device.device_id,
    )

    tasks = _serialize_tasks([task]) if task else []
    db.commit()
    return GetTaskResponse(tasks=tasks)


@router.post("/reportStatus", status_code=status.HTTP_200_OK)
def report_status(
    payload: ReportStatusRequest,
    db: Session = Depends(get_db),
) -> None:
    """Agent reporting execution results for a task."""

    device_service = DeviceService(db)
    task_service = TaskService(db)

    user = device_service.ensure_user(payload.user)
    device = device_service.get_device(
        user_key=user.user_key, device_identifier=payload.device
    )
    if device is None:
        device = device_service.register_or_touch_device(
            user=user, device_identifier=payload.device
        )

    task = task_service.get_by_uuid(payload.taskId)
    if task is None:
        logger.warning(
            "Report for unknown task %s from device %s",
            payload.taskId,
            payload.device,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found."
        )

    if task.user_key != user.user_key or task.device_identifier != device.device_id:
        logger.error(
            "Task ownership mismatch: task %s user/device %s/%s, got %s/%s",
            payload.taskId,
            task.user_key,
            task.device_identifier,
            user.user_key,
            device.device_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task does not belong to the provided user/device.",
        )

    truncated_log = payload.log[:MAX_LOG_CHARS] if payload.log else None

    task_service.update_status(
        task,
        status=payload.status,
        log=truncated_log,
        result=payload.result,
        stats=payload.stats,
    )
    device_service.register_or_touch_device(
        user=user,
        device_identifier=device.device_id,
        agent_version=payload.result.get("agentVersion") if payload.result else None,
    )

    db.commit()

