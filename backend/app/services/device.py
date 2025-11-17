"""Device related business logic."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Device, User


class DeviceService:
    """Service object encapsulating device persistence operations."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_user(self, user_key: str) -> User | None:
        """Fetch a user by key if it exists."""

        stmt = select(User).where(User.user_key == user_key)
        return self._session.scalar(stmt)

    def ensure_user(self, user_key: str, name: str | None = None) -> User:
        """Get or create a user by key."""

        user = self.get_user(user_key)
        if user:
            return user

        user = User(user_key=user_key, name=name)
        self._session.add(user)
        self._session.flush()
        return user

    def register_or_touch_device(
        self,
        *,
        user: User,
        device_identifier: str,
        display_name: str | None = None,
        agent_version: str | None = None,
    ) -> Device:
        """Ensure a device exists and update its heartbeat metadata."""

        stmt = (
            select(Device)
            .where(Device.user_key == user.user_key)
            .where(Device.device_id == device_identifier)
        )
        device = self._session.scalar(stmt)

        now = datetime.now(timezone.utc)

        if device is None:
            device = Device(
                user_id=user.id,
                user_key=user.user_key,
                device_id=device_identifier,
                display_name=display_name,
                status="online",
                agent_version=agent_version,
                last_seen_at=now,
            )
            self._session.add(device)
        else:
            device.last_seen_at = now
            device.agent_version = agent_version or device.agent_version
            device.status = "online"
            if display_name:
                device.display_name = display_name

        self._session.flush()
        return device

    def list_devices(self, user_key: str | None = None) -> list[Device]:
        """List devices optionally filtered by user."""

        stmt = select(Device).order_by(Device.created_at.desc())
        if user_key:
            stmt = stmt.where(Device.user_key == user_key)
        return list(self._session.scalars(stmt))

    def get_device(self, *, user_key: str, device_identifier: str) -> Device | None:
        """Fetch a device by composite key."""

        stmt = (
            select(Device)
            .where(Device.user_key == user_key)
            .where(Device.device_id == device_identifier)
        )
        return self._session.scalar(stmt)

