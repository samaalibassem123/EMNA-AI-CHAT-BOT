from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    DATABASE_URL: str               # Async SQL Server URL (mssql+aioodbc://...)

    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_DRIVER: str                  # e.g., ODBC+Driver+18+for+SQL+Server

  
    # Ollama for cloud service
    OLLAMA_API_KEY:str

    # GOOGLE Ai key
    GOOGLE_AI_KEY:str

    class Config:
        env_file = ".env"

settings = Settings()


