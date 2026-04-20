# core/config/init_db.py

from core.config.database import db_manager
from core.database.mongo_sync import sync_mongo


async def init_db():
    db_manager.init()
    
    sync_mongo() # Sincronizar models com mongo ao inicializar

    db = db_manager.get_mongo()

    required = [
        "agents",
        "chat_sessions",
        "chat_messages",
        "memory_user",
        "memory_chat",
    ]

    existing = db.list_collection_names()

    for col in required:
        if col not in existing:
            db.create_collection(col)

            if col == "memory_user":
                db[col].create_index([("user_id", 1), ("last_updated", -1)])

            if col == "memory_chat":
                db[col].create_index([("session_id", 1), ("timestamp", -1)])