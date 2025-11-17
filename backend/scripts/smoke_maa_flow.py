"""Quick smoke test for /maa/getTask and /maa/reportStatus without running uvicorn."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.db.session import Base, SessionLocal, engine
from app.main import app
from app.models import Device, Task, TaskStatus, User


def seed_task() -> str:
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
        return task.task_uuid
    finally:
        session.close()


def main() -> None:
    Base.metadata.create_all(bind=engine)
    task_uuid = seed_task()
    client = TestClient(app)

    get_task_payload = {
        "user": "demo-user",
        "device": "pc-mock",
        "agentVersion": "local-test",
    }
    resp = client.post("/maa/getTask", json=get_task_payload)
    resp.raise_for_status()
    body = resp.json()
    print("getTask response:", body)

    report_payload = {
        "user": "demo-user",
        "device": "pc-mock",
        "taskId": task_uuid,
        "status": "Succeeded",
        "log": "smoke test ok",
        "result": {"command": ["maa", "run", "daily"], "returnCode": 0},
    }
    resp = client.post("/maa/reportStatus", json=report_payload)
    resp.raise_for_status()
    print("reportStatus response status:", resp.status_code)


if __name__ == "__main__":
    main()

