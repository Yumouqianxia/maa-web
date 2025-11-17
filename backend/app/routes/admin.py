"""Management API endpoints for devices and tasks."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import DeviceOut, TaskCreate, TaskOut
from app.services import DeviceService, TaskService

router = APIRouter(prefix="/api", tags=["admin"])


@router.get("/devices", response_model=list[DeviceOut])
def list_devices(
    user: str | None = Query(
        default=None, description="Filter devices by user key (optional)."
    ),
    db: Session = Depends(get_db),
) -> list[DeviceOut]:
    """Return known devices, optionally filtered by user."""

    device_service = DeviceService(db)
    if user:
        # If user does not exist yet, return empty list for clarity.
        if not device_service.get_user(user):
            return []
    devices = device_service.list_devices(user)
    return devices


@router.get(
    "/devices/{device_id}/tasks",
    response_model=list[TaskOut],
)
def list_device_tasks(
    device_id: str,
    user: str = Query(..., description="User key that owns the device."),
    limit: int = Query(20, ge=1, le=100, description="Number of tasks to return."),
    db: Session = Depends(get_db),
) -> list[TaskOut]:
    """Return recent tasks for a specific device."""

    device_service = DeviceService(db)
    task_service = TaskService(db)

    user_obj = device_service.get_user(user)
    if user_obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    device = device_service.get_device(user_key=user, device_identifier=device_id)
    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Device not found."
        )

    tasks = task_service.list_recent_tasks(device=device, limit=limit)
    return list(tasks)


@router.post(
    "/devices/{device_id}/tasks",
    response_model=TaskOut,
    status_code=status.HTTP_201_CREATED,
)
def create_task_for_device(
    device_id: str,
    task_in: TaskCreate,
    user: str = Query(..., description="User key that owns the device."),
    db: Session = Depends(get_db),
) -> TaskOut:
    """Create a new task assigned to the given device."""

    device_service = DeviceService(db)
    task_service = TaskService(db)

    user_obj = device_service.get_user(user)
    if user_obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    device = device_service.get_device(user_key=user, device_identifier=device_id)
    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Device not found."
        )

    task = task_service.enqueue_task(
        user=user_obj,
        device=device,
        task_type=task_in.type,
        payload=task_in.params,
        priority=task_in.priority,
    )
    db.commit()
    db.refresh(task)
    return task

