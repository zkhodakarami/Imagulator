from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # add your envs with defaults
    API_PORT: int = 8000
    FW_API_KEY: str | None = None
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(
        env_file=".env",  # loads from repo-root .env if present
        extra="ignore",
    )

settings = Settings()