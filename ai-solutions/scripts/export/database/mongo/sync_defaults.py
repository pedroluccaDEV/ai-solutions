from pymongo.database import Database
from scripts.export.database.mongo.default_mcps import DEFAULT_MCPS
from scripts.export.database.mongo.default_tools import DEFAULT_TOOLS

def sync_defaults(mongo_db: Database):
    print("[INFO] Sincronizando coleções default (mcps, tools)...")

    _sync_collection(mongo_db, "mcp_servers", DEFAULT_MCPS, unique_field="name")
    _sync_collection(mongo_db, "tools", DEFAULT_TOOLS, unique_field="name")

def _sync_collection(mongo_db: Database, collection_name: str, defaults: list[dict], unique_field: str):
    collection = mongo_db[collection_name]

    for item in defaults:
        query = {unique_field: item[unique_field]}
        existing = collection.find_one(query)

        if existing:
            collection.update_one(query, {"$set": item})
            print(f"[UPDATE] {collection_name} -> {item[unique_field]}")
        else:
            collection.insert_one(item)
            print(f"[INSERT] {collection_name} -> {item[unique_field]}")
