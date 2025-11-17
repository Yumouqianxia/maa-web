"""Seed demo user, device, and task for manual agent testing."""

from __future__ import annotations

from app.db.session import Base, SessionLocal, engine
from app.models import Device, Task, TaskStatus, User


def main() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(user_key="demo-user").first()
        if not user:
            user = User(user_key="demo-user", name="Demo User")
            session.add(user)
            session.flush()

        device = (
            session.query(Device)
            .filter_by(user_key=user.user_key, device_id="pc-mock")
            .first()
        )
        if not device:
            device = Device(
                user_id=user.id,
                user_key=user.user_key,
                device_id="pc-mock",
                display_name="PC Mock",
                status="online",
            )
            session.add(device)
            session.flush()

        task = Task(
            user_id=user.id,
            user_key=user.user_key,
            device_id=device.id,
            device_identifier=device.device_id,
            type="LinkStart",
            payload={"note": "demo"},
            status=TaskStatus.PENDING,
        )
        session.add(task)
        session.commit()
        print(f"Seeded task {task.task_uuid} for device {device.device_id}")
    finally:
        session.close()


if __name__ == "__main__":
    main()

