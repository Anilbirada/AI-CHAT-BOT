from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DSCE AI Academic Assistant"
    database_url: str = Field(
        default="sqlite:///./database.db",
        validation_alias=AliasChoices("DATABASE_URL", "database_url"),
    )
    jwt_secret: str = Field(
        default="change-me-in-production",
        validation_alias=AliasChoices("JWT_SECRET", "jwt_secret"),
    )
    jwt_algorithm: str = Field(
        default="HS256",
        validation_alias=AliasChoices("JWT_ALGORITHM", "jwt_algorithm"),
    )
    access_token_minutes: int = Field(
        default=480,
        validation_alias=AliasChoices("ACCESS_TOKEN_MINUTES", "access_token_minutes"),
    )
    storage_path: str = Field(
        default="storage/uploads",
        validation_alias=AliasChoices("STORAGE_PATH", "storage_path"),
    )
    llm_provider: str = Field(
        default="openai",
        validation_alias=AliasChoices("LLM_PROVIDER", "llm_provider"),
    )
    llm_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("LLM_API_KEY", "llm_api_key"),
    )
    llm_base_url: str = Field(
        default="",
        validation_alias=AliasChoices("LLM_BASE_URL", "llm_base_url"),
    )
    llm_model: str = Field(
        default="gpt-4o-mini",
        validation_alias=AliasChoices("LLM_MODEL", "llm_model"),
    )
    llm_temperature: float = Field(
        default=0.2,
        validation_alias=AliasChoices("LLM_TEMPERATURE", "llm_temperature"),
    )
    llm_max_tokens: int = Field(
        default=500,
        validation_alias=AliasChoices("LLM_MAX_TOKENS", "llm_max_tokens"),
    )
    llm_timeout: float = Field(
        default=60.0,
        validation_alias=AliasChoices("LLM_TIMEOUT", "llm_timeout"),
    )
    llm_stream: bool = Field(
        default=True,
        validation_alias=AliasChoices("LLM_STREAM", "llm_stream"),
    )
    embedding_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("EMBEDDING_API_KEY", "embedding_api_key"),
    )
    vector_db_url: str = Field(
        default="",
        validation_alias=AliasChoices("VECTOR_DB_URL", "vector_db_url"),
    )
    cors_origins: str = Field(
        default="http://localhost:5173",
        validation_alias=AliasChoices("CORS_ORIGINS", "cors_origins"),
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)


settings = Settings()
