from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    USE_V2_CONFIG = True
except ImportError:
    from pydantic import BaseSettings
    USE_V2_CONFIG = False


if USE_V2_CONFIG:
    # =============================
    # Pydantic v2 Settings
    # =============================
    class Settings(BaseSettings):
        model_config = SettingsConfigDict(
            env_file=".env",
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

        # Google OAuth Configuration
        google_client_id: str = Field(..., env="GOOGLE_CLIENT_ID")
        google_client_secret: str = Field(..., env="GOOGLE_CLIENT_SECRET")
        
        # JWT Configuration
        jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
        jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
        jwt_expiration_hours: int = Field(24, env="JWT_EXPIRATION_HOURS")
        
        # Frontend URL for OAuth redirects
        frontend_url: str = Field("http://localhost:5173", env="FRONTEND_URL")
        
        # Admin emails (comma-separated list)
        admin_emails_raw: str | None = Field(None, env="ADMIN_EMAILS")
        
        @property
        def admin_emails(self) -> list[str]:
            """Parse admin emails from comma-separated string."""
            if not self.admin_emails_raw:
                return []
            return [email.strip() for email in self.admin_emails_raw.split(',') if email.strip()]


else:
    # =============================
    # Pydantic v1 Settings
    # =============================
    class Settings(BaseSettings):
        class Config:
            env_file = ".env"
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

        # Google OAuth Configuration
        google_client_id: str
        google_client_secret: str
        
        # JWT Configuration
        jwt_secret_key: str
        jwt_algorithm: str = "HS256"
        jwt_expiration_hours: int = 24
        
        # Frontend URL
        frontend_url: str = "http://localhost:5173"
        
        # Admin emails
        admin_emails_raw: str | None = None
        
        @property
        def admin_emails(self) -> list[str]:
            """Parse admin emails from comma-separated string."""
            if not self.admin_emails_raw:
                return []
            return [email.strip() for email in self.admin_emails_raw.split(',') if email.strip()]


settings = Settings()
