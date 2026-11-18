"""FastAPI application factory.

M1 scope: `/api/v1/health` and `/api/v1/version` only, with the localhost protections from
docs/security.md section 2 (Host-header check, strict CORS, JSON only, no cookies).
"""

from collections.abc import Callable

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from starlette.middleware.trustedhost import TrustedHostMiddleware

from engine import ENGINE_VERSION
from jyotish_api import APP_VERSION
from jyotish_api.config import Settings

DatabaseCheck = Callable[[], bool]


def make_database_check(database_url: str) -> DatabaseCheck:
    """Return a function that reports whether the database answers `SELECT 1`."""
    engine = create_engine(database_url, pool_pre_ping=True, connect_args={"connect_timeout": 3})

    def check() -> bool:
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except Exception:
            # No details in the response or logs: a connection error can contain the URL.
            return False
        return True

    return check


def create_app(settings: Settings, database_check: DatabaseCheck | None = None) -> FastAPI:
    app = FastAPI(title="Jyotish Research Platform API", version=APP_VERSION)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type"],
        allow_credentials=False,
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.hosts)

    check_db = database_check or make_database_check(settings.database_url)

    @app.get("/api/v1/health")
    def health(response: Response) -> dict[str, object]:
        database_ok = check_db()
        if not database_ok:
            response.status_code = 503
        return {
            "status": "ok" if database_ok else "degraded",
            "app_env": settings.app_env,
            "checks": {
                "database": "ok" if database_ok else "error",
                # Not built yet: reported honestly rather than as "ok".
                "ephemeris_files": "not_configured",
                "library_mount": "not_configured",
            },
            "ai_enabled": settings.ai_enabled,
        }

    @app.get("/api/v1/version")
    def version() -> dict[str, object]:
        return {
            "app_version": APP_VERSION,
            "engine_version": ENGINE_VERSION,
            "git_commit": settings.git_commit,
            # Filled in when the ephemeris, tzdata pin and datasets exist (M2-M4).
            "ephemeris": None,
            "tzdata": None,
            "dataset_versions": [],
        }

    return app
