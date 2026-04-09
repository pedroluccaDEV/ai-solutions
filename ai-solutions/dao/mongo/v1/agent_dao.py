from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId
from schemas.v1.agent_schema import AgentCreateSchema
from core.config.database import get_mongo_db

class AgentDAO:
    _db = None
    _agents_collection = None

    @classmethod
    def _get_db(cls):
        if cls._db is None:
            cls._db = get_mongo_db()
        return cls._db

    @classmethod
    def _get_agents_collection(cls):
        if cls._agents_collection is None:
            cls._agents_collection = cls._get_db().agents
        return cls._agents_collection

    @staticmethod
    def _serialize_document(doc: dict) -> dict:
        if not doc:
            return doc
        result = doc.copy()
        if "_id" in result and isinstance(result["_id"], ObjectId):
            result["_id"] = str(result["_id"])
        for field in ["knowledgeBase", "tools", "mcps"]:
            if field in result and isinstance(result[field], list):
                result[field] = [
                    str(item) if isinstance(item, ObjectId) else item
                    for item in result[field]
                ]
        return result

    # ---------------------------
    # GET POR ID COM VERIFICAÇÃO DE USUÁRIO
    # ---------------------------
    @classmethod
    def get_agent_by_id_and_user(cls, agent_id: str, uid: str) -> Optional[dict]:
        try:
            obj_id = ObjectId(agent_id)
        except InvalidId:
            return None

        collection = cls._get_agents_collection()
        agent = collection.find_one({"_id": obj_id, "uid": uid})
        return cls._serialize_document(agent) if agent else None

    # ---------------------------
    # GET APENAS POR ID (SEM UID) - para uso público
    # ---------------------------
    @classmethod
    def get_agent_by_id(cls, agent_id: str) -> Optional[dict]:
        try:
            obj_id = ObjectId(agent_id)
        except InvalidId:
            return None

        collection = cls._get_agents_collection()
        agent = collection.find_one({"_id": obj_id})
        return cls._serialize_document(agent) if agent else None

    @classmethod
    def create_agent(cls, agent_data: AgentCreateSchema, uid: str) -> dict:
        if not uid:
            raise ValueError("UID ausente ao criar agente")
        data = agent_data.dict(exclude_unset=True)
        now = datetime.utcnow()

        data["uid"] = uid
        data["createdAt"] = now
        data["updatedAt"] = now
        data["knowledgeBase"] = data.get("knowledgeBase") or []
        data["tools"] = data.get("tools") or []
        data["mcps"] = data.get("mcps") or []
        data["isClone"] = data.get("isClone", False)
        data["status"] = data.get("status", "active")

        collection = cls._get_agents_collection()
        result = collection.insert_one(data)
        created_agent = collection.find_one({"_id": result.inserted_id})
        return cls._serialize_document(created_agent)

    @classmethod
    def update_agent(cls, agent_id: str, agent_data: AgentCreateSchema, uid: str) -> Optional[dict]:
        try:
            obj_id = ObjectId(agent_id)
        except InvalidId:
            return None

        data = agent_data.dict(exclude_unset=True)
        data["updatedAt"] = datetime.utcnow()
        data["uid"] = uid
        data["knowledgeBase"] = data.get("knowledgeBase") or []
        data["tools"] = data.get("tools") or []
        data["mcps"] = data.get("mcps") or []
        data["isClone"] = data.get("isClone", False)

        collection = cls._get_agents_collection()
        result = collection.update_one(
            {"_id": obj_id, "uid": uid},  # <-- ADICIONADO VERIFICAÇÃO DE USUÁRIO
            {"$set": data}
        )

        if result.matched_count == 0:
            return None

        updated_agent = collection.find_one({"_id": obj_id})
        return cls._serialize_document(updated_agent)

    @classmethod
    def list_agents_by_user(cls, uid: str) -> List[dict]:
        collection = cls._get_agents_collection()
        cursor = collection.find({"uid": uid}).sort("updatedAt", -1)
        return [cls._serialize_document(a) for a in cursor]

    @classmethod
    def list_public_agents(cls) -> List[dict]:
        collection = cls._get_agents_collection()
        cursor = collection.find({"visibility": "public"}).sort("updatedAt", -1)
        return [cls._serialize_document(a) for a in cursor]

    @classmethod
    def delete_agent(cls, agent_id: str, uid: str) -> bool:
        try:
            obj_id = ObjectId(agent_id)
        except InvalidId:
            return False
        result = cls._get_agents_collection().update_one(
            {"_id": obj_id, "uid": uid},
            {"$set": {"status": "inactive", "updatedAt": datetime.utcnow()}}
        )
        return result.matched_count > 0

    @classmethod
    def list_agents_raw_by_user(cls, uid: str) -> List[dict]:
        collection = cls._get_agents_collection()
        cursor = collection.find({"uid": uid})
        return [cls._serialize_document(a) for a in cursor]