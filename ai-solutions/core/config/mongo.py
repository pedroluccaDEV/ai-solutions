# core/config/mongo.py

from pymongo import MongoClient
from core.config.settings import settings


class MongoConnection:
    def __init__(self):
        self._client: MongoClient | None = None
        self._db = None

    def connect(self):
        if self._client is None:
            self._client = MongoClient(
                settings.MONGO_URI,
                maxPoolSize=50,
                minPoolSize=5,
                serverSelectionTimeoutMS=5000,
            )

            self._db = self._client[settings.MONGO_DB_NAME]
            self._client.admin.command("ping")

    def get_db(self):
        if self._db is None:
            self.connect()
        return self._db

    def get_client(self):
        if self._client is None:
            self.connect()
        return self._client

    def close(self):
        if self._client:
            self._client.close()


mongo_conn = MongoConnection()