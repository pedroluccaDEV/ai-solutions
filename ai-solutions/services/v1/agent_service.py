from typing import Optional, List
from bson import ObjectId  # <-- ADICIONAR ESTE IMPORT
from bson.errors import InvalidId  # <-- ADICIONAR ESTE TAMBÉM
from dao.mongo.v1.agent_dao import AgentDAO
from dao.mongo.v1.chat_session_dao import ChatSessionDAO
from schemas.v1.agent_schema import AgentCreateSchema
from datetime import datetime


class AgentService:

    @staticmethod
    def create_agent(db, agent_data: AgentCreateSchema, uid: str) -> dict:
        return AgentDAO.create_agent(agent_data, uid)

    @staticmethod
    def list_agents_for_user(db, uid: str) -> List[dict]:
        """
        Retorna TODOS os agentes pertencentes ao usuário,
        sem filtros, sem agentes públicos, sem agente automático.
        """
        return AgentDAO.list_agents_raw_by_user(uid)

    @staticmethod
    def get_agent_by_id(db, agent_id: str, uid: str) -> Optional[dict]:
        # CORREÇÃO: Usar o método com verificação de usuário
        return AgentDAO.get_agent_by_id_and_user(agent_id, uid)

    @staticmethod
    def update_agent(db, agent_id: str, agent_data: AgentCreateSchema, uid: str):
        return AgentDAO.update_agent(agent_id, agent_data, uid)

    @staticmethod
    def delete_agent(db, agent_id: str, uid: str) -> bool:
        deleted = AgentDAO.delete_agent(agent_id, uid)
        if deleted:
            session_dao = ChatSessionDAO(db)
            session = session_dao.get_session_by_agent_and_user(agent_id=agent_id, user_id=uid)
            if session:
                session_dao.delete_session(session["_id"])
        return deleted

    # ADICIONAR MÉTODO DE VALIDAÇÃO QUE ESTÁ FALTANDO
    @staticmethod
    def validate_agent_references(db, agent_data: AgentCreateSchema) -> dict:
        """
        Valida se as referências (knowledgeBase, tools, mcps) existem no banco
        """
        errors = []
        
        # Validar knowledgeBase
        if agent_data.knowledgeBase:
            for kb_id in agent_data.knowledgeBase:
                try:
                    kb_doc = db.knowledge_bases.find_one({"_id": ObjectId(kb_id)})
                    if not kb_doc:
                        errors.append(f"KnowledgeBase {kb_id} não encontrada")
                except InvalidId:
                    errors.append(f"KnowledgeBase ID {kb_id} é inválido")
        
        # Validar tools
        if agent_data.tools:
            for tool_id in agent_data.tools:
                try:
                    tool_doc = db.tools.find_one({"_id": ObjectId(tool_id)})
                    if not tool_doc:
                        errors.append(f"Tool {tool_id} não encontrada")
                except InvalidId:
                    errors.append(f"Tool ID {tool_id} é inválido")
        
        # Validar mcps
        if agent_data.mcps:
            for mcp_id in agent_data.mcps:
                try:
                    mcp_doc = db.mcps.find_one({"_id": ObjectId(mcp_id)})
                    if not mcp_doc:
                        errors.append(f"MCP {mcp_id} não encontrado")
                except InvalidId:
                    errors.append(f"MCP ID {mcp_id} é inválido")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    # ADICIONAR MÉTODO DE CRIAÇÃO DE SESSÃO QUE ESTÁ FALTANDO
    @staticmethod
    async def create_agent_session(db, user_id: str, agent_id: str, org_id: str = None, title: str = "Nova Sessão"):
        from dao.mongo.v1.chat_session_dao import ChatSessionDAO
        
        session_dao = ChatSessionDAO(db)
        session_data = {
            "userId": user_id,
            "agentId": agent_id,
            "orgId": org_id or "default",
            "title": title,
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow(),
            "status": "active"
        }
        
        return session_dao.create_session(session_data)