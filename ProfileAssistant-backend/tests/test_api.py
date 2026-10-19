from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Config
from app.main import app
from app.mcp_server import create_mcp_http_app


client = TestClient(app)


def test_health_endpoint_returns_healthy_status():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_profile_endpoint_returns_labelled_sample_data():
    response = client.get("/api/profile")

    assert response.status_code == 200
    profile = response.json()
    assert profile["profile_type"] == "sample"
    assert "not a real person's profile" in profile["notice"]
    assert profile["name"] == "Sample User"


def test_profile_source_paths_use_repository_defaults(monkeypatch):
    monkeypatch.delenv("PROFILE_SOURCE_DIR", raising=False)
    monkeypatch.delenv("PROFILE_LINKEDIN_PDF", raising=False)
    monkeypatch.delenv("PROFILE_RESUME_PDF", raising=False)

    paths = Config.get_profile_source_paths()

    expected_dir = Path(__file__).resolve().parents[1] / "data" / "profile_sources"
    assert paths["linkedin"] == (expected_dir / "linkedin_profile.pdf").resolve()
    assert paths["resume"] == (expected_dir / "resume.pdf").resolve()


def test_profile_source_paths_allow_individual_overrides(monkeypatch, tmp_path):
    linkedin_path = tmp_path / "custom-linkedin.pdf"
    resume_path = tmp_path / "custom-resume.pdf"
    monkeypatch.setenv("PROFILE_SOURCE_DIR", str(tmp_path / "unused-defaults"))
    monkeypatch.setenv("PROFILE_LINKEDIN_PDF", str(linkedin_path))
    monkeypatch.setenv("PROFILE_RESUME_PDF", str(resume_path))

    paths = Config.get_profile_source_paths()

    assert paths == {
        "linkedin": linkedin_path.resolve(),
        "resume": resume_path.resolve(),
    }


def test_mcp_endpoint_is_mounted():
    assert any(route.path == "/" for route in app.routes)

    with TestClient(app) as test_client:
        response = test_client.get("/mcp")

    assert response.status_code != 404


def test_mcp_transport_allowlist_includes_hugging_face_space_host(monkeypatch):
    monkeypatch.setenv("SPACE_HOST", "profile-demo.hf.space")
    monkeypatch.delenv("PROFILE_MCP_ALLOWED_HOSTS", raising=False)

    allowed_hosts = Config.get_profile_mcp_allowed_hosts()

    assert "profile-demo.hf.space" in allowed_hosts