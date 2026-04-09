import pkgutil
import importlib
import inspect
from pathlib import Path
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import text
from core.config.settings import settings
from models.mongo.base import MongoModel

import models.postgres.subscription_plan_model
import models.postgres.user_subscription_model
import models.postgres.user_credits_model
import models.postgres.credit_transaction_model
import models.postgres.user_model
import models.postgres.organization_model
import models.postgres.faq_model
import models.postgres.contact_message_model
import models.postgres.project_model
import models.postgres.invite_model
import models.postgres.preference_model
import models.postgres.llm_model
import models.postgres.token_models

from core.config.init_faq_data import initialize_faq_data

from dao.postgres.v1.subscription_plan_dao import SubscriptionPlanDAO
from models.postgres.subscription_plan_model import SubscriptionPlan

from scripts.export.database.mongo.sync_defaults import sync_defaults

from core.config.database import (
    get_mongo_client,
    get_mongo_db,
    init_mongo_singleton
)

import asyncio

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

# ---------------------------------------
# 🚀 Inicialização geral
# ---------------------------------------

async def init_db():
    # 🔥 Garante que o Mongo está sempre inicializado antes de qualquer coisa
    init_mongo_singleton()

    # ------------------------------
    # Criar tabelas no PostgreSQL
    # ------------------------------
    try:
        async with async_engine.begin() as conn:
            await conn.execute(text("DROP TABLE IF EXISTS faq_feedback CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS faqs CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS faq_categories CASCADE"))

            await conn.run_sync(SQLModel.metadata.create_all)

        print("[OK] Tabelas do PostgreSQL criadas")

        async for db_session in get_postgres_db():
            await initialize_faq_data(db_session)
    except Exception as e:
        print(f"[WARN] PostgreSQL não disponível: {e}")

    # ------------------------------
    # Criar coleções no MongoDB
    # ------------------------------
    await init_mongo_collections()

async def init_mongo_collections():
    print("[INFO] Registrando coleções no MongoDB...")

    required = [
        "agents",
        "chat_sessions",
        "chat_messages",
        "channels",
        "knowledge_bases",
        "memories",
        "memory_chat",
        "memory_user",
        "teams",
        "tool_config",
        "tools",
        "mcp_servers",
        "mcp_connections",
        "skill_workflow"
    ]

    db = get_mongo_db()
    existing = db.list_collection_names()

    for col in required:
        if col not in existing:
            db.create_collection(col)
            print(f"[OK] Criada coleção: {col}")

            if col == "memory_user":
                db[col].create_index([("user_id", 1), ("last_updated", -1)])
                db[col].create_index([("user_id", 1), ("topics", 1)])

            if col == "memory_chat":
                db[col].create_index([("session_id", 1), ("timestamp", -1)])
        else:
            print(f"[INFO] Coleção já existe: {col}")

    # Sync defaults
    try:
        sync_defaults(db)
    except Exception as e:
        print(f"[WARN] Erro ao sincronizar dados padrão: {e}")

# ---------------------------------------
# 🧠 Planos padrão
# ---------------------------------------

DEFAULT_PLANS = [
    {
        "name": "gratuito",
        "display_name": "Base",
        "monthly_credits": 500,
        "monthly_price": 0,
        "annual_price": 0
    },
    {
        "name": "plus",
        "display_name": "Intermediário",
        "monthly_credits": 1000,
        "monthly_price": 10000,
        "annual_price": 8500
    },
    {
        "name": "pro",
        "display_name": "Avançado",
        "monthly_credits": 3000,
        "monthly_price": 30000,
        "annual_price": 25000
    }
]

async def initialize_plans():
    async for db in get_postgres_db():
        try:
            for plan_data in DEFAULT_PLANS:
                existing = await SubscriptionPlanDAO.get_by_name(db, plan_data["name"])
                if not existing:
                    await SubscriptionPlanDAO.create(db, SubscriptionPlan(**plan_data))

            await db.commit()
        except Exception:
            await db.rollback()
            raise
        finally:
            await db.close()

# ---------------------------------------
# Execução direta
# ---------------------------------------

if __name__ == "__main__":
    asyncio.run(init_db())
