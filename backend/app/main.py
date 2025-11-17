"""FastAPI application bootstrap."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import configure_logging
from app.db.session import Base, engine
from app.routes.admin import router as admin_router
from app.routes.maa import router as maa_router


def create_app() -> FastAPI:
    """Application factory."""

    configure_logging()
    Base.metadata.create_all(bind=engine)

    app = FastAPI(title=settings.app_name, debug=settings.debug)

    if settings.allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(maa_router)
    app.include_router(admin_router)

    return app


app = create_app()


@app.get("/healthz", tags=["health"])
def health_check() -> dict[str, str]:
    """Simple health check endpoint."""

    return {"status": "ok"}

