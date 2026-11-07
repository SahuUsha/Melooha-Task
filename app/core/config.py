
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str

    # LLM keys - keep these for answer generation
    GEMINI_API_KEY: str
    GROQ_API_KEY: str | None = None

    # Hugging Face hosted embedding API
    HF_TOKEN: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()
