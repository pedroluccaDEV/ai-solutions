# dao/mongo/v1/saphien_session_dao.py
"""
DAO para gerenciamento de sessões do Saphien Widget.
Formato compatível com chat_sessions collection (mesma do Telegram).
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from bson import ObjectId
from loguru import logger
import uuid

from core.config.database import get_mongo_db


class SaphienSessionDAO:
    _db = None
    _sessions_collection = None

    @classmethod
    def _get_db(cls):
        if cls._db is None:
            cls._db = get_mongo_db()
        return cls._db

    @classmethod
    def _get_collection(cls):
        if cls._sessions_collection is None:
            cls._sessions_collection = cls._get_db().chat_sessions
        return cls._sessions_collection

    @staticmethod
    def _serialize_document(doc: dict) -> dict:
        """Serializa ObjectId para string."""
        if not doc:
            return doc
        if "_id" in doc and isinstance(doc["_id"], ObjectId):
            doc["_id"] = str(doc["_id"])
        return doc

    # =====================================================
    # CRUD DE SESSÕES
    # =====================================================

    @classmethod
    def find_session(cls, widget_token: str, session_id: str) -> Optional[dict]:
        """
        Busca sessão existente por widget_token e session_id.
        """
        collection = cls._get_collection()
        session = collection.find_one({
            "widget_token": widget_token,
            "session_id": session_id,
            "type": "saphien"
        })
        return cls._serialize_document(session)

    @classmethod
    def find_session_by_id(cls, session_uuid: str) -> Optional[dict]:
        """Busca sessão pelo UUID (campo _id)."""
        collection = cls._get_collection()
        session = collection.find_one({"_id": session_uuid})
        return cls._serialize_document(session)

    @classmethod
    def find_sessions_by_widget(cls, widget_token: str, limit: int = 100, skip: int = 0) -> List[dict]:
        """Busca todas as sessões de um widget."""
        collection = cls._get_collection()
        cursor = collection.find({
            "widget_token": widget_token,
            "type": "saphien"
        }).sort("last_activity", -1).skip(skip).limit(limit)
        
        return [cls._serialize_document(session) for session in cursor]

    @classmethod
    def create_session(
        cls,
        widget_token: str,
        session_id: str,
        user_info: Dict[str, Any] = None,
        agents: List[Dict] = None,
        active_agent_id: str = None,
        active_agent_trigger: str = None,
    ) -> dict:
        """
        Cria uma nova sessão para um widget específico.
        
        Formato:
        {
            "_id": "uuid",
            "widget_token": "sw_xxx",
            "session_id": "session-uuid-from-frontend",
            "user_info": {
                "url": "https://...",
                "user_agent": "...",
                "ip": "..."
            },
            "active_agent": {
                "id": "agent_id",
                "trigger": "@a"
            },
            "agents": [...],
            "createdAt": datetime,
            "updatedAt": datetime,
            "last_activity": datetime,
            "type": "saphien"
        }
        """
        collection = cls._get_collection()
        
        now = datetime.utcnow()
        session_uuid = str(uuid.uuid4())
        
        session = {
            "_id": session_uuid,
            "widget_token": widget_token,
            "session_id": session_id,
            "type": "saphien",
            "createdAt": now,
            "updatedAt": now,
            "last_activity": now,
        }
        
        # Adiciona user_info se fornecido
        if user_info:
            session["user_info"] = user_info
        
        # Adiciona lista de agentes se fornecida
        if agents:
            cleaned_agents = []
            for agent in agents:
                cleaned_agent = {
                    "id": agent.get("id"),
                    "name": agent.get("name"),
                    "status": agent.get("status", "active"),
                    "trigger_config": agent.get("trigger_config", {}),
                    "priority": agent.get("priority", 0),
                    "created_at": agent.get("created_at", now),
                    "last_used": agent.get("last_used"),
                }
                cleaned_agents.append(cleaned_agent)
            session["agents"] = cleaned_agents
        
        # Adiciona active_agent se fornecido
        if active_agent_id:
            session["active_agent"] = {
                "id": active_agent_id,
                "trigger": active_agent_trigger or "",
            }
        
        collection.insert_one(session)
        
        logger.info(f"[SAPHIEN SESSION] Nova sessão criada: {widget_token[:15]}.../{session_id} (UUID: {session_uuid})")
        return cls._serialize_document(session)

    @classmethod
    def update_active_agent(
        cls, 
        session_uuid: str, 
        agent_id: str, 
        trigger: str = None
    ) -> bool:
        """
        Atualiza o agente ativo da sessão.
        """
        collection = cls._get_collection()
        
        update_data = {
            "active_agent": {
                "id": agent_id,
                "trigger": trigger or "",
            },
            "updatedAt": datetime.utcnow(),
        }
        
        result = collection.update_one(
            {"_id": session_uuid},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            logger.info(f"[SAPHIEN SESSION] Active agent atualizado: {session_uuid} → {agent_id}")
        
        return result.modified_count > 0

    @classmethod
    def update_agent_last_used(
        cls,
        session_uuid: str,
        agent_id: str,
    ) -> bool:
        """
        Atualiza o timestamp last_used de um agente na lista.
        """
        collection = cls._get_collection()
        now = datetime.utcnow()
        
        result = collection.update_one(
            {"_id": session_uuid, "agents.id": agent_id},
            {"$set": {
                "agents.$.last_used": now,
                "updatedAt": now,
            }}
        )
        
        return result.modified_count > 0

    @classmethod
    def update_last_activity(cls, session_uuid: str) -> bool:
        """Atualiza o timestamp da última atividade."""
        collection = cls._get_collection()
        now = datetime.utcnow()
        
        result = collection.update_one(
            {"_id": session_uuid},
            {"$set": {"last_activity": now, "updatedAt": now}}
        )
        
        return result.modified_count > 0

    @classmethod
    def get_active_agent(cls, session_uuid: str) -> Optional[Dict]:
        """Retorna o agente ativo da sessão."""
        collection = cls._get_collection()
        session = collection.find_one({"_id": session_uuid})
        
        if not session:
            return None
        
        active = session.get("active_agent")
        if not active:
            return None
        
        # Busca o agente completo na lista
        agent_id = active.get("id")
        for agent in session.get("agents", []):
            if agent.get("id") == agent_id:
                return agent
        
        return None

    @classmethod
    def get_session_agents(cls, session_uuid: str) -> List[Dict]:
        """Retorna a lista de agentes da sessão."""
        collection = cls._get_collection()
        session = collection.find_one({"_id": session_uuid})
        
        if not session:
            return []
        
        return session.get("agents", [])

    @classmethod
    def get_session_info(cls, session_uuid: str) -> Optional[Dict]:
        """Retorna informações básicas da sessão."""
        collection = cls._get_collection()
        session = collection.find_one(
            {"_id": session_uuid},
            {"_id": 1, "widget_token": 1, "session_id": 1, "type": 1, "createdAt": 1, "last_activity": 1}
        )
        return cls._serialize_document(session)

    @classmethod
    def sync_agents_from_channel(
        cls,
        widget_token: str,
        session_id: str,
        channel_agents: List[Dict],
    ) -> bool:
        """
        Sincroniza a lista de agentes do canal com a sessão.
        Útil quando o canal é atualizado.
        """
        collection = cls._get_collection()
        
        # Limpa os agentes para o formato da sessão
        cleaned_agents = []
        now = datetime.utcnow()
        
        for agent in channel_agents:
            cleaned_agent = {
                "id": agent.get("id"),
                "name": agent.get("name"),
                "status": agent.get("status", "active"),
                "trigger_config": agent.get("trigger_config", {}),
                "priority": agent.get("priority", 0),
                "created_at": agent.get("created_at", now),
                "last_used": agent.get("last_used"),
            }
            cleaned_agents.append(cleaned_agent)
        
        result = collection.update_one(
            {
                "widget_token": widget_token,
                "session_id": session_id,
                "type": "saphien"
            },
            {
                "$set": {
                    "agents": cleaned_agents,
                    "updatedAt": now,
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"[SAPHIEN SESSION] Agentes sincronizados: {widget_token[:15]}.../{session_id}")
        
        return result.modified_count > 0

    @classmethod
    def delete_session(cls, widget_token: str, session_id: str) -> bool:
        """Remove uma sessão."""
        collection = cls._get_collection()
        
        result = collection.delete_one({
            "widget_token": widget_token,
            "session_id": session_id,
            "type": "saphien"
        })
        
        if result.deleted_count > 0:
            logger.info(f"[SAPHIEN SESSION] Sessão removida: {widget_token[:15]}.../{session_id}")
        
        return result.deleted_count > 0

    @classmethod
    def delete_session_by_uuid(cls, session_uuid: str) -> bool:
        """Remove uma sessão pelo UUID."""
        collection = cls._get_collection()
        
        result = collection.delete_one({"_id": session_uuid})
        
        if result.deleted_count > 0:
            logger.info(f"[SAPHIEN SESSION] Sessão removida: {session_uuid}")
        
        return result.deleted_count > 0

    @classmethod
    def count_sessions_by_widget(cls, widget_token: str) -> int:
        """Conta o número de sessões de um widget."""
        collection = cls._get_collection()
        
        return collection.count_documents({
            "widget_token": widget_token,
            "type": "saphien"
        })

    @classmethod
    def delete_old_sessions(cls, days: int = 30) -> int:
        """Remove sessões inativas há mais de X dias."""
        collection = cls._get_collection()
        cutoff_date = datetime.utcnow()
        from datetime import timedelta
        cutoff_date = cutoff_date - timedelta(days=days)
        
        result = collection.delete_many({
            "type": "saphien",
            "last_activity": {"$lt": cutoff_date}
        })
        
        if result.deleted_count > 0:
            logger.info(f"[SAPHIEN SESSION] {result.deleted_count} sessões antigas removidas (>{days} dias)")
        
        return result.deleted_count