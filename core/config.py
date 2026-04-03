from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Optional metadata (if you still want them)
    DB_HOST: str
    DB_NAME: str
    DB_DRIVER: str

    # APIs
    OLLAMA_API_KEY: str
    GOOGLE_AI_KEY: str | None = None

    class Config:
        env_file = ".env"


settings = Settings()