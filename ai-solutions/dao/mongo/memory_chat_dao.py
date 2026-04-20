# dao/mongo/v1/memory_chat_dao.py

from typing import Dict, List, Optional, Any
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId
from uuid import UUID
import logging

from pymongo.database import Database
from pymongo.collection import Collection

logger = logging.getLogger(__name__)


class MemoryDAO:
    """
    DAO para gerenciamento de memória de chat.
    Usa a coleção memory_chat para armazenar mensagens.
    Versão atualizada com suporte a imagens e correção do erro de metadata.
    """
    
    def __init__(self, db: Database):
        self.memory_collection: Collection = db["memory_chat"]
        self.db = db
        
        # Criar índices
        self._create_memory_indexes()
        
        logger.info("✅ MemoryDAO inicializado")

    # ============================================================================
    # INICIALIZAÇÃO
    # ============================================================================

    def _create_memory_indexes(self) -> None:
        """Cria índices para otimizar a coleção memory_chat."""
        try:
            # Índice para busca rápida por session_id
            self.memory_collection.create_index([("session_id", 1)], unique=False)
        
            # Índice para busca por timestamp
            self.memory_collection.create_index([("updated_at", -1)])
            
            # Índice para busca por sessões com imagens
            self.memory_collection.create_index([("metadata.has_images", 1)])
            
            logger.debug("✅ Índices da memory_collection criados")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao criar índices das memórias: {e}")

    # ============================================================================
    # MÉTODOS PRINCIPAIS
    # ============================================================================

    def get_memory_by_session_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca a memória pelo session_id
        """
        try:
            # Validar se é um UUID válido
            UUID(session_id)
        except ValueError:
            logger.warning(f"⚠️ session_id inválido: {session_id}")
            return None
        
        try:
            memory = self.memory_collection.find_one({"session_id": session_id})
            return self._serialize_document(memory) if memory else None
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar memória: {e}")
            return None

    def create_memory(
        self, 
        session_id: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Cria uma nova memória para uma sessão
        """
        try:
            UUID(session_id)
        except ValueError:
            logger.error(f"❌ session_id inválido: {session_id}")
            raise ValueError("session_id inválido")
        
        now = datetime.utcnow()
        default_metadata = {
            "max_messages": 50,
            "version": "v1",
            "created_at": now,
            "source": "memory_dao",
            "has_images": False,
            "images_count": 0
        }
        
        if metadata:
            default_metadata.update(metadata)
        
        memory_data = {
            "session_id": session_id,
            "short_memory": {},
            "total_messages": 0,
            "created_at": now,
            "updated_at": now,
            "metadata": default_metadata
        }
        
        try:
            result = self.memory_collection.insert_one(memory_data)
            if not result.acknowledged:
                logger.error(f"❌ Falha ao criar memória para sessão: {session_id}")
                return None
            
            created_memory = self.memory_collection.find_one({"_id": result.inserted_id})
            logger.info(f"✅ Memória criada para sessão: {session_id}")
            return self._serialize_document(created_memory)
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar memória: {e}")
            return None

    def add_message_to_memory(
        self, 
        session_id: str, 
        sender: str, 
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        images: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[str]:
        """
        Adiciona uma nova mensagem à memória da sessão
        Agora suporta imagens.
        Retorna o message_id ou None se não for possível
        """
        try:
            UUID(session_id)
        except ValueError:
            logger.warning(f"⚠️ session_id inválido: {session_id}")
            return None
        
        try:
            now = datetime.utcnow()
            
            # Buscar memória atual
            memory = self.memory_collection.find_one({"session_id": session_id})
            
            if not memory:
                # Se não existe memória, criar uma nova
                logger.info(f"📝 Criando memória para nova sessão: {session_id}")
                self.create_memory(session_id, metadata={"auto_created": True})
                memory = self.memory_collection.find_one({"session_id": session_id})
                
                if not memory:
                    logger.error(f"❌ Não foi possível criar memória para sessão: {session_id}")
                    return None
            
            # Obter próximo número de mensagem
            total_messages = memory.get("total_messages", 0)
            next_message_num = total_messages + 1
            
            # Criar objeto da mensagem
            message_id = f"msg_{session_id}_{next_message_num}_{int(now.timestamp())}"
            message_data = {
                "message_id": message_id,
                "sender": sender,
                "content": content,
                "timestamp": now,
                "message_number": next_message_num,
                "metadata": metadata or {}
            }
            
            # Adicionar imagens se existirem
            has_images = False
            images_count = 0
            if images:
                message_data["images"] = images
                message_data["has_images"] = True
                message_data["images_count"] = len(images)
                has_images = True
                images_count = len(images)
                logger.info(f"📸 Mensagem com {len(images)} imagem(ns) adicionada à memória")
            
            # 🔥 CORREÇÃO: Construir update_data de forma segura
            update_data = {
                f"short_memory.{next_message_num}": message_data,
                "total_messages": next_message_num,
                "updated_at": now
            }
            
            # 🔥 CORREÇÃO: Atualizar metadata sem conflito
            # Primeiro, pegar a metadata atual
            current_metadata = memory.get("metadata", {})
            
            # Criar nova metadata baseada na atual
            new_metadata = current_metadata.copy()
            
            # Adicionar/atualizar campos de imagem
            if has_images:
                new_metadata["has_images"] = True
                new_metadata["images_count"] = new_metadata.get("images_count", 0) + images_count
            
            # Se houver metadata adicional fornecida, mesclar
            if metadata:
                # Mesclar sem sobrescrever campos importantes
                for key, value in metadata.items():
                    if key not in ["has_images", "images_count"]:  # Não sobrescrever campos de imagem
                        new_metadata[key] = value
            
            # Adicionar a metadata atualizada ao update_data
            update_data["metadata"] = new_metadata
            
            # Executar update
            result = self.memory_collection.update_one(
                {"session_id": session_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.debug(f"✅ Mensagem adicionada à memória - Sessão: {session_id}, Sender: {sender}")
                return message_id
            else:
                logger.warning(f"⚠️ Não foi possível adicionar mensagem à memória - Sessão: {session_id}")
                return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar mensagem à memória: {e}")
            return None

    def update_message_in_memory(
        self,
        session_id: str,
        message_number: int,
        content: str,
        edited: bool = True
    ) -> bool:
        """
        Atualiza uma mensagem existente na memória
        """
        try:
            UUID(session_id)
        except ValueError:
            logger.warning(f"⚠️ session_id inválido: {session_id}")
            return False
        
        try:
            now = datetime.utcnow()
            
            # Verificar se a mensagem existe
            memory = self.memory_collection.find_one({
                "session_id": session_id,
                f"short_memory.{message_number}": {"$exists": True}
            })
            
            if not memory:
                logger.warning(f"⚠️ Mensagem {message_number} não encontrada na sessão {session_id}")
                return False
            
            # Atualizar a mensagem
            update_data = {
                f"short_memory.{message_number}.content": content,
                f"short_memory.{message_number}.edited": edited,
                f"short_memory.{message_number}.timestamp": now,
                "updated_at": now
            }
            
            result = self.memory_collection.update_one(
                {"session_id": session_id},
                {"$set": update_data}
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"✅ Mensagem atualizada - Sessão: {session_id}, Número: {message_number}")
            else:
                logger.warning(f"⚠️ Não foi possível atualizar mensagem - Sessão: {session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar mensagem: {e}")
            return False

    def delete_memory_by_session_id(self, session_id: str) -> bool:
        """
        Remove a memória de uma sessão
        """
        try:
            UUID(session_id)
        except ValueError:
            logger.warning(f"⚠️ session_id inválido: {session_id}")
            return False
        
        try:
            result = self.memory_collection.delete_one({"session_id": session_id})
            success = result.deleted_count > 0
            
            if success:
                logger.info(f"✅ Memória removida - Sessão: {session_id}")
            else:
                logger.warning(f"⚠️ Memória não encontrada - Sessão: {session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Erro ao remover memória: {e}")
            return False

    # ============================================================================
    # MÉTODOS DE CONSULTA
    # ============================================================================

    def get_conversation_history(
        self, 
        session_id: str, 
        limit: Optional[int] = None,
        offset: int = 0,
        include_images: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retorna o histórico de conversa em formato ordenado
        Agora inclui imagens se disponíveis.
        """
        try:
            memory = self.get_memory_by_session_id(session_id)
            if not memory or "short_memory" not in memory:
                return []
            
            short_memory = memory["short_memory"]
            
            # Converter para lista ordenada por message_number
            conversation = []
            for msg_num_str, message_data in short_memory.items():
                try:
                    msg_num = int(msg_num_str)
                    msg_dict = {
                        "message_id": message_data.get("message_id", f"msg_{msg_num}"),
                        "message_number": msg_num,
                        "sender": message_data.get("sender", "unknown"),
                        "content": message_data.get("content", ""),
                        "timestamp": message_data.get("timestamp"),
                        "edited": message_data.get("edited", False),
                        "metadata": message_data.get("metadata", {})
                    }
                    
                    # Incluir imagens se existirem
                    if include_images and "images" in message_data:
                        msg_dict["images"] = message_data.get("images", [])
                        msg_dict["has_images"] = message_data.get("has_images", False)
                        msg_dict["images_count"] = message_data.get("images_count", 0)
                    
                    conversation.append(msg_dict)
                except (ValueError, TypeError):
                    continue
            
            # Ordenar por message_number (crescente)
            conversation.sort(key=lambda x: x["message_number"])
            
            # Aplicar offset e limite
            if offset > 0:
                conversation = conversation[offset:]
            
            if limit and limit > 0:
                conversation = conversation[:limit]
            
            return conversation
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar histórico: {e}")
            return []

    def get_last_messages(
        self, 
        session_id: str, 
        count: int = 10,
        include_images: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retorna as últimas N mensagens da conversa
        """
        try:
            history = self.get_conversation_history(
                session_id, 
                limit=count,
                include_images=include_images
            )
            # Ordenar por timestamp decrescente para últimas mensagens
            history.sort(key=lambda x: x.get("timestamp") or datetime.min, reverse=True)
            return history[:count]
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar últimas mensagens: {e}")
            return []

    def get_message_count(self, session_id: str) -> int:
        """
        Retorna o total de mensagens na sessão
        """
        try:
            memory = self.get_memory_by_session_id(session_id)
            if memory:
                return memory.get("total_messages", 0)
            return 0
            
        except Exception as e:
            logger.error(f"❌ Erro ao contar mensagens: {e}")
            return 0

    def get_messages_with_images(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Retorna apenas mensagens que contêm imagens.
        """
        try:
            memory = self.get_memory_by_session_id(session_id)
            if not memory or "short_memory" not in memory:
                return []
            
            short_memory = memory["short_memory"]
            messages_with_images = []
            
            for msg_num_str, message_data in short_memory.items():
                if message_data.get("has_images", False) or "images" in message_data:
                    try:
                        msg_num = int(msg_num_str)
                        msg_dict = {
                            "message_id": message_data.get("message_id", f"msg_{msg_num}"),
                            "message_number": msg_num,
                            "sender": message_data.get("sender", "unknown"),
                            "content": message_data.get("content", ""),
                            "timestamp": message_data.get("timestamp"),
                            "images": message_data.get("images", []),
                            "has_images": True,
                            "images_count": message_data.get("images_count", len(message_data.get("images", []))),
                            "metadata": message_data.get("metadata", {})
                        }
                        messages_with_images.append(msg_dict)
                    except (ValueError, TypeError):
                        continue
            
            # Ordenar por message_number
            messages_with_images.sort(key=lambda x: x["message_number"])
            
            # Aplicar limite
            if limit and limit > 0:
                messages_with_images = messages_with_images[:limit]
            
            return messages_with_images
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar mensagens com imagens: {e}")
            return []

    # ============================================================================
    # MÉTODOS DE MANUTENÇÃO
    # ============================================================================

    def cleanup_old_messages(
        self, 
        session_id: str, 
        keep_last: int = 50
    ) -> bool:
        """
        Remove mensagens antigas, mantendo apenas as últimas 'keep_last' mensagens
        Preserva imagens se existirem.
        """
        try:
            memory = self.get_memory_by_session_id(session_id)
            if not memory or "short_memory" not in memory:
                return False
            
            short_memory = memory["short_memory"]
            
            if len(short_memory) <= keep_last:
                return True
            
            # Ordenar mensagens por número
            sorted_messages = sorted(
                [(int(k), v) for k, v in short_memory.items() if k.isdigit()],
                key=lambda x: x[0]
            )
            
            # Manter apenas as últimas 'keep_last' mensagens
            messages_to_keep = sorted_messages[-keep_last:]
            
            # Reconstruir o short_memory
            new_short_memory = {}
            has_images = False
            total_images = 0
            
            for i, (_, msg_data) in enumerate(messages_to_keep, 1):
                new_short_memory[str(i)] = msg_data
                new_short_memory[str(i)]["message_number"] = i
                
                # Contar imagens
                if msg_data.get("has_images", False):
                    has_images = True
                    total_images += msg_data.get("images_count", 1)
            
            # Atualizar no banco
            now = datetime.utcnow()
            update_data = {
                "short_memory": new_short_memory,
                "total_messages": len(messages_to_keep),
                "updated_at": now
            }
            
            # Atualizar metadata de imagens
            if "metadata" in memory:
                new_metadata = memory["metadata"].copy()
                new_metadata["has_images"] = has_images
                new_metadata["images_count"] = total_images
                update_data["metadata"] = new_metadata
            
            result = self.memory_collection.update_one(
                {"session_id": session_id},
                {"$set": update_data}
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"✅ Memória limpa - Sessão: {session_id}, Mantidas: {len(messages_to_keep)}")
            else:
                logger.warning(f"⚠️ Não foi possível limpar memória - Sessão: {session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Erro ao limpar memória: {e}")
            return False

    # ============================================================================
    # MÉTODOS UTILITÁRIOS
    # ============================================================================

    def _serialize_document(self, doc: dict) -> Dict[str, Any]:
        """Serializa documento MongoDB para JSON seguro."""
        if not doc:
            return {}
        
        result = doc.copy()
        
        # Converter ObjectId para string
        if "_id" in result and isinstance(result["_id"], ObjectId):
            result["_id"] = str(result["_id"])
        
        # Converter timestamps para ISO string
        for field in ["created_at", "updated_at"]:
            if field in result and isinstance(result[field], datetime):
                result[field] = result[field].isoformat()
        
        # Serializar timestamps dentro de short_memory
        if "short_memory" in result and isinstance(result["short_memory"], dict):
            for msg_num, msg_data in result["short_memory"].items():
                if isinstance(msg_data, dict):
                    if "timestamp" in msg_data and isinstance(msg_data["timestamp"], datetime):
                        msg_data["timestamp"] = msg_data["timestamp"].isoformat()
                    
                    # Garantir que imagens estejam serializadas
                    if "images" in msg_data and isinstance(msg_data["images"], list):
                        for img in msg_data["images"]:
                            if "timestamp" in img and isinstance(img["timestamp"], datetime):
                                img["timestamp"] = img["timestamp"].isoformat()
        
        return result

    def session_has_memory(self, session_id: str) -> bool:
        """Verifica se a sessão tem memória."""
        try:
            memory = self.get_memory_by_session_id(session_id)
            return memory is not None
        except Exception:
            return False

    def session_has_images(self, session_id: str) -> bool:
        """Verifica se a sessão tem imagens na memória."""
        try:
            memory = self.get_memory_by_session_id(session_id)
            if not memory:
                return False
            return memory.get("metadata", {}).get("has_images", False)
        except Exception:
            return False

    def get_memory_stats(self, session_id: str) -> Dict[str, Any]:
        """Obtém estatísticas da memória."""
        try:
            memory = self.get_memory_by_session_id(session_id)
            if not memory:
                return {"exists": False, "session_id": session_id}
            
            history = self.get_conversation_history(session_id, limit=1000)
            
            # Contar por tipo
            user_count = sum(1 for msg in history if msg.get("sender") == "user")
            assistant_count = sum(1 for msg in history if msg.get("sender") == "assistant")
            other_count = len(history) - user_count - assistant_count
            
            # Contar mensagens com imagens
            messages_with_images = self.get_messages_with_images(session_id, limit=1000)
            images_count = len(messages_with_images)
            
            return {
                "exists": True,
                "session_id": session_id,
                "total_messages": len(history),
                "messages_with_images": images_count,
                "has_images": images_count > 0,
                "memory_breakdown": {
                    "user": user_count,
                    "assistant": assistant_count,
                    "other": other_count
                },
                "created_at": memory.get("created_at"),
                "updated_at": memory.get("updated_at"),
                "metadata": memory.get("metadata", {})
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas: {e}")
            return {"error": str(e)}

    # ============================================================================
    # MÉTODOS DE HEALTH CHECK
    # ============================================================================

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do DAO."""
        try:
            count = self.memory_collection.count_documents({})
            
            # Contar documentos com imagens
            images_count = self.memory_collection.count_documents({"metadata.has_images": True})
            
            return {
                "status": "healthy",
                "collection": "memory_chat",
                "document_count": count,
                "documents_with_images": images_count,
                "timestamp": datetime.utcnow().isoformat(),
                "message": "MemoryDAO funcionando corretamente"
            }
        except Exception as e:
            logger.error(f"❌ Erro no health check: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }