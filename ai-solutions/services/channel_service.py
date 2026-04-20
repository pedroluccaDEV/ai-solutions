# services/v1/channel_service.py
"""
Serviço genérico para gerenciar canais (CRUD + operações específicas por tipo).

- whatsapp  → delega ao EvoChannelHandler (síncrono, Evolution API)
- telegram  → delega ao TelegramChannelHandler (async, Telegram Bot API)
- webhook_saphien → delega ao SaphienChannelHandler (síncrono, geração de widget)
"""
from typing import Optional, Dict, Any, List, Tuple
from loguru import logger
from datetime import datetime

from dao.mongo.channel_dao import ChannelDAO

# Tipos de canal e seus handlers
EVO_CHANNEL_TYPES = {"whatsapp"}
TELEGRAM_CHANNEL_TYPES = {"telegram"}
SAPHIEN_CHANNEL_TYPES = {"webhook_saphien"}


def _get_evo_handler():
    """Import lazy do EvoChannelHandler."""
    from features.channels.evolution.connection.evo_channel_handler import EvoChannelHandler
    return EvoChannelHandler()


def _get_telegram_handler():
    """Import lazy do TelegramChannelHandler."""
    from features.channels.telegram.connection.telegram_channel_handler import TelegramChannelHandler
    return TelegramChannelHandler()


def _get_saphien_handler():
    """Import lazy do SaphienChannelHandler."""
    from features.channels.webhook_saphien.connection.saphien_channel_handler import SaphienChannelHandler
    return SaphienChannelHandler()


