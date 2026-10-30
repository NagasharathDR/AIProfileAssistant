# Configuration settings for the application

import os
from pathlib import Path

class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_default_secret_key')
    DEBUG = os.environ.get('DEBUG', 'False') == 'True'
    DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///default.db')
    PROFILE_PDF_MAX_BYTES = int(os.environ.get("PROFILE_PDF_MAX_BYTES", 10 * 1024 * 1024))
    PROFILE_PDF_MAX_PAGES = int(os.environ.get("PROFILE_PDF_MAX_PAGES", 100))
    PROFILE_CHUNK_SIZE = int(os.environ.get("PROFILE_CHUNK_SIZE", 1000))
    PROFILE_CHUNK_OVERLAP = int(os.environ.get("PROFILE_CHUNK_OVERLAP", 150))
    PROFILE_EMBEDDING_MODEL = os.environ.get(
        "PROFILE_EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5"
    )
    PROFILE_RETRIEVAL_TOP_K = int(os.environ.get("PROFILE_RETRIEVAL_TOP_K", 4))
    GITHUB_MCP_COMMAND = os.environ.get("GITHUB_MCP_COMMAND", "npx")
    GITHUB_MCP_ARGS = [
        arg for arg in os.environ.get("GITHUB_MCP_ARGS", "-y @modelcontextprotocol/server-github").split() if arg
    ]
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    GEMINI_API_BASE_URL = os.environ.get("GEMINI_API_BASE_URL", "https://generativelanguage.googleapis.com")

    @classmethod
    def get_gemini_api_key(cls) -> str | None:
        return os.environ.get("GEMINI_API_KEY") or cls.GEMINI_API_KEY

    @classmethod
    def get_gemini_model(cls) -> str:
        return os.environ.get("GEMINI_MODEL", cls.GEMINI_MODEL)

    @classmethod
    def get_gemini_api_base_url(cls) -> str:
        return os.environ.get("GEMINI_API_BASE_URL", cls.GEMINI_API_BASE_URL)

    @classmethod
    def get_github_token(cls) -> str:
        """Return the configured GitHub token for the GitHub MCP server."""
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
        if not token:
            raise ValueError(
                "GITHUB_TOKEN or GITHUB_PERSONAL_ACCESS_TOKEN must be set to use the GitHub MCP server."
            )
        return token

    @classmethod
    def get_github_mcp_server_params(cls):
        """Build the stdio server parameters for the GitHub MCP server."""
        from mcp import StdioServerParameters

        return StdioServerParameters(
            command=cls.GITHUB_MCP_COMMAND,
            args=cls.GITHUB_MCP_ARGS,
            env={
                **os.environ,
                "GITHUB_TOKEN": cls.get_github_token(),
            },
        )

    @classmethod
    def get_profile_source_paths(cls) -> dict[str, Path]:
        """Return the configured locations of the fixed profile source PDFs."""
        default_source_dir = Path(__file__).resolve().parents[2] / "data" / "profile_sources"
        source_dir = Path(os.environ.get("PROFILE_SOURCE_DIR", default_source_dir)).expanduser()

        return {
            "linkedin": Path(
                os.environ.get("PROFILE_LINKEDIN_PDF", source_dir / "linkedin_profile.pdf")
            ).expanduser().resolve(),
            "resume": Path(
                os.environ.get("PROFILE_RESUME_PDF", source_dir / "resume.pdf")
            ).expanduser().resolve(),
        }

    @classmethod
    def get_profile_mcp_allowed_hosts(cls) -> list[str]:
        """Resolve MCP host allowlisting from deployment-time environment values."""
        configured_hosts = os.environ.get("PROFILE_MCP_ALLOWED_HOSTS")
        if configured_hosts is None:
            configured_hosts = ",".join(
                filter(
                    None,
                    [
                        "localhost",
                        "localhost:*",
                        "127.0.0.1",
                        "127.0.0.1:*",
                        os.environ.get("SPACE_HOST"),
                    ],
                )
            )
        return [host.strip() for host in configured_hosts.split(",") if host.strip()]

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///dev.db')

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///test.db')

class ProductionConfig(Config):
    """Production configuration."""
    DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///prod.db')