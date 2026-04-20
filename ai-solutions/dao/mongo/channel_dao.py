# dao/mongo/v1/channel_dao.py
"""
DAO Genérico para gerenciamento de canais (Evolution, Telegram, Discord, etc.)
"""
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId
from loguru import logger

from core.config.database import get_mongo_db


class ChannelDAO:
    _db = None
    _channels_collection = None

    @classmethod
    def _get_db(cls):
        if cls._db is None:
            cls._db = get_mongo_db()
        return cls._db

    @classmethod
    def _get_collection(cls):
        if cls._channels_collection is None:
            cls._channels_collection = cls._get_db().channels
        return cls._channels_collection

    @staticmethod
    def _serialize_objectid(obj: Any) -> Any:
        """Serializa recursivamente ObjectId para string."""
        if isinstance(obj, ObjectId):
            return str(obj)
        elif isinstance(obj, dict):
            return {k: ChannelDAO._serialize_objectid(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [ChannelDAO._serialize_objectid(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(ChannelDAO._serialize_objectid(item) for item in obj)
        else:
            return obj

    @staticmethod
    def _serialize_document(doc: dict) -> dict:
        """Serializa ObjectId e outros campos para JSON."""
        if not doc:
            return doc
        return ChannelDAO._serialize_objectid(doc)

    # =====================================================
    # GET POR ID COM VERIFICAÇÃO DE USUÁRIO
    # =====================================================
    
    @classmethod
    def get_channel_by_id_and_user(cls, channel_id: str, user_id: str) -> Optional[dict]:
        """Busca canal por ID verificando o usuário."""
        try:
            obj_id = ObjectId(channel_id)
        except InvalidId:
            return None

        collection = cls._get_collection()
        channel = collection.find_one({"_id": obj_id, "user_id": user_id})
        return cls._serialize_document(channel) if channel else None

    # =====================================================
    # GET APENAS POR ID (SEM USER_ID)
    # =====================================================
    
    @classmethod
    def get_channel_by_id(cls, channel_id: str) -> Optional[dict]:
        """Busca canal por ID sem verificar usuário."""
        try:
            obj_id = ObjectId(channel_id)
        except InvalidId:
            return None

        collection = cls._get_collection()
        channel = collection.find_one({"_id": obj_id})
        return cls._serialize_document(channel) if channel else None

    # =====================================================
    # BUSCAS POR NOME DE INSTÂNCIA E BOT TOKEN
    # =====================================================
    
    @classmethod
    def get_channel_by_instance_name(
        cls, 
        channel_type: str, 
        instance_name: str
    ) -> Tuple[Optional[str], Optional[dict]]:
        """Busca canal pelo nome da instância."""
        collection = cls._get_collection()
        
        doc = collection.find_one({
            "channel_type": channel_type,
            "metadata.instance_name": instance_name
        })
        
        if doc:
            doc = cls._serialize_document(doc)
            return doc.get("user_id"), doc
        
        return None, None
    
    @classmethod
    def get_channel_by_bot_token(cls, bot_token: str) -> Tuple[Optional[str], Optional[dict]]:
        """Busca canal do Telegram pelo bot_token."""
        collection = cls._get_collection()
        
        doc = collection.find_one({
            "channel_type": "telegram",
            "required.bot_token": bot_token
        })
        
        if doc:
            doc = cls._serialize_document(doc)
            return doc.get("user_id"), doc
        
        return None, None

    # =====================================================
    # CREATE
    # =====================================================
    
    @classmethod
    def create_channel(cls, channel_dict: dict) -> Optional[dict]:
        """Cria um novo canal."""
        try:
            collection = cls._get_collection()
            
            # Timestamps
            now = datetime.utcnow()
            if "created_at" not in channel_dict:
                channel_dict["created_at"] = now
            if "updated_at" not in channel_dict:
                channel_dict["updated_at"] = now
            
            # Garante que status tenha last_checked
            if "status" not in channel_dict:
                channel_dict["status"] = {}
            if "last_checked" not in channel_dict["status"]:
                channel_dict["status"]["last_checked"] = now
            
            # Converte ObjectIds para string recursivamente
            channel_dict = cls._serialize_objectid(channel_dict)
            
            # Remove _id se existir (para não gerar conflito)
            channel_dict.pop("_id", None)
            
            # Insere no banco (MongoDB gera ObjectId automaticamente)
            result = collection.insert_one(channel_dict)
            
            # Busca o documento criado com o ObjectId gerado
            created_channel = collection.find_one({"_id": result.inserted_id})
            return cls._serialize_document(created_channel)
            
        except Exception as e:
            logger.error(f"[CHANNEL DAO] Erro ao criar canal: {e}")
            return None

    # =====================================================
    # UPDATE
    # =====================================================
    
    @classmethod
    def update_channel(cls, channel_id: str, updates: Dict[str, Any], user_id: str) -> Optional[dict]:
        """Atualiza parcialmente um canal."""
        try:
            obj_id = ObjectId(channel_id)
        except InvalidId:
            return None
        
        # Adiciona timestamp
        updates["updated_at"] = datetime.utcnow()
        
        # Converte ObjectIds para string recursivamente
        updates = cls._serialize_objectid(updates)
        
        collection = cls._get_collection()
        result = collection.update_one(
            {"_id": obj_id, "user_id": user_id},
            {"$set": updates}
        )
        
        if result.matched_count == 0:
            return None
        
        updated_channel = collection.find_one({"_id": obj_id})
        return cls._serialize_document(updated_channel)
    
    @classmethod
    def update_channel_status(
        cls,
        channel_id: str,
        user_id: str,
        state: str,
        connection: str,
        error_message: Optional[str] = None
    ) -> Optional[dict]:
        """Atualiza status de conexão do canal."""
        updates = {
            "status.state": state,
            "status.connection": connection,
            "status.last_checked": datetime.utcnow()
        }
        
        if error_message:
            updates["status.error_message"] = error_message
        else:
            updates["status.error_message"] = None
        
        return cls.update_channel(channel_id, updates, user_id)

    # =====================================================
    # UPDATE CAMPO ESPECÍFICO POR INSTANCE_NAME
    # =====================================================
    
    @classmethod
    def update_channel_field(
        cls,
        channel_type: str,
        instance_name: str,
        field_path: str,
        value: Any,
    ) -> bool:
        """
        Atualiza um campo específico de um canal usando instance_name.
        Usado pelo webhook service para salvar chat_id e status.
        
        Args:
            channel_type: Tipo do canal ("telegram", "whatsapp", etc.)
            instance_name: Nome da instância (metadata.instance_name)
            field_path: Caminho do campo (ex: "required.chat_id", "status.connection")
            value: Valor a ser atribuído
        
        Returns:
            True se atualizou, False se não encontrou ou erro
        """
        try:
            collection = cls._get_collection()
            
            # Prepara o update com timestamp
            update_data = {
                field_path: value,
                "updated_at": datetime.utcnow()
            }
            
            result = collection.update_one(
                {
                    "channel_type": channel_type,
                    "metadata.instance_name": instance_name,
                },
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"[CHANNEL DAO] Campo '{field_path}' atualizado para {instance_name} = {value}")
                return True
            
            # Se não modificou, verifica se o canal existe
            exists = collection.find_one({
                "channel_type": channel_type,
                "metadata.instance_name": instance_name,
            })
            
            if exists:
                # Canal existe mas o valor já era o mesmo
                logger.debug(f"[CHANNEL DAO] Campo '{field_path}' já possuía o valor {value}")
                return True
            
            logger.warning(f"[CHANNEL DAO] Canal não encontrado: {channel_type}/{instance_name}")
            return False
            
        except Exception as e:
            logger.error(f"[CHANNEL DAO] Erro ao atualizar campo '{field_path}': {e}")
            return False

    # =====================================================
    # DELETE
    # =====================================================
    
    @classmethod
    def delete_channel(cls, channel_id: str, user_id: str) -> bool:
        """Remove um canal permanentemente."""
        try:
            obj_id = ObjectId(channel_id)
        except InvalidId:
            return False
        
        collection = cls._get_collection()
        result = collection.delete_one({"_id": obj_id, "user_id": user_id})
        
        if result.deleted_count > 0:
            logger.info(f"[CHANNEL DAO] Canal deletado: {channel_id}")
        
        return result.deleted_count > 0

    # =====================================================
    # HABILITAR/DESABILITAR
    # =====================================================
    
    @classmethod
    def enable_channel(cls, channel_id: str, user_id: str) -> Optional[dict]:
        """Habilita um canal."""
        return cls.update_channel(channel_id, {"enabled": True}, user_id)
    
    @classmethod
    def disable_channel(cls, channel_id: str, user_id: str) -> Optional[dict]:
        """Desabilita um canal."""
        return cls.update_channel(channel_id, {"enabled": False}, user_id)

    # =====================================================
    # AGENTES NO CANAL
    # =====================================================
    
    @classmethod
    def add_agent_to_channel(
        cls,
        channel_id: str,
        user_id: str,
        agent: Dict[str, Any]
    ) -> Optional[dict]:
        """Adiciona um agente ao canal."""
        try:
            obj_id = ObjectId(channel_id)
        except InvalidId:
            return None
        
        collection = cls._get_collection()
        result = collection.update_one(
            {"_id": obj_id, "user_id": user_id},
            {
                "$push": {"agents": agent},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        if result.matched_count == 0:
            return None
        
        updated_channel = collection.find_one({"_id": obj_id})
        return cls._serialize_document(updated_channel)
    
    @classmethod
    def remove_agent_from_channel(
        cls,
        channel_id: str,
        user_id: str,
        agent_id: str
    ) -> Optional[dict]:
        """Remove um agente do canal."""
        try:
            obj_id = ObjectId(channel_id)
        except InvalidId:
            return None
        
        collection = cls._get_collection()
        result = collection.update_one(
            {"_id": obj_id, "user_id": user_id},
            {
                "$pull": {"agents": {"id": agent_id}},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        if result.matched_count == 0:
            return None
        
        updated_channel = collection.find_one({"_id": obj_id})
        return cls._serialize_document(updated_channel)

    # =====================================================
    # LISTAGEM
    # =====================================================
    
    @classmethod
    def list_user_channels(
        cls, 
        user_id: str, 
        channel_type: Optional[str] = None
    ) -> List[dict]:
        """Lista todos os canais de um usuário."""
        collection = cls._get_collection()
        
        query = {"user_id": user_id}
        if channel_type:
            query["channel_type"] = channel_type
        
        cursor = collection.find(query).sort("created_at", -1)
        return [cls._serialize_document(channel) for channel in cursor]
    
    @classmethod
    def list_all_channels(
        cls,
        channel_type: Optional[str] = None,
        enabled_only: bool = False,
        limit: int = 100,
        skip: int = 0
    ) -> List[dict]:
        """Lista todos os canais (admin/sistema)."""
        collection = cls._get_collection()
        
        query = {}
        if channel_type:
            query["channel_type"] = channel_type
        if enabled_only:
            query["enabled"] = True
        
        cursor = collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
        return [cls._serialize_document(channel) for channel in cursor]

    # =====================================================
    # UTILITÁRIOS
    # =====================================================
    
    @classmethod
    def channel_exists(cls, channel_id: str, user_id: str) -> bool:
        """Verifica se o canal existe e pertence ao usuário."""
        try:
            obj_id = ObjectId(channel_id)
        except InvalidId:
            return False
        
        collection = cls._get_collection()
        count = collection.count_documents({"_id": obj_id, "user_id": user_id})
        return count > 0
    
    @classmethod
    def count_user_channels(
        cls,
        user_id: str,
        channel_type: Optional[str] = None
    ) -> int:
        """Conta quantos canais um usuário possui."""
        collection = cls._get_collection()
        
        query = {"user_id": user_id}
        if channel_type:
            query["channel_type"] = channel_type
        
        return collection.count_documents(query)
    
    @classmethod
    def update_webhook_config(
        cls,
        channel_id: str,
        user_id: str,
        webhook_data: Dict[str, Any]
    ) -> Optional[dict]:
        """Atualiza configuração de webhook do canal."""
        return cls.update_channel(channel_id, {"webhook": webhook_data}, user_id)
    
    # dao/mongo/v1/channel_dao.py (adicione este método)

    @classmethod
    def get_channel_by_widget_token(cls, widget_token: str) -> Tuple[Optional[str], Optional[dict]]:
        """
        Busca canal pelo widget_token do Saphien.
        Retorna (user_id, channel_dict) ou (None, None) se não encontrar.
        """
        try:
            collection = cls._get_collection()
            channel = collection.find_one({"required.widget_token": widget_token})
            if channel:
                return channel.get("user_id"), cls._serialize_document(channel)
            return None, None
        except Exception as e:
            logger.error(f"[CHANNEL_DAO] Erro ao buscar por widget_token: {e}")
            return None, None