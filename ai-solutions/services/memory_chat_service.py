# services/v1/memory_chat_service.py - VERSÃO COMPLETA COM SUPORTE A IMAGENS
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from uuid import uuid4

from dao.mongo.memory_chat_dao import MemoryDAO

logger = logging.getLogger(__name__)


class MemoryChatService:
    """
    Service focado apenas no gerenciamento de memória de chat.
    Responsabilidade única: armazenar e recuperar mensagens de conversas.
    Versão atualizada com suporte a imagens.
    """
    
    def __init__(self, db):
        self.memory_dao = MemoryDAO(db)
        self.chat_messages_collection = db["chat_messages"]
        logger.info("✅ MemoryChatService inicializado com persistência completa")

    # ============================================================================
    # MÉTODOS BÁSICOS (com suporte a imagens)
    # ============================================================================

    def add_user_message(
        self,
        session_id: str,
        user_id: str,
        content: str,
        images: Optional[List[Dict[str, Any]]] = None  # 🔥 NOVO
    ) -> Optional[str]:
        """Adiciona mensagem do usuário à memória."""
        try:
            message_id = self.memory_dao.add_message_to_memory(
                session_id=session_id,
                sender="user",
                content=content,
                metadata={"user_id": user_id},
                images=images  # 🔥 NOVO
            )
            
            if message_id:
                if images:
                    logger.info(f"📸 Mensagem do usuário com {len(images)} imagem(ns) salva")
                else:
                    logger.debug(f"✅ Mensagem do usuário salva na memória - Sessão: {session_id}")
            else:
                logger.warning(f"⚠️ Não foi possível salvar mensagem do usuário - Sessão: {session_id}")
            
            return message_id
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar mensagem do usuário: {e}")
            return None

    def add_assistant_message(
        self,
        session_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        images: Optional[List[Dict[str, Any]]] = None  # 🔥 NOVO
    ) -> Optional[str]:
        """Adiciona mensagem do assistente à memória."""
        try:
            message_id = self.memory_dao.add_message_to_memory(
                session_id=session_id,
                sender="assistant",
                content=content,
                metadata=metadata or {},
                images=images  # 🔥 NOVO
            )
            
            if message_id:
                if images:
                    logger.info(f"📸 Mensagem do assistente com {len(images)} imagem(ns) salva")
                else:
                    logger.debug(f"✅ Mensagem do assistente salva na memória - Sessão: {session_id}")
            else:
                logger.warning(f"⚠️ Não foi possível salvar mensagem do assistente - Sessão: {session_id}")
            
            return message_id
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar mensagem do assistente: {e}")
            return None

    def session_has_memory(
        self,
        session_id: str
    ) -> bool:
        """Verifica se a sessão tem memória."""
        try:
            return self.memory_dao.session_has_memory(session_id)
        except Exception as e:
            logger.error(f"❌ Erro ao verificar memória da sessão: {e}")
            return False

    # 🔥 NOVO: Verificar se a sessão tem imagens
    def session_has_images(
        self,
        session_id: str
    ) -> bool:
        """Verifica se a sessão tem imagens na memória."""
        try:
            return self.memory_dao.session_has_images(session_id)
        except Exception as e:
            logger.error(f"❌ Erro ao verificar imagens da sessão: {e}")
            return False

    def create_memory_for_session(
        self,
        session_id: str,
        user_id: str,
        agent_id: str,
        is_new: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Cria memória para uma sessão."""
        try:
            base_metadata = {
                "user_id": user_id,
                "agent_id": agent_id,
                "is_new": is_new,
                "created_at": datetime.utcnow().isoformat(),
                "source": "new_session" if is_new else "existing_session",
                "has_images": False,  # 🔥 NOVO
                "images_count": 0     # 🔥 NOVO
            }
            
            if metadata:
                base_metadata.update(metadata)
            
            created = self.memory_dao.create_memory(
                session_id=session_id,
                metadata=base_metadata
            ) is not None
            
            if created:
                logger.info(f"✅ Memória criada para sessão: {session_id}")
            else:
                logger.warning(f"⚠️ Não foi possível criar memória para sessão: {session_id}")
            
            return created
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar memória: {e}")
            return False

    def get_memory_for_session(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Recupera dados da memória da sessão."""
        try:
            return self.memory_dao.get_memory_by_session_id(session_id)
        except Exception as e:
            logger.error(f"❌ Erro ao recuperar memória: {e}")
            return None

    def clear_session_memory(
        self,
        session_id: str
    ) -> bool:
        """Limpa todas as mensagens da memória da sessão."""
        try:
            deleted = self.memory_dao.delete_memory_by_session_id(session_id)
            
            if deleted:
                logger.info(f"✅ Memória limpa para sessão: {session_id}")
            else:
                logger.warning(f"⚠️ Não foi possível limpar memória para sessão: {session_id}")
            
            return deleted
            
        except Exception as e:
            logger.error(f"❌ Erro ao limpar memória: {e}")
            return False

    # ============================================================================
    # MÉTODOS DE PERSISTÊNCIA UNIFICADA (COM IMAGENS)
    # ============================================================================

    async def save_user_message_with_files(
        self,
        session_id: str,
        user_id: str,
        content: str,
        files_dict: Optional[Dict[str, Any]] = None,
        images: Optional[List[Dict[str, Any]]] = None  # 🔥 NOVO
    ) -> Dict[str, Any]:
        """
        Salva mensagem do usuário com arquivos e imagens em ambas as coleções.
        Retorna IDs de ambas as mensagens.
        """
        try:
            # 1. Preparar attachments
            attachments = None
            if files_dict and files_dict.get("files"):
                attachments = self._prepare_attachments_from_files(
                    files_dict, 
                    source="user_uploaded"
                )

            # 2. Salvar no Memory (principal)
            memory_metadata = {
                "source": "chat_streaming",
                "user_id": user_id,
                "has_files": attachments is not None,
                "file_count": len(attachments) if attachments else 0
            }

            memory_message_id = self.add_user_message(
                session_id=session_id,
                user_id=user_id,
                content=content,
                images=images  # 🔥 NOVO
            )

            # 3. Salvar no chat_messages (legacy/UI)
            chat_metadata = {
                "source": "chat_streaming",
                "memory_id": memory_message_id,
                "memory_service": "v1"
            }
            
            # 🔥 NOVO: Adicionar info de imagens ao metadata
            if images:
                chat_metadata["has_images"] = True
                chat_metadata["images_count"] = len(images)

            chat_message_id = self._save_to_chat_messages(
                session_id=session_id,
                sender="user",
                content=content,
                user_id=user_id,
                metadata=chat_metadata,
                attachments=attachments,
                images=images  # 🔥 NOVO
            )

            logger.info(
                f"✅ Mensagem do usuário salva | Memory: {memory_message_id}, Chat: {chat_message_id}"
            )

            return {
                "success": True,
                "memory_id": memory_message_id,
                "chat_id": chat_message_id,
                "session_id": session_id,
                "has_files": attachments is not None,
                "has_images": images is not None  # 🔥 NOVO
            }

        except Exception as e:
            logger.error(f"❌ Erro ao salvar mensagem do usuário: {e}")
            return {
                "success": False,
                "error": str(e),
                "memory_id": None,
                "chat_id": None
            }

    async def save_assistant_response_with_context(
        self,
        session_id: str,
        user_id: str,
        content: str,
        files_dict: Optional[Dict[str, Any]] = None,
        model_info: Optional[Dict[str, Any]] = None,
        flow_type: str = "chat",
        images: Optional[List[Dict[str, Any]]] = None  # 🔥 NOVO
    ) -> Dict[str, Any]:
        """
        Salva resposta do assistente com contexto completo.
        Agora suporta imagens geradas pelo assistente.
        """
        try:
            # 1. Preparar metadados
            memory_metadata = {
                "source": "chat_streaming",
                "flow_type": flow_type,
                "saved_at": datetime.utcnow().isoformat()
            }

            # 🔥 NOVO: Adicionar info de imagens ao metadata
            if images:
                memory_metadata["has_images"] = True
                memory_metadata["images_count"] = len(images)

            # 2. Adicionar informações do modelo se disponível
            if model_info:
                if isinstance(model_info, dict):
                    memory_metadata["model"] = {
                        "id": model_info.get("model_id"),
                        "name": model_info.get("model_name"),
                        "provider": model_info.get("provider_name")
                    }
                    # 🔥 NOVO: Adicionar info dos modelos de imagem
                    if "image_models" in model_info:
                        memory_metadata["image_models"] = model_info.get("image_models", [])
                else:
                    memory_metadata["model"] = str(model_info)

            # 3. Preparar attachments (se arquivos gerados pelo assistente)
            attachments = None
            if files_dict and files_dict.get("files"):
                attachments = self._prepare_attachments_from_files(
                    files_dict,
                    source="assistant_generated"
                )

            # 4. Salvar no Memory (principal)
            memory_message_id = self.add_assistant_message(
                session_id=session_id,
                content=content,
                metadata=memory_metadata,
                images=images  # 🔥 NOVO
            )

            # 5. Salvar no chat_messages (legacy/UI)
            chat_metadata = {
                "source": "chat_streaming",
                "memory_id": memory_message_id,
                "flow_type": flow_type,
                "memory_service": "v1"
            }

            # Copiar metadados do modelo
            if "model" in memory_metadata:
                chat_metadata["model"] = memory_metadata["model"]
            
            # 🔥 NOVO: Adicionar info de imagens ao chat_metadata
            if images:
                chat_metadata["has_images"] = True
                chat_metadata["images_count"] = len(images)
                if "image_models" in memory_metadata:
                    chat_metadata["image_models"] = memory_metadata["image_models"]

            chat_message_id = self._save_to_chat_messages(
                session_id=session_id,
                sender="assistant",
                content=content,
                user_id=user_id,
                metadata=chat_metadata,
                attachments=attachments,
                images=images  # 🔥 NOVO
            )

            logger.info(
                f"✅ Resposta do assistente salva | Flow: {flow_type} | "
                f"Memory: {memory_message_id}, Chat: {chat_message_id}"
            )

            return {
                "success": True,
                "memory_id": memory_message_id,
                "chat_id": chat_message_id,
                "session_id": session_id,
                "model_info": model_info,
                "flow_type": flow_type,
                "has_images": images is not None,  # 🔥 NOVO
                "images_count": len(images) if images else 0  # 🔥 NOVO
            }

        except Exception as e:
            logger.error(f"❌ Erro ao salvar resposta do assistente: {e}")
            return {
                "success": False,
                "error": str(e),
                "memory_id": None,
                "chat_id": None
            }

    async def get_or_create_session_memory(
        self,
        user_id: str,
        agent_id: str,
        existing_session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Obtém ou cria memória para sessão.
        Unifica a lógica que estava no ChatStreamingService.
        """
        try:
            if existing_session_id:
                logger.info(f"🔍 Buscando sessão existente: {existing_session_id}")

                # Verificar se já tem memória
                if self.session_has_memory(existing_session_id):
                    logger.info(f"✅ Sessão já tem memória: {existing_session_id}")
                    memory = self.get_memory_for_session(existing_session_id)
                    
                    # 🔥 NOVO: Verificar se tem imagens
                    has_images = memory.get("metadata", {}).get("has_images", False) if memory else False
                    
                    return {
                        "session_id": existing_session_id,
                        "is_new_session": False,
                        "has_existing_memory": True,
                        "memory_data": memory,
                        "needs_title_generation": False,
                        "has_images": has_images  # 🔥 NOVO
                    }
                else:
                    # Criar memória para sessão existente
                    logger.info(f"🆕 Criando memória para sessão existente: {existing_session_id}")
                    success = self.create_memory_for_session(
                        session_id=existing_session_id,
                        user_id=user_id,
                        agent_id=agent_id,
                        is_new=False,
                        metadata={
                            "source": "existing_session_retroactive",
                            "created_at": datetime.utcnow().isoformat(),
                            **(metadata or {})
                        }
                    )

                    return {
                        "session_id": existing_session_id,
                        "is_new_session": False,
                        "has_existing_memory": not success,
                        "memory_created": success,
                        "needs_title_generation": True,
                        "has_images": False  # 🔥 NOVO
                    }
            else:
                # Nova sessão
                new_session_id = str(uuid4())
                logger.info(f"🆕 Criando nova sessão com memória: {new_session_id}")

                success = self.create_memory_for_session(
                    session_id=new_session_id,
                    user_id=user_id,
                    agent_id=agent_id,
                    is_new=True,
                    metadata={
                        "source": "new_session_auto",
                        "created_at": datetime.utcnow().isoformat(),
                        "needs_title_generation": True,
                        **(metadata or {})
                    }
                )

                return {
                    "session_id": new_session_id,
                    "is_new_session": True,
                    "has_existing_memory": False,
                    "memory_created": success,
                    "needs_title_generation": True,
                    "has_images": False  # 🔥 NOVO
                }

        except Exception as e:
            logger.error(f"❌ Erro ao obter/criar memória da sessão: {e}")
            raise

    async def get_session_messages_for_ui(
        self,
        session_id: str,
        limit: int = 100,
        include_images: bool = True  # 🔥 NOVO
    ) -> Dict[str, Any]:
        """
        Recupera mensagens formatadas para UI de ambas as fontes.
        Prioriza chat_messages para compatibilidade.
        Agora inclui imagens se disponíveis.
        """
        try:
            # 1. Buscar de chat_messages (primary para UI)
            chat_messages = list(self.chat_messages_collection.find(
                {"session_id": session_id},
                sort=[("message_number", 1)]
            ).limit(limit))

            formatted_messages = []
            seen_ids = set()

            for msg in chat_messages:
                try:
                    message_id = str(msg.get("_id", ""))

                    if message_id in seen_ids:
                        continue

                    seen_ids.add(message_id)

                    formatted_msg = {
                        "id": message_id,
                        "session_id": msg.get("session_id", session_id),
                        "sender": msg.get("sender", "user"),
                        "content": msg.get("content", ""),
                        "timestamp": msg.get("timestamp", datetime.utcnow()),
                        "message_number": msg.get("message_number", 0),
                        "edited": msg.get("edited", False),
                        "metadata": msg.get("metadata", {}),
                        "updated_at": msg.get("updated_at"),
                        "user_id": msg.get("user_id"),
                        "attachments": msg.get("attachments", [])
                    }

                    # 🔥 NOVO: Incluir imagens se existirem
                    if include_images and "images" in msg:
                        formatted_msg["images"] = msg.get("images", [])
                        formatted_msg["has_images"] = True
                        formatted_msg["images_count"] = len(msg.get("images", []))
                    elif "has_images" in msg.get("metadata", {}):
                        formatted_msg["has_images"] = msg["metadata"]["has_images"]
                        formatted_msg["images_count"] = msg["metadata"].get("images_count", 0)

                    formatted_messages.append(formatted_msg)

                except Exception as format_error:
                    logger.debug(f"⚠️ Erro ao formatar mensagem: {format_error}")
                    continue

            # 2. Buscar da memória (para verificação)
            memory_history = self.get_conversation_history(
                session_id, 
                limit=limit,
                include_images=include_images
            )

            # 🔥 NOVO: Verificar se tem imagens
            has_images = any(msg.get("has_images", False) for msg in memory_history)

            return {
                "session_id": session_id,
                "messages": formatted_messages,
                "sources": {
                    "chat_messages_count": len(chat_messages),
                    "memory_messages_count": len(memory_history),
                    "formatted_count": len(formatted_messages)
                },
                "memory_available": len(memory_history) > 0,
                "total_messages": len(formatted_messages),
                "has_images": has_images,  # 🔥 NOVO
                "images_count": sum(msg.get("images_count", 0) for msg in memory_history if msg.get("has_images"))  # 🔥 NOVO
            }

        except Exception as e:
            logger.error(f"❌ Erro ao buscar mensagens para UI: {e}")
            return {
                "session_id": session_id,
                "messages": [],
                "sources": {"error": str(e)},
                "memory_available": False,
                "total_messages": 0,
                "has_images": False
            }

    # 🔥 NOVO: Buscar apenas mensagens com imagens
    async def get_messages_with_images(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Recupera apenas mensagens que contêm imagens."""
        try:
            return self.memory_dao.get_messages_with_images(session_id, limit)
        except Exception as e:
            logger.error(f"❌ Erro ao buscar mensagens com imagens: {e}")
            return []

    async def clear_session_completely(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Limpa completamente uma sessão de ambas as coleções.
        """
        try:
            # 1. Limpar memória
            memory_cleared = self.clear_session_memory(session_id)

            # 2. Limpar chat_messages
            chat_cleared = False
            chat_count = 0
            try:
                result = self.chat_messages_collection.delete_many({"session_id": session_id})
                chat_cleared = result.deleted_count > 0
                chat_count = result.deleted_count
                logger.info(f"🗑️ Removidas {chat_count} mensagens de chat_messages")
            except Exception as chat_error:
                logger.error(f"❌ Erro ao limpar chat_messages: {chat_error}")
                chat_cleared = False

            return {
                "session_id": session_id,
                "success": memory_cleared or chat_cleared,
                "details": {
                    "memory_cleared": memory_cleared,
                    "chat_messages_cleared": chat_cleared,
                    "chat_messages_count": chat_count
                }
            }

        except Exception as e:
            logger.error(f"❌ Erro ao limpar sessão completamente: {e}")
            return {
                "session_id": session_id,
                "success": False,
                "error": str(e)
            }

    # ============================================================================
    # MÉTODOS AUXILIARES (atualizados)
    # ============================================================================

    def _prepare_attachments_from_files(
        self,
        files_dict: Dict[str, Any],
        source: str = "user_uploaded"
    ) -> List[Dict[str, Any]]:
        """Prepara attachments para salvamento."""
        if not files_dict or not files_dict.get("files"):
            return None

        attachments = []
        for file_info in files_dict["files"]:
            attachment = {
                "filename": file_info.get("filename", "arquivo"),
                "content_type": file_info.get("content_type", "application/octet-stream"),
                "size": file_info.get("size", 0),
                "source": source,
                "processed_at": datetime.utcnow().isoformat()
            }

            if source == "assistant_generated":
                attachment["reference"] = True

            attachments.append(attachment)

        return attachments

    def _save_to_chat_messages(
        self,
        session_id: str,
        sender: str,
        content: str,
        user_id: str = None,
        metadata: Optional[Dict[str, Any]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        images: Optional[List[Dict[str, Any]]] = None  # 🔥 NOVO
    ) -> Optional[str]:
        """
        Salva mensagem na coleção chat_messages (legacy/UI).
        Agora suporta imagens.
        """
        try:
            message_id = str(uuid4())
            now = datetime.utcnow()

            message_data = {
                "_id": message_id,
                "session_id": session_id,
                "sender": sender,
                "content": content,
                "timestamp": now,
                "message_number": self._get_next_chat_message_number(session_id),
                "edited": False,
                "updated_at": None
            }

            if user_id:
                message_data["user_id"] = user_id

            if metadata:
                message_data["metadata"] = metadata

            if attachments:
                message_data["attachments"] = attachments
                logger.debug(f"💾 Mensagem com {len(attachments)} anexo(s)")

            # 🔥 NOVO: Adicionar imagens se existirem
            if images:
                message_data["images"] = images
                message_data["has_images"] = True
                message_data["images_count"] = len(images)
                logger.info(f"📸 Mensagem com {len(images)} imagem(ns) salva em chat_messages")

            result = self.chat_messages_collection.insert_one(message_data)

            if result.acknowledged:
                logger.debug(f"💾 Mensagem salva em chat_messages - Sessão: {session_id}, Sender: {sender}")
                return message_id
            else:
                logger.warning(f"⚠️ Não foi possível salvar em chat_messages - Sessão: {session_id}")
                return None

        except Exception as e:
            logger.error(f"❌ Erro ao salvar em chat_messages: {e}")
            return None

    def _get_next_chat_message_number(self, session_id: str) -> int:
        """Obtém o próximo número de mensagem para chat_messages."""
        try:
            last_message = self.chat_messages_collection.find_one(
                {"session_id": session_id},
                sort=[("message_number", -1)]
            )

            if last_message:
                return last_message.get("message_number", 0) + 1
            return 1

        except Exception as e:
            logger.warning(f"⚠️ Erro ao buscar próximo número de mensagem: {e}")
            return 1

    # ============================================================================
    # MÉTODOS DE RECUPERAÇÃO (atualizados)
    # ============================================================================

    def get_conversation_history(
        self,
        session_id: str,
        limit: int = 50,
        offset: int = 0,
        include_images: bool = True  # 🔥 NOVO
    ) -> List[Dict[str, Any]]:
        """Recupera histórico da conversa."""
        try:
            return self.memory_dao.get_conversation_history(
                session_id=session_id,
                limit=limit,
                offset=offset,
                include_images=include_images
            )
            
        except Exception as e:
            logger.error(f"❌ Erro ao recuperar histórico: {e}")
            return []

    def get_last_messages(
        self,
        session_id: str,
        count: int = 10,
        include_images: bool = True  # 🔥 NOVO
    ) -> List[Dict[str, Any]]:
        """Recupera as últimas N mensagens da conversa."""
        try:
            return self.memory_dao.get_last_messages(
                session_id, 
                count=count,
                include_images=include_images
            )
            
        except Exception as e:
            logger.error(f"❌ Erro ao recuperar últimas mensagens: {e}")
            return []

    def get_message_count(
        self,
        session_id: str
    ) -> int:
        """Conta total de mensagens na sessão."""
        try:
            return self.memory_dao.get_message_count(session_id)
        except Exception as e:
            logger.error(f"❌ Erro ao contar mensagens: {e}")
            return 0

    # 🔥 NOVO: Obter estatísticas da sessão
    def get_session_stats(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """Obtém estatísticas da memória da sessão."""
        try:
            return self.memory_dao.get_memory_stats(session_id)
        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas: {e}")
            return {"error": str(e)}

    # ============================================================================
    # MÉTODOS COMPATIBILIDADE (mantidos)
    # ============================================================================

    def add_message(
        self,
        session_id: str,
        sender: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        images: Optional[List[Dict[str, Any]]] = None  # 🔥 NOVO
    ) -> Optional[str]:
        """Adiciona mensagem genérica à memória."""
        try:
            message_id = self.memory_dao.add_message_to_memory(
                session_id=session_id,
                sender=sender,
                content=content,
                metadata=metadata or {},
                images=images  # 🔥 NOVO
            )
            
            if message_id:
                logger.debug(f"✅ Mensagem de '{sender}' salva na memória - Sessão: {session_id}")
            
            return message_id
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar mensagem: {e}")
            return None