#core\config\database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine
from pymongo import MongoClient
from core.config.settings import settings
from contextlib import asynccontextmanager

# ---------------------------------------
# 📦 PostgreSQL - Async
# ---------------------------------------

async_engine = create_async_engine(
    settings.POSTGRES_URL,
    echo=False,
    future=True
)

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def get_postgres_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

@asynccontextmanager
async def get_postgres_db_context():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# ---------------------------------------
# 📦 PostgreSQL - Sync
# ---------------------------------------

sync_postgres_url = settings.POSTGRES_URL.replace("+asyncpg", "")

sync_engine = create_engine(
    sync_postgres_url,
    echo=False
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    expire_on_commit=False
)

def get_postgres_db_sync():
    session = SyncSessionLocal()
    try:
        return session
    except Exception:
        session.close()
        raise

# ---------------------------------------
# 🍃 MongoDB — Singleton Verdadeiro
# ---------------------------------------

_mongo_client = None
_mongo_db = None

def init_mongo_singleton():
    """Inicializa o MongoDB somente uma vez."""
    global _mongo_client, _mongo_db

    if _mongo_client:
        return _mongo_client, _mongo_db

    try:
        print(f"[DATABASE] Inicializando MongoDB")
        print(f"  URI = {settings.MONGO_URI}")
        print(f"  DB  = {settings.MONGO_DB_NAME}")

        _mongo_client = MongoClient(settings.MONGO_URI)
        _mongo_db = _mongo_client[settings.MONGO_DB_NAME]

        _mongo_client.admin.command("ping")
        print("[DATABASE] MongoDB conectado com sucesso")

    except Exception as e:
        print(f"[DATABASE] Erro ao conectar ao MongoDB: {e}")
        _mongo_client = None
        _mongo_db = None
        raise

    return _mongo_client, _mongo_db

def get_mongo_db():
    if _mongo_db is None:
        init_mongo_singleton()
    return _mongo_db

def get_mongo_client():
    if _mongo_client is None:
        init_mongo_singleton()
    return _mongo_client
