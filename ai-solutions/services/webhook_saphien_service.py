# services/v1/webhook_saphien_service.py
"""
Serviço para processamento de webhooks do Saphien Widget.
Orquestra o fluxo: validação → sessão → memória → agente → resposta.
"""
from loguru import logger
from typing import Optional, Dict, Any
from datetime import datetime

from services.v1.channel_service import ChannelService
from services.v1.memory_chat_service import MemoryChatService
from services.v1.saphien_session_service import SaphienSessionService
from features.widget.agent.saphien_agent import execute_saphien_agent
from features.widget.connection.saphien_connection import SaphienConnection


# ======================================================
# HELPERS
# ======================================================

def _lookup_channel_by_widget_token(widget_token: str):
    """Busca canal Saphien pelo widget_token."""
    user_id, channel_data = ChannelService.get_channel_by_widget_token(widget_token)
    return user_id, channel_data


def _get_instance_name_from_channel(channel_data: dict) -> str:
    """Extrai instance_name do channel_data."""
    return channel_data.get("instance_name") or channel_data.get("metadata", {}).get("instance_name", "unknown")


def _check_allowed_origin(channel_data: dict, origin: Optional[str]) -> bool:
    """Verifica se a origem é permitida."""
    allowed_origins = channel_data.get("required", {}).get("allowed_origins", [])
    
    if not allowed_origins:
        return True
    
    if not origin:
        logger.warning("[SAPHIEN WEBHOOK] Requisição sem origin e allowed_origins configurado")
        return False
    
    return origin in allowed_origins


def _extract_user_info(data: dict) -> dict:
    """Extrai informações do usuário."""
    return {
        "url": data.get("url"),
        "user_agent": data.get("userAgent"),
        "ip": data.get("ip"),
        "timestamp": data.get("timestamp"),
    }


# ======================================================
# SERVICE PRINCIPAL
# ======================================================

