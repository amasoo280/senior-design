from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    USE_V2_CONFIG = True
except ImportError:
    from pydantic import BaseSettings
    USE_V2_CONFIG = False

# Load .env from backend directory so it works regardless of cwd
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_ENV_FILE = _BACKEND_DIR / ".env"

if USE_V2_CONFIG:
    # =============================
    # Pydantic v2 Settings
    # =============================
    class Settings(BaseSettings):
        model_config = SettingsConfigDict(
            env_file=str(_ENV_FILE) if _ENV_FILE.exists() else ".env",
            env_file_encoding="utf-8",
            extra="allow"
        )

        # -----------------------------
        # Database Settings
        # -----------------------------
        db_host: str = Field(..., env="DB_HOST")
        db_port: int = Field(3306, env="DB_PORT")
        db_user: str = Field(..., env="DB_USER")
        db_password: str = Field(..., env="DB_PASSWORD")
        db_name: str = Field(..., env="DB_NAME")
        db_query_timeout_seconds: int = Field(30, env="DB_QUERY_TIMEOUT_SECONDS")

        # -----------------------------
        # AWS / Bedrock Settings
        # -----------------------------
        aws_access_key_id: str | None = Field(None, env="AWS_ACCESS_KEY_ID")
        aws_secret_access_key: str | None = Field(None, env="AWS_SECRET_ACCESS_KEY")
        aws_region: str | None = Field("us-east-1", env="AWS_REGION")

        # IMPORTANT:
        # Never hardcode the model ID — ALWAYS read from .env
        # The .env should contain the *inference profile ID* now.
        bedrock_model_id: str | None = Field(None, env="BEDROCK_MODEL_ID")

        # Optional tenant
        default_tenant_id: str | None = Field(None, env="DEFAULT_TENANT_ID")

        # Logging configuration
        log_level: str = Field("INFO", env="LOG_LEVEL")

        # Authentication (simple username/password)
        auth_username: str = Field("admin", env="AUTH_USERNAME")
        auth_password: str = Field("admin", env="AUTH_PASSWORD")


else:
    # =============================
    # Pydantic v1 Settings
    # =============================
    class Settings(BaseSettings):
        class Config:
            env_file = str(_ENV_FILE) if _ENV_FILE.exists() else ".env"
            env_file_encoding = "utf-8"
            extra = "allow"

        # -----------------------------
        # Database
        # -----------------------------
        db_host: str
        db_port: int = 3306
        db_user: str
        db_password: str
        db_name: str
        db_query_timeout_seconds: int = 30

        # -----------------------------
        # AWS
        # -----------------------------
        aws_access_key_id: str | None = None
        aws_secret_access_key: str | None = None
        aws_region: str | None = "us-east-1"

        # Again, do NOT hardcode — allow .env to override
        bedrock_model_id: str | None = Field(None, env="BEDROCK_MODEL_ID")


        default_tenant_id: str | None = None

        # Logging configuration
        log_level: str = "INFO"

        # Authentication (simple username/password)
        auth_username: str = "admin"
        auth_password: str = "admin"


settings = Settings()

# Startup diagnostic: see exactly what was loaded (helps debug wrong model ID)
def _config_diagnostic() -> None:
    import os
    env_path = str(_ENV_FILE) if _ENV_FILE.exists() else ".env"
    os_val = os.environ.get("BEDROCK_MODEL_ID")
    print(
        "[CONFIG] .env path:",
        _ENV_FILE,
        "| exists:",
        _ENV_FILE.exists(),
        "| os.environ BEDROCK_MODEL_ID:",
        repr(os_val) if os_val is not None else "<not set>",
        "| settings.bedrock_model_id:",
        repr(settings.bedrock_model_id),
        flush=True,
    )

_config_diagnostic()
