from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str
    PROJECT_DESCRIPTION: str
    VERSION: str
    API_PREFIX: str
    HOST: str
    PORT: int

    # Banco de dados
    POSTGRES_URL: str
    MONGO_DB_NAME: str
    MONGO_URI: str

    # Firebase
    GOOGLE_APPLICATION_CREDENTIALS: str
    FIREBASE_API_KEY: str
    FIREBASE_AUTH_DOMAIN: str
    FIREBASE_PROJECT_ID: str
    FIREBASE_STORAGE_BUCKET: str
    FIREBASE_MSG_SENDER_ID: str
    FIREBASE_APP_ID: str

    # Contexto e histórico
    MAX_CONTEXT_TOKENS: int
    MAX_HISTORY_RESPONSES: int

    # APIs externas
    OPENROUTER_API_KEY: str
    OPENROUTER_BASE_URL: str
    DEEPSEEK_API_KEY: str
    DEEPSEEK_BASE_URL: str
    OPENAI_API_KEY: str
    FIRECRAWL_API_KEY: str
    ANTHROPIC_API_KEY: Optional[str] = None

    # Usuário e logging
    USER_ID: str
    LOG_LEVEL: str = "INFO"
    REQUESTS_CA_BUNDLE: Optional[str] = None
    API_BASE_URL: str
    VITE_API_BASE_URL: Optional[str] = None

    # Desenvolvimento
    DEV_USER_UID: Optional[str] = None
    DEV_USER_EMAIL: Optional[str] = None
    DEV_USER_NAME: Optional[str] = None
    DEV_USER_SURNAME: Optional[str] = None
    DEV_USER_BIRTHDATE: Optional[str] = None

    # Chroma
    CHROMA_URL: str
    CHROMA_AUTH: str

    # Evolution API
    EVOLUTION_BASE_URL: str = "https://evolution-api-development-db11.up.railway.app"
    EVOLUTION_API_KEY: str
    EVOLUTION_WEBHOOK_PATH: str = "/api/v1/evolution/webhook"
    PUBLIC_API_URL: str = "http://localhost:8000"

    TRIGGER_SECRET_KEY: str = "default-trigger-key"

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }


settings = Settings()