class WebhookSaphienService:

    @staticmethod
    async def handle_incoming_message(
        widget_token: str,
        session_id: str,
        data: dict,
        origin: Optional[str] = None,
        db=None
    ) -> Optional[Dict[str, Any]]:
        """
        Processa mensagem recebida do widget Saphien.
        
        Args:
            widget_token: Token do widget (do header)
            session_id: ID da sessão do visitante (do header)
            data: Payload da mensagem
            origin: Origem da requisição (CORS)
            db: Conexão com MongoDB
        """
        try:
            logger.info(f"[SAPHIEN WEBHOOK] Mensagem recebida | token: {widget_token[:15]}... | session: {session_id}")

            message = data.get("message")
            if not message:
                logger.warning("[SAPHIEN WEBHOOK] Payload sem message")
                return SaphienConnection.create_error_response("Mensagem não fornecida")

            logger.info(f"[SAPHIEN WEBHOOK] Mensagem: {message[:100]}...")

            # Resolve canal
            user_id, channel_data = _lookup_channel_by_widget_token(widget_token)

            if not channel_data:
                logger.warning(f"[SAPHIEN WEBHOOK] Canal não encontrado para token: {widget_token[:15]}...")
                return SaphienConnection.create_error_response("Canal não encontrado")

            instance_name = _get_instance_name_from_channel(channel_data)
            logger.info(f"[SAPHIEN WEBHOOK] Canal encontrado: {instance_name}")

            if not channel_data.get("enabled", True):
                logger.warning(f"[SAPHIEN WEBHOOK] Canal desabilitado: {instance_name}")
                return SaphienConnection.create_error_response("Canal desabilitado")

            if not _check_allowed_origin(channel_data, origin):
                logger.warning(f"[SAPHIEN WEBHOOK] Origem não permitida: {origin}")
                return SaphienConnection.create_error_response("Origem não autorizada")

            # Obtém ou cria sessão
            session, is_new = SaphienSessionService.get_or_create_session(
                widget_token=widget_token,
                session_id=session_id,
                channel_agents=channel_data.get("agents", []),
            )
            
            if not session:
                logger.error(f"[SAPHIEN WEBHOOK] Falha ao obter/criar sessão para {session_id}")
                return SaphienConnection.create_error_response("Erro interno ao processar sessão")
            
            session_uuid = session["_id"]
            
            # Resolve agente
            agent = SaphienSessionService.resolve_and_update_agent(
                session=session,
                channel_data=channel_data,
                message_text=message,
            )
            
            if not agent:
                return SaphienConnection.create_error_response(
                    "Nenhum agente configurado. Configure um agente no painel."
                )
            
            agent_id = agent.get("id")
            agent_name = agent.get("name", "Desconhecido")
            
            # Limpa o prompt
            cleaned_prompt = SaphienSessionService.clean_prompt(message, agent)
            
            logger.info(f"[SAPHIEN WEBHOOK] Agente: {agent_name} ({agent_id}) | Prompt: {cleaned_prompt[:100]}...")
            
            # Inicializa serviço de memória
            memory_service = MemoryChatService(db)
            
            # Salva mensagem do usuário
            await memory_service.save_user_message_with_files(
                session_id=session_uuid,
                user_id=session_uuid,
                content=cleaned_prompt,
                files_dict=None,
                images=None
            )
            
            # Salva no DAO
            SaphienSessionService.save_user_message(
                session_uuid=session_uuid,
                user_id=session_uuid,
                content=cleaned_prompt,
                metadata={
                    "original_message": message,
                    "agent_id": agent_id,
                    "cleaned": True,
                }
            )
            
            # Busca histórico
            conversation_history = SaphienSessionService.get_conversation_history(
                session_uuid=session_uuid,
                limit=10,
            )
            
            # Executa agente
            try:
                agent_response = await execute_saphien_agent(
                    request_data={
                        "user_id": user_id,
                        "agent_id": agent_id,
                        "message": cleaned_prompt,
                        "session_id": session_uuid,
                        "conversation_history": conversation_history,
                        "channel": "saphien",
                        "widget_token": widget_token,
                        "session_id_frontend": session_id,
                    },
                    user_jwt="",
                    user_id=user_id,
                    db=db,
                )
                
                if agent_response and agent_response.get("success"):
                    response_text = agent_response.get("response", "")
                    model_used = agent_response.get("model_used")
                    
                    if response_text:
                        await memory_service.save_assistant_response_with_context(
                            session_id=session_uuid,
                            user_id=session_uuid,
                            content=response_text,
                            files_dict=None,
                            model_info={
                                "model_id": model_used,
                                "model_name": model_used,
                                "provider": "saphien_widget"
                            },
                            flow_type="saphien",
                            images=None
                        )
                        
                        SaphienSessionService.save_assistant_message(
                            session_uuid=session_uuid,
                            agent_id=agent_id,
                            content=response_text,
                            metadata={"model_used": model_used}
                        )
                        
                        SaphienSessionService.update_session_activity(session_uuid)
                        
                        logger.info(f"[SAPHIEN WEBHOOK] ✅ Resposta enviada para session {session_id}")
                        
                        return SaphienConnection.create_response(response_text)
                    else:
                        return SaphienConnection.create_error_response(
                            "Não consegui processar sua solicitação no momento."
                        )
                else:
                    error_msg = agent_response.get("error", "Erro desconhecido") if agent_response else "Sem resposta"
                    logger.error(f"[SAPHIEN WEBHOOK] Agente retornou erro: {error_msg}")
                    return SaphienConnection.create_error_response(
                        "Ocorreu um erro ao processar sua mensagem. Tente novamente."
                    )
                    
            except Exception as agent_error:
                logger.exception(f"[SAPHIEN WEBHOOK] Erro no agente: {agent_error}")
                return SaphienConnection.create_error_response(
                    "Ocorreu um erro inesperado. Tente novamente mais tarde."
                )

        except Exception as e:
            logger.exception(f"[SAPHIEN WEBHOOK ERRO] {e}")
            return SaphienConnection.create_error_response(f"Erro interno: {str(e)}")

    @staticmethod
    async def register_session(
        widget_token: str,
        session_id: str,
        data: dict,
        origin: Optional[str] = None,
        db=None
    ) -> Optional[Dict[str, Any]]:
        try:
            logger.info(f"[SAPHIEN WEBHOOK] Registro de sessão | token: {widget_token[:15]}... | session: {session_id}")

            user_info = _extract_user_info(data)

            user_id, channel_data = _lookup_channel_by_widget_token(widget_token)

            if not channel_data:
                return {
                    "status": "error",
                    "message": "Canal não encontrado",
                    "session_id": session_id,
                    "is_new": False,
                    "created_at": None,
                    "instance_name": None
                }

            if not _check_allowed_origin(channel_data, origin):
                logger.warning(f"[SAPHIEN WEBHOOK] Origem não permitida: {origin}")
                return {
                    "status": "error",
                    "message": "Origem não autorizada",
                    "session_id": session_id,
                    "is_new": False,
                    "created_at": None,
                    "instance_name": None
                }

            session, is_new = SaphienSessionService.get_or_create_session(
                widget_token=widget_token,
                session_id=session_id,
                channel_agents=channel_data.get("agents", []),
                user_info=user_info,
            )

            if not session:
                return {
                    "status": "error",
                    "message": "Erro ao criar sessão",
                    "session_id": session_id,
                    "is_new": False,
                    "created_at": None,
                    "instance_name": None
                }

            # 🔥 CONVERTER datetime PARA string
            created_at_value = session.get("createdAt") or session.get("created_at")
            if created_at_value and hasattr(created_at_value, 'isoformat'):
                created_at_str = created_at_value.isoformat()
            else:
                created_at_str = None

            return {
                "status": "success",
                "session_id": session_id,
                "is_new": is_new,
                "created_at": created_at_str,  # ← agora é string
                "instance_name": _get_instance_name_from_channel(channel_data),
            }

        except Exception as e:
            logger.exception(f"[SAPHIEN WEBHOOK] Erro ao registrar sessão: {e}")
            return {
                "status": "error",
                "message": str(e),
                "session_id": session_id,
                "is_new": False,
                "created_at": None,
                "instance_name": None
            }
            
    @staticmethod
    async def get_session_messages(
        widget_token: str,
        session_id: str,
        origin: Optional[str] = None,
        limit: int = 50
    ) -> Optional[Dict[str, Any]]:
        """
        Retorna as mensagens de uma sessão.
        """
        try:
            logger.info(f"[SAPHIEN WEBHOOK] Buscando mensagens | session: {session_id}")

            user_id, channel_data = _lookup_channel_by_widget_token(widget_token)

            if not channel_data:
                return {"status": "error", "message": "Canal não encontrado", "session_id": session_id, "messages": [], "count": 0}

            if not _check_allowed_origin(channel_data, origin):
                return {"status": "error", "message": "Origem não autorizada", "session_id": session_id, "messages": [], "count": 0}

            session, _ = SaphienSessionService.get_or_create_session(
                widget_token=widget_token,
                session_id=session_id,
                channel_agents=channel_data.get("agents", []),
            )

            if not session:
                return {"status": "error", "message": "Sessão não encontrada", "session_id": session_id, "messages": [], "count": 0}

            session_uuid = session["_id"]
            messages = SaphienSessionService.get_conversation_history(session_uuid, limit)

            formatted_messages = []
            for msg in messages:
                # 🔥 CONVERTER timestamp PARA STRING
                timestamp_value = msg.get("timestamp")
                if timestamp_value and hasattr(timestamp_value, 'isoformat'):
                    timestamp_str = timestamp_value.isoformat()
                else:
                    timestamp_str = None
                
                formatted_messages.append({
                    "text": msg.get("content"),
                    "sender": "user" if msg.get("role") == "user" else "bot",
                    "timestamp": timestamp_str,  # ← agora é string
                })

            return {
                "status": "success",
                "session_id": session_id,
                "messages": formatted_messages,
                "count": len(formatted_messages),
            }

        except Exception as e:
            logger.exception(f"[SAPHIEN WEBHOOK] Erro ao buscar mensagens: {e}")
            return {"status": "error", "message": str(e), "session_id": session_id, "messages": [], "count": 0}