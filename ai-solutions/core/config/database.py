# core/config/database.py

from core.config.mongo import mongo_conn

class DatabaseManager:
    def __init__(self):
        self._initialized = False

    def init(self):
        if self._initialized:
            return

        # 🔥 inicializa tudo aqui
        mongo_conn.connect()

        # futuro:
        # supabase_conn.connect()

        self._initialized = True
        print("[DatabaseManager] Inicializado")

    def get_mongo(self):
        return mongo_conn.get_db()

    def close(self):
        mongo_conn.close()


db_manager = DatabaseManager()