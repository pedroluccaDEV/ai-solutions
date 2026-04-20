from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId

from schemas.agent_schema import AgentCreateSchema
from core.config.database import db_manager


class AgentDAO:
    def __init__(self):
        self.collection = db_manager.get_mongo()["agents"]

    # ---------------------------
    # Utils
    # ---------------------------

    @staticmethod
    def _serialize(doc: dict) -> dict:
        if not doc:
            return doc

        doc["_id"] = str(doc["_id"])

        for field in ["knowledgeBase", "tools", "mcps"]:
            if field in doc:
                doc[field] = [
                    str(i) if isinstance(i, ObjectId) else i
                    for i in doc[field]
                ]

        return doc

    @staticmethod
    def _to_object_id(id_str: str) -> Optional[ObjectId]:
        try:
            return ObjectId(id_str)
        except InvalidId:
            return None

    # ---------------------------
    # Reads
    # ---------------------------

    def get_by_id(self, agent_id: str, uid: Optional[str] = None) -> Optional[dict]:
        obj_id = self._to_object_id(agent_id)
        if not obj_id:
            return None

        query = {"_id": obj_id}
        if uid:
            query["uid"] = uid

        doc = self.collection.find_one(query)
        return self._serialize(doc) if doc else None

    def list_by_user(self, uid: str) -> List[dict]:
        cursor = self.collection.find({"uid": uid}).sort("updatedAt", -1)
        return [self._serialize(doc) for doc in cursor]

    def list_public(self) -> List[dict]:
        cursor = self.collection.find({"visibility": "public"}).sort("updatedAt", -1)
        return [self._serialize(doc) for doc in cursor]

    # ---------------------------
    # Writes
    # ---------------------------

    def create(self, data: AgentCreateSchema, uid: str) -> dict:
        payload = data.dict(exclude_unset=True)

        now = datetime.utcnow()

        payload.update({
            "uid": uid,
            "createdAt": now,
            "updatedAt": now,
        })

        result = self.collection.insert_one(payload)
        doc = self.collection.find_one({"_id": result.inserted_id})

        return self._serialize(doc)

    def update(self, agent_id: str, data: AgentCreateSchema, uid: str) -> Optional[dict]:
        obj_id = self._to_object_id(agent_id)
        if not obj_id:
            return None

        payload = data.dict(exclude_unset=True)
        payload["updatedAt"] = datetime.utcnow()

        result = self.collection.update_one(
            {"_id": obj_id, "uid": uid},
            {"$set": payload}
        )

        if result.matched_count == 0:
            return None

        doc = self.collection.find_one({"_id": obj_id})
        return self._serialize(doc)

    def delete(self, agent_id: str, uid: str) -> bool:
        obj_id = self._to_object_id(agent_id)
        if not obj_id:
            return False

        result = self.collection.update_one(
            {"_id": obj_id, "uid": uid},
            {
                "$set": {
                    "status": "inactive",
                    "updatedAt": datetime.utcnow()
                }
            }
        )

        return result.matched_count > 0