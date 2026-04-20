# core/database/mongo_sync.py

from core.config.database import db_manager
from core.database.mongo_model_loader import load_mongo_models


def sync_mongo():
    db = db_manager.get_mongo()

    models = load_mongo_models()
    existing_collections = db.list_collection_names()

    for model in models:
        name = model.collection_name()

        # 📦 cria coleção
        if name not in existing_collections:
            db.create_collection(name)
            print(f"[Mongo] Criada coleção: {name}")
        else:
            print(f"[Mongo] Coleção já existe: {name}")

        # ⚡ índices
        for index in model.get_indexes():
            db[name].create_index(index)
            print(f"[Mongo] Index aplicado em {name}: {index}")