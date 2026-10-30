import pytest

from app.core.config import Config


@pytest.mark.parametrize(
    "env_var",
    ["GITHUB_TOKEN", "GITHUB_PERSONAL_ACCESS_TOKEN"],
)
def test_github_token_config_is_available(monkeypatch, env_var):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_PERSONAL_ACCESS_TOKEN", raising=False)
    monkeypatch.setenv(env_var, "test-token")

    assert Config.get_github_token() == "test-token"


def test_github_mcp_server_params_include_token_and_command(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")

    params = Config.get_github_mcp_server_params()

    assert params.command == "npx"
    assert "@modelcontextprotocol/server-github" in params.args
    assert params.env["GITHUB_TOKEN"] == "test-token"
