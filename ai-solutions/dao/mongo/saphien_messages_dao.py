# dao/mongo/v1/saphien_messages_dao.py
"""
DAO para mensagens do chat Saphien Widget.
Reutiliza a mesma estrutura do TelegramMessagesDAO.
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from loguru import logger

from core.config.database import get_mongo_db


class SaphienMessagesDAO:
    """DAO para mensagens do chat Saphien Widget"""

    _db = None
    _collection = None
    COLLECTION_NAME = "chat_messages"  # Mesma coleção do Telegram e Evolution

    @classmethod
    def _get_db(cls):
        if cls._db is None:
            cls._db = get_mongo_db()
        return cls._db

    @classmethod
    def _get_collection(cls):
        if cls._collection is None:
            cls._collection = cls._get_db()[cls.COLLECTION_NAME]
        return cls._collection

    # ---------------------------------------------------------------------
    # MÉTODOS PRINCIPAIS
    # ---------------------------------------------------------------------

    @classmethod
    def get_next_message_number(cls, session_id: str) -> int:
        """Obtém o próximo número de mensagem para uma sessão."""
        last_msg = cls._get_collection().find_one(
            {"session_id": session_id, "channel": "saphien"},
            sort=[("message_number", -1)]
        )
        return (last_msg["message_number"] + 1) if last_msg else 1

    @classmethod
    def save_message(
        cls, 
        session_id: str, 
        sender: str, 
        content: str, 
        role: str = None, 
        metadata: Dict = None
    ) -> Dict[str, Any]:
        """
        Salva uma mensagem associada à sessão.
        
        Args:
            session_id: ID da sessão (UUID)
            sender: ID do remetente (user_id ou agent_id)
            content: Conteúdo da mensagem
            role: "user" ou "assistant" (para compatibilidade)
            metadata: Metadados adicionais
        """
        message_number = cls.get_next_message_number(session_id)
        
        # Determina o role baseado no sender ou parâmetro
        if role:
            msg_role = role
        else:
            msg_role = "assistant" if (sender and (len(sender) == 36 or sender.startswith("68f"))) else "user"
        
        msg_doc = {
            "_id": str(uuid.uuid4()),
            "session_id": session_id,
            "sender": sender,
            "role": msg_role,
            "content": content,
            "created_at": datetime.utcnow(),
            "message_number": message_number,
            "channel": "saphien",  # Para diferenciar do Telegram e Evolution
        }
        
        if metadata:
            msg_doc["metadata"] = metadata
        
        cls._get_collection().insert_one(msg_doc)
        logger.debug(f"[SAPHIEN MSG] Mensagem salva: session={session_id}, num={message_number}, role={msg_role}")
        return msg_doc

    @classmethod
    def save_user_message(
        cls, 
        session_id: str, 
        user_id: str, 
        content: str, 
        metadata: Dict = None
    ) -> Dict[str, Any]:
        """Salva mensagem do usuário."""
        return cls.save_message(session_id, user_id, content, role="user", metadata=metadata)

    @classmethod
    def save_assistant_message(
        cls, 
        session_id: str, 
        agent_id: str, 
        content: str, 
        metadata: Dict = None
    ) -> Dict[str, Any]:
        """Salva mensagem do assistente (agente)."""
        return cls.save_message(session_id, agent_id, content, role="assistant", metadata=metadata)

    @classmethod
    def get_messages_by_session(cls, session_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """Retorna todas as mensagens de uma sessão (ordenadas por número)."""
        query = {"session_id": session_id, "channel": "saphien"}
        cursor = cls._get_collection().find(query).sort("message_number", 1)
        
        if limit:
            cursor = cursor.limit(limit)
        
        return list(cursor)

    @classmethod
    def get_conversation_history(cls, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retorna o histórico da conversa formatado para o agente.
        Formato: [{"role": "user", "content": "...", "timestamp": ...}, ...]
        """
        messages = cls.get_messages_by_session(session_id, limit=limit)
        
        history = []
        for msg in messages:
            history.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
                "timestamp": msg.get("created_at"),
            })
        
        return history

    @classmethod
    def delete_messages_by_session(cls, session_id: str) -> int:
        """Remove todas as mensagens associadas a uma sessão."""
        result = cls._get_collection().delete_many({"session_id": session_id, "channel": "saphien"})
        logger.info(f"[SAPHIEN MSG] {result.deleted_count} mensagens removidas da sessão {session_id}")
        return result.deleted_count

    @classmethod
    def get_last_message(cls, session_id: str) -> Optional[Dict[str, Any]]:
        """Retorna a última mensagem da sessão."""
        result = cls._get_collection().find_one(
            {"session_id": session_id, "channel": "saphien"},
            sort=[("message_number", -1)]
        )
        return result if result else None

    @classmethod
    def get_message_count(cls, session_id: str) -> int:
        """Retorna a quantidade de mensagens de uma sessão."""
        return cls._get_collection().count_documents({"session_id": session_id, "channel": "saphien"})