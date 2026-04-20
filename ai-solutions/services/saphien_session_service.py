# services/v1/saphien_session_service.py
"""
Serviço de gerenciamento de sessões para o widget Saphien.
Similar ao TelegramSessionService, mas adaptado para web.
Responsável por:
  - Criar/recuperar sessões para visitantes
  - Gerenciar o agente ativo baseado em triggers
  - Sincronizar agentes do canal com a sessão
  - Gerenciar mensagens da sessão
"""
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger
from datetime import datetime

from dao.mongo.saphien_session_dao import SaphienSessionDAO
from dao.mongo.saphien_messages_dao import SaphienMessagesDAO


class SaphienSessionService:
    """Gerencia sessões de conversa do widget Saphien."""

    # =====================================================
    # SESSÕES
    # =====================================================

    @staticmethod
    def get_or_create_session(
        widget_token: str,
        session_id: str,
        channel_agents: List[Dict[str, Any]],
        user_info: Optional[Dict[str, Any]] = None
    ) -> Tuple[Optional[Dict[str, Any]], bool]:
        """
        Busca ou cria uma sessão para o visitante.
        
        Args:
            widget_token: Token do widget (identifica o canal)
            session_id: ID único da sessão (gerado pelo frontend)
            channel_agents: Lista de agentes do canal
            user_info: Informações do usuário (URL, userAgent, IP)
        
        Returns:
            Tuple (session_dict, is_new)
        """
        try:
            # Busca sessão existente para este visitante neste canal
            session = SaphienSessionDAO.find_session(widget_token, session_id)
            
            if session:
                # Atualiza última atividade
                SaphienSessionDAO.update_last_activity(session["_id"])
                logger.debug(f"[SAPHIEN SESSION] Sessão existente: {widget_token[:15]}.../{session_id}")
                return session, False
            
            # Cria nova sessão
            new_session = SaphienSessionDAO.create_session(
                widget_token=widget_token,
                session_id=session_id,
                user_info=user_info,
                agents=channel_agents,
            )
            
            if new_session:
                logger.info(f"[SAPHIEN SESSION] Nova sessão criada: {widget_token[:15]}.../{session_id}")
                return new_session, True
            
            return None, False
            
        except Exception as e:
            logger.error(f"[SAPHIEN SESSION] Erro ao obter/criar sessão: {e}")
            return None, False

    @staticmethod
    def resolve_and_update_agent(
        session: Dict[str, Any],
        channel_data: Dict[str, Any],
        message_text: str
    ) -> Optional[Dict[str, Any]]:
        """
        Resolve qual agente usar baseado no trigger e atualiza a sessão se necessário.
        
        Regras:
        1. Se a mensagem contém um trigger que corresponde a um agente, troca para aquele agente
        2. Se não há trigger correspondente, mantém o agente atual (se existir)
        3. Se não há agente atual, usa o primeiro agente ativo sem trigger (fallback)
        
        Args:
            session: Dados da sessão
            channel_data: Dados do canal
            message_text: Texto da mensagem
        
        Returns:
            Agente selecionado ou None
        """
        channel_agents = channel_data.get("agents", [])
        active_agents = [a for a in channel_agents if a.get("status") == "active"]
        
        if not active_agents:
            logger.warning("[SAPHIEN SESSION] Nenhum agente ativo no canal")
            return None
        
        session_uuid = session.get("_id")
        
        # Obtém o agente ativo atual da sessão
        current_active = session.get("active_agent", {})
        current_agent_id = current_active.get("id")
        
        # Procura por trigger correspondente
        matched_agent = None
        matched_trigger = None
        
        for agent in active_agents:
            trigger_config = agent.get("trigger_config", {})
            if trigger_config.get("enabled"):
                trigger = trigger_config.get("trigger", "")
                operator = trigger_config.get("operator", "contains")
                case_sensitive = trigger_config.get("case_sensitive", False)
                
                if not trigger:
                    continue
                
                compare_text = message_text if case_sensitive else message_text.lower()
                compare_trigger = trigger if case_sensitive else trigger.lower()
                
                matched = False
                if operator == "contains":
                    matched = compare_trigger in compare_text
                elif operator == "equals":
                    matched = compare_text == compare_trigger
                elif operator == "startswith":
                    matched = compare_text.startswith(compare_trigger)
                elif operator == "endswith":
                    matched = compare_text.endswith(compare_trigger)
                
                if matched:
                    matched_agent = agent
                    matched_trigger = trigger
                    break
        
        # Se encontrou trigger correspondente
        if matched_agent:
            agent_id = matched_agent.get("id")
            
            # Se o agente mudou, atualiza a sessão
            if current_agent_id != agent_id:
                SaphienSessionDAO.update_active_agent(
                    session_uuid,
                    agent_id,
                    matched_trigger,
                )
                logger.info(f"[SAPHIEN SESSION] Agente alterado: {current_agent_id} → {agent_id} (trigger: {matched_trigger})")
            
            # Atualiza last_used do agente
            SaphienSessionDAO.update_agent_last_used(session_uuid, agent_id)
            
            return matched_agent
        
        # Se tem agente atual, mantém ele
        if current_agent_id:
            for agent in active_agents:
                if agent.get("id") == current_agent_id:
                    SaphienSessionDAO.update_agent_last_used(session_uuid, current_agent_id)
                    return agent
        
        # Se só tem um agente, retorna ele
        if len(active_agents) == 1:
            agent = active_agents[0]
            SaphienSessionDAO.update_active_agent(
                session_uuid,
                agent.get("id"),
                agent.get("trigger_config", {}).get("trigger", ""),
            )
            SaphienSessionDAO.update_agent_last_used(session_uuid, agent.get("id"))
            return agent
        
        # Fallback: primeiro agente sem trigger
        for agent in active_agents:
            if not agent.get("trigger_config", {}).get("enabled"):
                SaphienSessionDAO.update_active_agent(
                    session_uuid,
                    agent.get("id"),
                    "",
                )
                SaphienSessionDAO.update_agent_last_used(session_uuid, agent.get("id"))
                return agent
        
        # Último fallback: primeiro agente da lista
        if active_agents:
            agent = active_agents[0]
            SaphienSessionDAO.update_active_agent(
                session_uuid,
                agent.get("id"),
                agent.get("trigger_config", {}).get("trigger", ""),
            )
            SaphienSessionDAO.update_agent_last_used(session_uuid, agent.get("id"))
            return agent
        
        return None

    @staticmethod
    def get_agent_by_id(session: Dict[str, Any], agent_id: str) -> Optional[Dict[str, Any]]:
        """Busca um agente na lista da sessão pelo ID."""
        for agent in session.get("agents", []):
            if agent.get("id") == agent_id:
                return agent
        return None

    @staticmethod
    def clean_prompt(message_text: str, agent: Dict[str, Any]) -> str:
        """
        Remove o trigger do prompt para enviar ao agente.
        """
        trigger_config = agent.get("trigger_config", {})
        trigger = trigger_config.get("trigger", "")
        
        if not trigger or not trigger_config.get("enabled", False):
            return message_text.strip()
        
        case_sensitive = trigger_config.get("case_sensitive", False)
        operator = trigger_config.get("operator", "contains")
        
        if operator == "contains" and trigger in (message_text if case_sensitive else message_text.lower()):
            cleaned = message_text.replace(trigger, "").strip()
            return cleaned if cleaned else message_text
        
        return message_text.strip()

    @staticmethod
    def update_session_activity(session_uuid: str) -> None:
        """Atualiza timestamp de última atividade da sessão."""
        try:
            SaphienSessionDAO.update_last_activity(session_uuid)
        except Exception as e:
            logger.warning(f"[SAPHIEN SESSION] Erro ao atualizar atividade: {e}")

    @staticmethod
    def sync_agents_from_channel(session_uuid: str, channel_agents: List[Dict]) -> bool:
        """Sincroniza agentes do canal com a sessão."""
        try:
            session = SaphienSessionDAO.find_session_by_id(session_uuid)
            if not session:
                return False
            
            return SaphienSessionDAO.sync_agents_from_channel(
                session.get("widget_token"),
                session.get("session_id"),
                channel_agents
            )
        except Exception as e:
            logger.error(f"[SAPHIEN SESSION] Erro ao sincronizar agentes: {e}")
            return False

    # =====================================================
    # MENSAGENS
    # =====================================================

    @staticmethod
    def save_user_message(
        session_uuid: str,
        user_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Salva mensagem do usuário no banco.
        """
        try:
            return SaphienMessagesDAO.save_user_message(
                session_id=session_uuid,
                user_id=user_id,
                content=content,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"[SAPHIEN SESSION] Erro ao salvar mensagem do usuário: {e}")
            return None

    @staticmethod
    def save_assistant_message(
        session_uuid: str,
        agent_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Salva mensagem do assistente no banco.
        """
        try:
            return SaphienMessagesDAO.save_assistant_message(
                session_id=session_uuid,
                agent_id=agent_id,
                content=content,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"[SAPHIEN SESSION] Erro ao salvar mensagem do assistente: {e}")
            return None

    @staticmethod
    def get_conversation_history(
        session_uuid: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Busca histórico da conversa formatado para o agente.
        
        Returns:
            Lista de mensagens no formato:
            [{"role": "user", "content": "...", "timestamp": ...}, ...]
        """
        try:
            return SaphienMessagesDAO.get_conversation_history(session_uuid, limit)
        except Exception as e:
            logger.error(f"[SAPHIEN SESSION] Erro ao buscar histórico: {e}")
            return []

    @staticmethod
    def get_session_messages(
        session_uuid: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Retorna todas as mensagens da sessão (sem formatação).
        """
        try:
            return SaphienMessagesDAO.get_messages_by_session(session_uuid, limit)
        except Exception as e:
            logger.error(f"[SAPHIEN SESSION] Erro ao buscar mensagens: {e}")
            return []

    @staticmethod
    def delete_session_messages(session_uuid: str) -> int:
        """
        Remove todas as mensagens de uma sessão.
        """
        try:
            return SaphienMessagesDAO.delete_messages_by_session(session_uuid)
        except Exception as e:
            logger.error(f"[SAPHIEN SESSION] Erro ao deletar mensagens: {e}")
            return 0