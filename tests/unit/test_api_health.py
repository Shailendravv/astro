"""M1 API slice: health, version, and the localhost protections from docs/security.md section 2."""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from engine import ENGINE_VERSION
from jyotish_api import APP_VERSION
from jyotish_api.config import Settings
from jyotish_api.main import create_app

ORIGIN = "http://127.0.0.1:3000"


def make_settings(**overrides: str) -> Settings:
    values = {
        "app_env": "test",
        "database_url": "postgresql+psycopg://unused:unused@127.0.0.1:1/unused",
        "allowed_origins": ORIGIN,
        "allowed_hosts": "127.0.0.1,localhost",
        **overrides,
    }
    return Settings(**values)  # type: ignore[arg-type]


def client(database_ok: bool = True, **overrides: str) -> TestClient:
    app = create_app(make_settings(**overrides), database_check=lambda: database_ok)
    return TestClient(app, base_url="http://127.0.0.1")


def test_health_ok_when_database_answers() -> None:
    response = client(database_ok=True).get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["checks"]["database"] == "ok"


def test_health_is_honest_about_unbuilt_checks() -> None:
    body = client().get("/api/v1/health").json()
    # Ephemeris and library are not built in M1: never report them as "ok".
    assert body["checks"]["ephemeris_files"] == "not_configured"
    assert body["checks"]["library_mount"] == "not_configured"


def test_health_503_when_database_down() -> None:
    response = client(database_ok=False).get("/api/v1/health")
    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
    assert response.json()["checks"]["database"] == "error"


def test_version_reports_stored_versions_and_nulls_for_unbuilt_parts() -> None:
    body = client(git_commit="abc1234").get("/api/v1/version").json()
    assert body["app_version"] == APP_VERSION
    assert body["engine_version"] == ENGINE_VERSION
    assert body["git_commit"] == "abc1234"
    assert body["ephemeris"] is None
    assert body["tzdata"] is None
    assert body["dataset_versions"] == []


def test_ai_disabled_without_model_configuration() -> None:
    assert client().get("/api/v1/health").json()["ai_enabled"] is False
    assert make_settings().ai_enabled is False
    # A provider without a model ID (or the reverse) must not enable AI features.
    assert make_settings(runtime_provider="some-provider").ai_enabled is False
    assert make_settings(runtime_model_id="some-id").ai_enabled is False


def test_host_header_not_on_allow_list_is_rejected() -> None:
    response = client().get("/api/v1/health", headers={"Host": "evil.example"})
    assert response.status_code == 400


def test_cors_allows_only_the_configured_origin() -> None:
    http = client()
    allowed = http.get("/api/v1/health", headers={"Origin": ORIGIN})
    assert allowed.headers.get("access-control-allow-origin") == ORIGIN
    assert "access-control-allow-credentials" not in allowed.headers
    other = http.get("/api/v1/health", headers={"Origin": "http://evil.example"})
    assert "access-control-allow-origin" not in other.headers


@pytest.mark.parametrize("field", ["app_env", "database_url", "allowed_origins", "allowed_hosts"])
def test_settings_have_no_silent_fallback(field: str) -> None:
    values = {
        "app_env": "test",
        "database_url": "postgresql+psycopg://x:y@127.0.0.1/z",
        "allowed_origins": ORIGIN,
        "allowed_hosts": "127.0.0.1",
    }
    del values[field]
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **values)  # type: ignore[arg-type]


@pytest.mark.parametrize("field", ["allowed_origins", "allowed_hosts"])
def test_wildcards_are_rejected(field: str) -> None:
    with pytest.raises(ValidationError):
        make_settings(**{field: "*"})