class ChannelService:

    # ======================================================
    # CRIAR CANAL
    # ======================================================

    @staticmethod
    async def create_channel(
        user_id: str,
        channel_type: str,
        channel_data: Dict[str, Any],
    ) -> Optional[dict]:
        """
        Cria uma nova instância de canal.

        Fluxo por tipo:
          whatsapp → registra na Evolution API → salva no banco
          telegram → valida token + registra webhook no Telegram → salva no banco
          webhook_saphien → gera widget_token + snippet JS → salva no banco
        """
        try:
            if "metadata" in channel_data:
                channel_data["metadata"].setdefault("created_at", datetime.now())
                channel_data["metadata"].setdefault("updated_at", datetime.now())

            channel_data.setdefault("status", {})
            channel_data["status"].setdefault("last_checked", datetime.now())
            channel_data["status"].setdefault("state", "pending")
            channel_data["status"].setdefault("connection", "never_connected")

            # Extrai agents se existirem
            agents = channel_data.pop("agents", [])
            
            logger.info(f"[CHANNEL] Agents extraídos: {len(agents)} agents")

            # --- WhatsApp / Evolution ---
            if channel_type in EVO_CHANNEL_TYPES:
                handler = _get_evo_handler()
                evo_result = handler.on_channel_created(channel_data)

                if evo_result:
                    channel_data["status"]["qrcode"] = evo_result.get("qrcode")
                    channel_data["status"]["state"] = "pending"
                    channel_data["status"]["connection"] = "awaiting_qr"

                    if evo_result.get("webhook_url") and "webhook" in channel_data:
                        channel_data["webhook"]["url"] = evo_result["webhook_url"]

            # --- Telegram ---
            elif channel_type in TELEGRAM_CHANNEL_TYPES:
                handler = _get_telegram_handler()
                telegram_result = await handler.on_channel_created(channel_data)

                if telegram_result:
                    channel_data["status"]["connection"] = "awaiting_start"
                    channel_data["status"]["state"] = "pending"
                    channel_data["bot_info"] = telegram_result.get("bot_info", {})

                    if telegram_result.get("webhook_url") and "webhook" in channel_data:
                        channel_data["webhook"]["url"] = telegram_result["webhook_url"]

                    logger.info(
                        f"[CHANNEL] Telegram webhook configurado | "
                        f"bot=@{telegram_result.get('bot_info', {}).get('username')} | "
                        f"instância={channel_data.get('instance_name')}"
                    )

            # --- Saphien Webhook ---
            elif channel_type in SAPHIEN_CHANNEL_TYPES:
                handler = _get_saphien_handler()
                saphien_result = handler.on_channel_created(channel_data)

                if saphien_result:
                    channel_data["status"]["connection"] = "connected"
                    channel_data["status"]["state"] = "active"
                    channel_data["status"]["webhook_set"] = True
                    channel_data["status"]["webhook_url_confirmed"] = saphien_result.get("webhook_url")
                    
                    if "required" not in channel_data:
                        channel_data["required"] = {}
                    channel_data["required"]["widget_token"] = saphien_result["widget_token"]
                    
                    logger.info(
                        f"[CHANNEL] Saphien widget criado | "
                        f"token={saphien_result['widget_token'][:15]}... | "
                        f"instância={channel_data.get('instance_name')}"
                    )

            # --- Persiste no MongoDB ---
            channel_dict = {
                "user_id": user_id,
                "channel_type": channel_type,
                **channel_data,
            }
            
            # Adiciona agents se existirem
            if agents:
                agents_list = []
                for agent in agents:
                    # Suporta Pydantic v1 (dict) e v2 (model_dump)
                    if hasattr(agent, 'model_dump'):
                        agent_dict = agent.model_dump()
                    elif hasattr(agent, 'dict'):
                        agent_dict = agent.dict()
                    elif isinstance(agent, dict):
                        agent_dict = agent.copy()
                    else:
                        agent_dict = dict(agent)
                    
                    # Garante que trigger_config seja dict
                    if "trigger_config" in agent_dict:
                        if hasattr(agent_dict["trigger_config"], 'model_dump'):
                            agent_dict["trigger_config"] = agent_dict["trigger_config"].model_dump()
                        elif hasattr(agent_dict["trigger_config"], 'dict'):
                            agent_dict["trigger_config"] = agent_dict["trigger_config"].dict()
                        elif not isinstance(agent_dict["trigger_config"], dict):
                            agent_dict["trigger_config"] = {}
                    else:
                        agent_dict["trigger_config"] = {}
                    
                    # Garante campos opcionais
                    agent_dict.setdefault("priority", 0)
                    agent_dict.setdefault("created_at", datetime.now().isoformat())
                    agent_dict.setdefault("last_used", None)
                    agent_dict.setdefault("status", "active")
                    
                    agents_list.append(agent_dict)
                
                channel_dict["agents"] = agents_list
                logger.info(f"[CHANNEL] Adicionando {len(agents_list)} agentes ao canal")
            else:
                channel_dict["agents"] = []
                logger.info(f"[CHANNEL] Nenhum agente para adicionar")

            logger.info(f"[CHANNEL] Channel_dict final tem {len(channel_dict.get('agents', []))} agentes")

            result = ChannelDAO.create_channel(channel_dict)
            if result:
                logger.info(
                    f"[CHANNEL] Criado {channel_type} para user {user_id} "
                    f"com ID: {result.get('_id')} e {len(result.get('agents', []))} agentes"
                )
            return result

        except RuntimeError as e:
            logger.error(f"[CHANNEL] API externa recusou criação: {e}")
            raise
        except Exception as e:
            logger.error(f"[CHANNEL] Erro ao criar canal: {e}")
            logger.exception(e)
            return None

    # ======================================================
    # LEITURA
    # ======================================================

    @staticmethod
    def get_channel(channel_id: str) -> Optional[dict]:
        return ChannelDAO.get_channel_by_id(channel_id)

    @staticmethod
    def get_channel_by_id_and_user(channel_id: str, user_id: str) -> Optional[dict]:
        return ChannelDAO.get_channel_by_id_and_user(channel_id, user_id)

    @staticmethod
    def get_channel_by_instance_name(
        channel_type: str,
        instance_name: str,
    ) -> Tuple[Optional[str], Optional[dict]]:
        """Busca canal pelo nome da instância. Retorna (user_id, channel)."""
        return ChannelDAO.get_channel_by_instance_name(channel_type, instance_name)

    @staticmethod
    def get_channel_by_bot_token(bot_token: str) -> Tuple[Optional[str], Optional[dict]]:
        """Busca canal do Telegram pelo bot_token. Retorna (user_id, channel)."""
        return ChannelDAO.get_channel_by_bot_token(bot_token)
    
    @staticmethod
    def get_channel_by_widget_token(widget_token: str) -> Tuple[Optional[str], Optional[dict]]:
        """Busca canal do Saphien pelo widget_token. Retorna (user_id, channel)."""
        return ChannelDAO.get_channel_by_widget_token(widget_token)

    @staticmethod
    def list_user_channels(
        user_id: str,
        channel_type: Optional[str] = None,
    ) -> List[dict]:
        return ChannelDAO.list_user_channels(user_id, channel_type)

    @staticmethod
    def list_all_channels(
        channel_type: Optional[str] = None,
        enabled_only: bool = False,
        limit: int = 100,
        skip: int = 0,
    ) -> List[dict]:
        return ChannelDAO.list_all_channels(channel_type, enabled_only, limit, skip)

    @staticmethod
    def count_user_channels(
        user_id: str,
        channel_type: Optional[str] = None,
    ) -> int:
        try:
            return ChannelDAO.count_user_channels(user_id, channel_type)
        except Exception as e:
            logger.error(f"[CHANNEL] Erro ao contar canais do user {user_id}: {e}")
            return 0

    # ======================================================
    # ATUALIZAR CANAL
    # ======================================================

    @staticmethod
    def update_channel_field(
        channel_type: str,
        instance_name: str,
        field_path: str,
        value: Any,
    ) -> bool:
        """
        Atualiza um campo específico de um canal via instance_name.
        Usado pelo webhook service para salvar chat_id e status.
        """
        return ChannelDAO.update_channel_field(
            channel_type=channel_type,
            instance_name=instance_name,
            field_path=field_path,
            value=value,
        )
        
    @staticmethod
    async def update_channel(
        channel_id: str,
        user_id: str,
        updates: Dict[str, Any],
    ) -> Optional[dict]:
        """
        Atualiza canal no banco.

        Suporta atualização de agents via campo "agents" no updates.
        """
        try:
            current = ChannelDAO.get_channel_by_id_and_user(channel_id, user_id)
            if not current:
                return None

            channel_type = current.get("channel_type", "")

            # Extrai agents do update (se existir)
            agents_update = updates.pop("agents", None)
            
            # Propaga para handlers externos
            if channel_type in EVO_CHANNEL_TYPES:
                handler = _get_evo_handler()
                merged = {**current, **updates}
                try:
                    handler.on_channel_updated(merged, updated_fields=updates)
                except Exception as e:
                    logger.warning(f"[CHANNEL] Evolution update parcialmente falhou: {e}")

            elif channel_type in TELEGRAM_CHANNEL_TYPES:
                handler = _get_telegram_handler()
                merged = {**current, **updates}
                try:
                    await handler.on_channel_updated(merged, updated_fields=updates)
                except Exception as e:
                    logger.warning(f"[CHANNEL] Telegram update parcialmente falhou: {e}")
            
            elif channel_type in SAPHIEN_CHANNEL_TYPES:
                handler = _get_saphien_handler()
                merged = {**current, **updates}
                try:
                    handler.on_channel_updated(merged, updated_fields=updates)
                except Exception as e:
                    logger.warning(f"[CHANNEL] Saphien update parcialmente falhou: {e}")

            # Atualiza campos normais
            result = ChannelDAO.update_channel(channel_id, updates, user_id)
            
            # Se tiver agents_update, atualiza a lista completa
            if agents_update is not None:
                agents_list = []
                for agent in agents_update:
                    # Suporta Pydantic v1/v2
                    if hasattr(agent, 'model_dump'):
                        agent_dict = agent.model_dump()
                    elif hasattr(agent, 'dict'):
                        agent_dict = agent.dict()
                    elif isinstance(agent, dict):
                        agent_dict = agent.copy()
                    else:
                        agent_dict = dict(agent)
                    
                    # Garante que trigger_config seja dict
                    if "trigger_config" in agent_dict:
                        if hasattr(agent_dict["trigger_config"], 'model_dump'):
                            agent_dict["trigger_config"] = agent_dict["trigger_config"].model_dump()
                        elif hasattr(agent_dict["trigger_config"], 'dict'):
                            agent_dict["trigger_config"] = agent_dict["trigger_config"].dict()
                        elif not isinstance(agent_dict["trigger_config"], dict):
                            agent_dict["trigger_config"] = {}
                    else:
                        agent_dict["trigger_config"] = {}
                    
                    # Garante campos opcionais
                    agent_dict.setdefault("priority", 0)
                    agent_dict.setdefault("created_at", datetime.now().isoformat())
                    agent_dict.setdefault("last_used", None)
                    agent_dict.setdefault("status", "active")
                    
                    agents_list.append(agent_dict)
                
                # Substitui a lista inteira de agentes
                agent_result = ChannelDAO.update_channel(
                    channel_id, 
                    {"agents": agents_list}, 
                    user_id
                )
                if agent_result:
                    result = agent_result
                    logger.info(f"[CHANNEL] Lista de agentes atualizada: {len(agents_list)} agentes")
            
            return result

        except Exception as e:
            logger.error(f"[CHANNEL] Erro ao atualizar canal {channel_id}: {e}")
            logger.exception(e)
            return None

    # ======================================================
    # DELETAR CANAL
    # ======================================================

    @staticmethod
    async def delete_channel(channel_id: str, user_id: str) -> bool:
        """
        Remove canal do banco.

        Remove instância/webhook da API externa antes.
        Erro externo não impede remoção do banco.
        """
        try:
            current = ChannelDAO.get_channel_by_id_and_user(channel_id, user_id)
            if not current:
                return False

            channel_type = current.get("channel_type", "")

            if channel_type in EVO_CHANNEL_TYPES:
                handler = _get_evo_handler()
                handler.on_channel_deleted(current)

            elif channel_type in TELEGRAM_CHANNEL_TYPES:
                handler = _get_telegram_handler()
                await handler.on_channel_deleted(current)
            
            elif channel_type in SAPHIEN_CHANNEL_TYPES:
                handler = _get_saphien_handler()
                handler.on_channel_deleted(current)

            return ChannelDAO.delete_channel(channel_id, user_id)

        except Exception as e:
            logger.error(f"[CHANNEL] Erro ao deletar canal {channel_id}: {e}")
            return False

    # ======================================================
    # STATUS E ENABLE/DISABLE
    # ======================================================

    @staticmethod
    def update_channel_status(
        channel_id: str,
        user_id: str,
        state: str,
        connection: str,
        error_message: Optional[str] = None,
    ) -> Optional[dict]:
        return ChannelDAO.update_channel_status(
            channel_id, user_id, state, connection, error_message
        )

    @staticmethod
    def enable_channel(channel_id: str, user_id: str) -> Optional[dict]:
        return ChannelDAO.enable_channel(channel_id, user_id)

    @staticmethod
    def disable_channel(channel_id: str, user_id: str) -> Optional[dict]:
        return ChannelDAO.disable_channel(channel_id, user_id)

    # ======================================================
    # AGENTES (operações específicas)
    # ======================================================

    @staticmethod
    def add_agent_to_channel(
        channel_id: str,
        user_id: str,
        agent_id: str,
        agent_name: str,
        trigger_config: Optional[Dict[str, Any]] = None,
    ) -> Optional[dict]:
        """
        Adiciona um agente ao canal (push na lista).
        """
        agent = {
            "id": agent_id,
            "name": agent_name,
            "status": "active",
            "trigger_config": trigger_config or {
                "enabled": False,
                "type": "keyword",
                "operator": "contains",
                "trigger": "",
                "case_sensitive": False,
            },
            "priority": 0,
            "created_at": datetime.now().isoformat(),
            "last_used": None,
        }
        logger.info(f"[CHANNEL] Adicionando agente {agent_id} ao canal {channel_id}")
        return ChannelDAO.add_agent_to_channel(channel_id, user_id, agent)

    @staticmethod
    def remove_agent_from_channel(
        channel_id: str,
        user_id: str,
        agent_id: str,
    ) -> Optional[dict]:
        """
        Remove um agente do canal.
        """
        logger.info(f"[CHANNEL] Removendo agente {agent_id} do canal {channel_id}")
        return ChannelDAO.remove_agent_from_channel(channel_id, user_id, agent_id)

    @staticmethod
    def get_agents_from_channel(
        channel_id: str,
        user_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Retorna a lista de agentes de um canal.
        """
        channel = ChannelDAO.get_channel_by_id_and_user(channel_id, user_id)
        if not channel:
            return []
        return channel.get("agents", [])