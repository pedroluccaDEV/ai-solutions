# features/chat/agent_builder.py
import asyncio
from typing import Dict, List, Any, Optional
import sys
from pathlib import Path
import uuid
from datetime import datetime

sys.path.append(str(Path(__file__).resolve().parents[2]))

from core.config.database import get_mongo_db, get_postgres_db
from dao.mongo.v1.agent_dao import AgentDAO
from dao.mongo.v1.tools_dao import ToolDAO
from dao.mongo.v1.tool_config_dao import ToolConfigDAO
from dao.mongo.v1.mcp_server_dao import MCPServerDAO
from dao.mongo.v1.mcp_connection_dao import MCPConnectionDAO
from dao.mongo.v1.knowledge_base_dao import KnowledgeBaseDAO
from dao.mongo.v1.memory_chat_dao import MemoryDAO
from bson import ObjectId

# =============================================================
# CONSTANTES
# =============================================================

DEFAULT_AGENT_NAME = "SaphienAI"
DEFAULT_AGENT_CATEGORY = "default"
DEFAULT_MODEL = "1"

# =============================================================
# RESOLUÇÃO DE MODELO VIA POSTGRES
# =============================================================

async def resolve_model_config(model_ref: str, pg_conn) -> Dict:
    """
    Resolve o modelo final a partir do model_ref
    Retorna tudo que o runtime precisa para instanciar o modelo
    """
    print(f"\n[BUILDER] 🔍 RESOLVENDO MODELO: {model_ref}")
    
    try:
        cursor = pg_conn.cursor()

        # Caso seja ID numérico
        if str(model_ref).isdigit():
            print(f"[BUILDER] 📍 Buscando modelo por ID: {model_ref}")
            cursor.execute("""
                SELECT
                    m.model_name,
                    m.capabilities,
                    m.context_window,
                    m.max_tokens,
                    p.id as provider_id,
                    p.name as provider_name,
                    p.module_path,
                    p.class_name,
                    p.config_key,
                    p.api_base_url
                FROM models m
                JOIN providers p ON p.id = m.provider_id
                WHERE m.id = %s AND m.is_active = true
            """, (int(model_ref),))
        else:
            # Caso string
            if ":" in model_ref:
                _, model_name = model_ref.split(":", 1)
                print(f"[BUILDER] 📍 Buscando modelo por nome (com prefixo): {model_name}")
            else:
                model_name = model_ref
                print(f"[BUILDER] 📍 Buscando modelo por nome: {model_name}")

            cursor.execute("""
                SELECT
                    m.model_name,
                    m.capabilities,
                    m.context_window,
                    m.max_tokens,
                    p.id as provider_id,
                    p.name as provider_name,
                    p.module_path,
                    p.class_name,
                    p.config_key,
                    p.api_base_url
                FROM models m
                JOIN providers p ON p.id = m.provider_id
                WHERE m.model_name = %s AND m.is_active = true
            """, (model_name,))

        row = cursor.fetchone()

        if not row:
            raise ValueError(f"Modelo não encontrado ou inativo: {model_ref}")

        # Parse capabilities de JSON para lista
        capabilities = row["capabilities"] or []
        if isinstance(capabilities, str):
            try:
                import json
                capabilities = json.loads(capabilities)
            except:
                capabilities = []

        model_config = {
            "provider": row["provider_name"],
            "provider_id": row["provider_id"],
            "module_path": row["module_path"],
            "class_name": row["class_name"],
            "config_key": row["config_key"],
            "model_id": row["model_name"],
            "capabilities": capabilities,
            "context_window": row["context_window"],
            "max_tokens": row["max_tokens"],
            "api_base_url": row["api_base_url"]
        }

        print(f"[BUILDER] ✅ Modelo resolvido:")
        print(f"  • Provider: {model_config['provider']}")
        print(f"  • Classe: {model_config['class_name']}")
        print(f"  • Model ID: {model_config['model_id']}")
        print(f"  • Capabilities: {model_config['capabilities']}")
        
        return model_config
        
    except Exception as e:
        print(f"[BUILDER] ❌ Erro ao resolver modelo {model_ref}: {e}")
        raise

# =============================================================
# FUNÇÕES AUXILIARES PARA MEMÓRIA
# =============================================================

async def load_session_memory(session_id: str, user_message: str = None) -> Dict[str, Any]:
    """
    Carrega a memória da sessão
    """
    memory_data = {
        "memory_loaded": False,
        "conversation_history": [],
        "total_messages": 0,
        "memory_object": None
    }
    
    if not session_id:
        return memory_data
    
    try:
        print(f"[MEMORY] 🔍 Buscando memória para sessão: {session_id}")
        
        db = get_mongo_db()
        memory_dao = MemoryDAO(db)
        
        memory = memory_dao.get_memory_by_session_id(session_id)
        
        if memory:
            print(f"[MEMORY] ✅ Memória encontrada: {memory.get('_id')}")
            memory_data["memory_object"] = memory
            memory_data["memory_loaded"] = True
            
            conversation_history = memory_dao.get_conversation_history(session_id)
            memory_data["conversation_history"] = conversation_history
            memory_data["total_messages"] = len(conversation_history)
        else:
            print(f"[MEMORY] ⚠️  Nenhuma memória encontrada para sessão: {session_id}")
        
        return memory_data
        
    except Exception as e:
        print(f"[MEMORY] ❌ Erro ao carregar memória: {e}")
        return memory_data

async def add_assistant_response_to_memory(session_id: str, response: str):
    """
    Adiciona a resposta do assistente à memória
    """
    if not session_id or not response:
        return
    
    try:
        print(f"[MEMORY] ✍️  Adicionando resposta do assistente à memória")
        
        db = get_mongo_db()
        memory_dao = MemoryDAO(db)
        
        memory_dao.add_message_to_memory(
            session_id=session_id,
            sender="assistant",
            content=response
        )
        
        print(f"[MEMORY] ✅ Resposta do assistente adicionada à memória")
        
    except Exception as e:
        print(f"[MEMORY] ❌ Erro ao adicionar resposta: {e}")

# =============================================================
# FUNÇÕES DE SELEÇÃO DE AGENTE
# =============================================================

def should_use_default_agent(agent_id: Any) -> bool:
    """
    Determina se deve usar o agente padrão SaphienAI
    """
    if agent_id is None:
        return True
    
    if isinstance(agent_id, str):
        agent_id_str = agent_id.strip()
        
        # String vazia ou apenas espaços
        if not agent_id_str:
            return True
        
        # String com valores inválidos
        if agent_id_str.lower() in ["null", "undefined", "none", "default"]:
            return True
        
        # IDs zerados ou muito curtos
        if (agent_id_str == "0" or 
            agent_id_str == "000000000000000000000000" or
            len(agent_id_str) < 3):
            return True
        
        # Verifica se parece ser um ObjectId válido
        if ObjectId.is_valid(agent_id_str):
            return False
        else:
            if len(agent_id_str) < 10:
                return True
    
    if agent_id is False or agent_id == 0:
        return True
    
    return False

def get_default_agent_document() -> Dict:
    """
    Retorna o agente SaphienAI padrão
    """
    print(f"\n[BUILDER] 🎯 BUSCANDO AGENTE PADRÃO SAPHIENAI")
    
    try:
        db = get_mongo_db()
        
        # Busca EXATAMENTE por nome e categoria
        default_agent = db.agents.find_one({
            "name": DEFAULT_AGENT_NAME,
            "category": DEFAULT_AGENT_CATEGORY,
            "status": "active"
        })
        
        if default_agent:
            print(f"[BUILDER] ✅ SaphienAI encontrado no banco")
            if "_id" in default_agent and isinstance(default_agent["_id"], ObjectId):
                default_agent["_id"] = str(default_agent["_id"])
            return default_agent
        
        # Se não encontrou, busca o primeiro agente ativo
        print(f"[BUILDER] ⚠️  SaphienAI não encontrado, buscando primeiro agente ativo")
        
        fallback_agent = db.agents.find_one({"status": "active"})
        if fallback_agent:
            print(f"[BUILDER] ✅ Usando agente fallback: {fallback_agent.get('name', 'Sem nome')}")
            if "_id" in fallback_agent and isinstance(fallback_agent["_id"], ObjectId):
                fallback_agent["_id"] = str(fallback_agent["_id"])
            return fallback_agent
        
        raise ValueError("Nenhum agente ativo encontrado no banco")
        
    except Exception as e:
        print(f"[BUILDER] ❌ Erro ao buscar agente padrão: {e}")
        raise

def get_agent_document(agent_id: str) -> Optional[Dict]:
    """
    Busca o documento do agente
    """
    print(f"\n[BUILDER] 🔍 GET_AGENT_DOCUMENT")
    print(f"[BUILDER] agent_id recebido: '{agent_id}'")
    
    # Verifica se deve usar o agente padrão
    if should_use_default_agent(agent_id):
        print(f"[BUILDER] 🎯 Usando agente padrão")
        return get_default_agent_document()
    
    agent_id_str = str(agent_id).strip()
    print(f"[BUILDER] 🔎 Buscando agente específico: {agent_id_str}")
    
    try:
        # Tenta como ObjectId
        if ObjectId.is_valid(agent_id_str):
            print(f"[BUILDER] 📍 Tentando buscar como ObjectId")
            agent = AgentDAO.get_agent_by_id(agent_id_str)
            
            if not agent:
                db = get_mongo_db()
                agent = db.agents.find_one({"_id": ObjectId(agent_id_str)})
            
            if agent:
                print(f"[BUILDER] ✅ Agente encontrado via ObjectId: {agent.get('name', 'Sem nome')}")
                if "_id" in agent and isinstance(agent["_id"], ObjectId):
                    agent["_id"] = str(agent["_id"])
                return agent
        
        # Tenta como string ID
        print(f"[BUILDER] 📍 Tentando buscar como string ID")
        db = get_mongo_db()
        agent = db.agents.find_one({"_id": agent_id_str})
        
        if agent:
            print(f"[BUILDER] ✅ Agente encontrado via string ID: {agent.get('name', 'Sem nome')}")
            return agent
        
        # Retorna padrão se não encontrou
        print(f"[BUILDER] ⚠️  Agente {agent_id_str} não encontrado, usando padrão")
        return get_default_agent_document()
        
    except Exception as e:
        print(f"[BUILDER] ❌ Erro ao buscar agente: {e}")
        return get_default_agent_document()

# =============================================================
# FUNÇÕES DE PROCESSAMENTO
# =============================================================

def filter_agent_fields(agent: Dict) -> Dict:
    """Filtra apenas os campos necessários do agente"""
    return {
        "category": agent.get("category", DEFAULT_AGENT_CATEGORY),
        "name": agent.get("name", DEFAULT_AGENT_NAME),
        "description": agent.get("description", ""),
        "roleDefinition": agent.get("roleDefinition", ""),
        "goal": agent.get("goal", ""),
        "agentRules": agent.get("agentRules", ""),
        "whenToUse": agent.get("whenToUse", ""),
        "model": agent.get("model", DEFAULT_MODEL),
        "knowledgeBase": agent.get("knowledgeBase", []),
        "tools": agent.get("tools", []),
        "mcps": agent.get("mcps", [])
    }

def apply_agent_overrides(agent_data: Dict, overrides: Dict) -> Dict:
    """
    Aplica os overrides ao agente
    """
    print(f"\n[BUILDER] 🔄 Aplicando overrides...")
    
    result = agent_data.copy()
    
    if not overrides:
        return result
    
    # Aplica cada override individualmente
    if "tools" in overrides and overrides["tools"]:
        result["tools"] = overrides["tools"]
        print(f"[BUILDER] ✅ Tools substituídas: {len(result['tools'])} tools")
    
    if "mcps" in overrides and overrides["mcps"]:
        agent_mcps = set(agent_data.get("mcps", []))
        override_mcps = set(overrides["mcps"])
        merged_mcps = list(agent_mcps.union(override_mcps))
        result["mcps"] = merged_mcps
        print(f"[BUILDER] ✅ MCPs mesclados: {len(merged_mcps)} mcps")
    
    if "knowledgeBase" in overrides and overrides["knowledgeBase"]:
        result["knowledgeBase"] = overrides["knowledgeBase"]
        print(f"[BUILDER] ✅ KBs substituídas: {len(result['knowledgeBase'])} kbs")
    
    if "model" in overrides and overrides["model"]:
        result["model"] = str(overrides["model"])
        print(f"[BUILDER] ✅ Model substituído: {result['model']}")
    
    return result

def get_tool_with_config(tool_id: str, user_id: str) -> Optional[Dict]:
    """Busca tool com configuração do usuário"""
    try:
        tool = ToolDAO.get_tool_by_id(tool_id)
        if not tool:
            return None
        
        tool_config = ToolConfigDAO.get_tool_by_id(user_id, tool_id)
        
        # Extrair API key se existir
        api_key = None
        config_enabled = False
        
        if tool_config:
            for config_data in tool_config.values():
                if config_data.get('enabled', False):
                    config_enabled = True
                    required = config_data.get('required', {})
                    if 'api_key' in required:
                        api_key = required['api_key']
                    break
        
        tool_data = {
            "id": str(tool.get("_id", tool_id)),
            "tool_id": str(tool.get("_id", tool_id)),
            "name": tool.get("name", ""),
            "description": tool.get("description", ""),
            "class_name": tool.get("tool_class", ""),
            "module_path": tool.get("module_path", ""),
            "tool_class": tool.get("tool_class", ""),
            "schema": tool.get("schema", {}),
            "active": tool.get("active", True),
            "category": tool.get("category", ""),
            "tool_param": tool.get("tool_param", ""),
            "requires_auth": bool(tool.get("tool_param")),
            "user_config": tool_config or {},
            "config_enabled": config_enabled,
            "api_key": api_key,
        }
        
        return tool_data
        
    except Exception:
        return None

def get_mcp_with_connection(mcp_id: str, user_id: str) -> Optional[Dict]:
    """Busca MCP com conexão do usuário"""
    try:
        db = get_mongo_db()
        mcp_server_dao = MCPServerDAO()
        server = mcp_server_dao.getById(mcp_id)
        
        if not server:
            return None
        
        mcp_conn_dao = MCPConnectionDAO(db)
        connection = mcp_conn_dao.get_by_user_and_server(user_id, mcp_id)
        
        mcp_data = {
            "server_id": str(server.get("_id", mcp_id)),
            "server_name": server.get("name", ""),
            "server_description": server.get("description", ""),
            "transport": "streamable-http",
            "active": server.get("active", True),
            "connected": connection.get("connected", False) if connection else False,
            "category": server.get("category", ""),
            "connection": connection.get("connection", "") if connection else "",
            "img_url": server.get("img_url", ""),
            "fornecedores": server.get("fornecedores", []),
            "show": server.get("show", True),
            "user_token": connection.get("user_token") if connection else None
        }
        
        mcp_data["server"] = {
            "name": mcp_data["server_name"],
            "description": mcp_data["server_description"],
            "img_url": mcp_data["img_url"],
            "category": mcp_data["category"],
            "active": mcp_data["active"],
            "fornecedores": mcp_data["fornecedores"],
            "show": mcp_data["show"]
        }
        
        mcp_data["connection_data"] = {
            "active": mcp_data["active"],
            "connected": mcp_data["connected"],
            "connection": mcp_data["connection"],
            "transport": mcp_data["transport"],
            "user_token": mcp_data["user_token"]
        }
        
        return mcp_data
        
    except Exception:
        return None

def get_knowledge_base_data(kb_id: str) -> Optional[Dict]:
    """Busca knowledge base"""
    try:
        kb = KnowledgeBaseDAO.get_by_id(kb_id)
        if not kb:
            return None
        
        kb_data = {
            "_id": str(kb.get("_id", kb_id)),
            "id": str(kb.get("_id", kb_id)),
            "name": kb.get("name", ""),
            "description": kb.get("description", ""),
            "language": kb.get("language", "pt"),
            "tags": kb.get("tags", []),
            "origin": kb.get("origin", []),
            "metadata": kb.get("metadata", {}),
            "vector_collection_name": kb.get("vector_collection_name", ""),
            "status": kb.get("status", "active"),
            "active": True
        }
        
        return kb_data
        
    except Exception:
        return None

# =============================================================
# FUNÇÃO PRINCIPAL
# =============================================================

async def build_agent_for_chat(
    agent_id: str, 
    user_id: str, 
    agent_overrides: Dict = None,
    message: str = "",
    session_id: str = None,
    org_id: str = None,
    project_id: str = None,
    app_id: str = None
) -> Dict[str, Any]:
    """
    Constrói o agente completo com resolução de modelo no Postgres
    """
    print(f"\n{'='*60}")
    print(f"🏗️  AGENT BUILDER INICIADO")
    print(f"{'='*60}")
    print(f"[BUILDER] 📥 INPUTS:")
    print(f"  • agent_id: '{agent_id}'")
    print(f"  • user_id: '{user_id}'")
    print(f"  • session_id: '{session_id}'")
    print(f"  • has_overrides: {'Sim' if agent_overrides else 'Não'}")
    
    try:
        # 1. Carregar memória se tiver session_id
        memory_data = {
            "memory_loaded": False,
            "conversation_history": [],
            "total_messages": 0,
        }
        
        if session_id and session_id.strip():
            print(f"\n[BUILDER] 🧠 Carregando memória da sessão...")
            memory_data = await load_session_memory(session_id, message)
        
        # 2. Buscar agente
        print(f"\n[BUILDER] 🔍 BUSCANDO AGENTE...")
        agent_doc = get_agent_document(agent_id)
        
        agent_name = agent_doc.get('name', 'Sem nome')
        agent_category = agent_doc.get('category', 'Sem categoria')
        
        is_saphienai = (agent_name == DEFAULT_AGENT_NAME and 
                       agent_category == DEFAULT_AGENT_CATEGORY)
        
        print(f"[BUILDER] ✅ Agente encontrado: {agent_name}")
        print(f"[BUILDER] 🎯 É SaphienAI padrão: {is_saphienai}")
        
        # 3. Filtrar campos
        agent_filtered = filter_agent_fields(agent_doc)
        
        # 4. Aplicar overrides se existirem
        final_agent = agent_filtered.copy()
        if agent_overrides:
            print(f"\n[BUILDER] 🔄 APLICANDO OVERRIDES")
            final_agent = apply_agent_overrides(agent_filtered, agent_overrides)
        
        print(f"\n[BUILDER] 📊 AGENTE FINAL:")
        print(f"  • Nome: {final_agent['name']}")
        print(f"  • Modelo: {final_agent['model']}")
        
        # 5. Resolver modelo no Postgres
        print(f"\n[BUILDER] 🎯 RESOLVENDO MODELO FINAL...")
        
        pg_conn = get_postgres_db()
        model_config = await resolve_model_config(
            model_ref=final_agent["model"],
            pg_conn=pg_conn
        )
        
        print(f"[BUILDER] ✅ Modelo config resolvido no Postgres")
        
        # 6. Carregar recursos
        print(f"\n[BUILDER] 📦 CARREGANDO RECURSOS...")
        
        tools_loaded = []
        for tool_id in final_agent.get("tools", []):
            tool = get_tool_with_config(tool_id, user_id)
            if tool:
                tools_loaded.append(tool)
        
        mcps_loaded = []
        for mcp_id in final_agent.get("mcps", []):
            mcp = get_mcp_with_connection(mcp_id, user_id)
            if mcp:
                mcps_loaded.append(mcp)
        
        kbs_loaded = []
        for kb_id in final_agent.get("knowledgeBase", []):
            kb = get_knowledge_base_data(kb_id)
            if kb:
                kbs_loaded.append(kb)
        
        # 7. Construir resultado final
        agent_oid = agent_doc.get("_id", "default-agent")
        
        result = {
            "agent": {
                "category": final_agent["category"],
                "name": final_agent["name"],
                "description": final_agent["description"],
                "roleDefinition": final_agent["roleDefinition"],
                "goal": final_agent["goal"],
                "agentRules": final_agent["agentRules"],
                "whenToUse": final_agent["whenToUse"],
                "model": final_agent["model"],
                "knowledgeBase": final_agent["knowledgeBase"],
                "tools": final_agent["tools"],
                "mcps": final_agent["mcps"],
                "_id": {"$oid": str(agent_oid)} if agent_oid != "default-agent" else {"$oid": "000000000000000000000000"}
            },
            "model_config": model_config,
            "resources": {
                "tools": tools_loaded,
                "mcps": mcps_loaded,
                "knowledgeBase": kbs_loaded
            },
            "message": message,
            "context": {
                "user_id": user_id,
                "session_id": session_id,
                "org_id": org_id,
                "project_id": project_id,
                "app_id": app_id,
                "conversation_history": memory_data.get("conversation_history", []),
                "has_memory": memory_data.get("memory_loaded", False),
                "total_history_messages": len(memory_data.get("conversation_history", [])),
                "timestamp": datetime.utcnow().isoformat()
            },
            "metadata": {
                "user_id": user_id,
                "agent_id": str(agent_oid),
                "agent_name": final_agent["name"],
                "agent_category": final_agent["category"],
                "is_default_agent": is_saphienai,
                "builder_version": "5.0",
                "has_memory": memory_data.get("memory_loaded", False),
                "session_id": session_id,
                "tools_count": len(tools_loaded),
                "mcps_count": len(mcps_loaded),
                "kbs_count": len(kbs_loaded),
                "model_resolved": True,
                "model_provider": model_config["provider"],
                "model_capabilities": model_config["capabilities"]
            }
        }
        
        # 8. Log final
        print(f"\n{'='*60}")
        print(f"✅ AGENT BUILDER FINALIZADO")
        print(f"{'='*60}")
        print(f"📊 RESUMO:")
        print(f"  • Agente: {final_agent['name']}")
        print(f"  • Modelo: {final_agent['model']} → {model_config['provider']}/{model_config['model_id']}")
        print(f"  • Classe: {model_config['class_name']}")
        print(f"  • Capabilities: {model_config['capabilities']}")
        print(f"  • É padrão: {is_saphienai}")
        print(f"  • Tools: {len(tools_loaded)}")
        print(f"  • MCPs: {len(mcps_loaded)}")
        print(f"  • KBs: {len(kbs_loaded)}")
        print(f"  • Memória: {memory_data.get('memory_loaded', False)}")
        print(f"{'='*60}")
        
        return result
        
    except Exception as e:
        print(f"[BUILDER] ❌ ERRO CRÍTICO: {e}")
        raise

# =============================================================
# FUNÇÕES AUXILIARES
# =============================================================

async def build_agent_from_request(request_data: Dict) -> Dict[str, Any]:
    """
    Versão simplificada para receber o request diretamente.
    """
    print(f"\n[BUILDER] 📨 PROCESSANDO REQUEST...")
    
    agent_id = request_data.get("agent_id", "")
    user_id = request_data.get("user_id", "")
    agent_overrides = request_data.get("agent_overrides", {})
    message = request_data.get("message", "")
    session_id = request_data.get("session_id")
    org_id = request_data.get("org_id")
    project_id = request_data.get("project_id")
    app_id = request_data.get("app_id")
    
    return await build_agent_for_chat(
        agent_id=agent_id,
        user_id=user_id,
        agent_overrides=agent_overrides,
        message=message,
        session_id=session_id,
        org_id=org_id,
        project_id=project_id,
        app_id=app_id
    )

async def add_assistant_response(request_data: Dict, response_content: str):
    """
    Adiciona a resposta do assistente à memória
    """
    session_id = request_data.get("session_id")
    
    if session_id and response_content:
        print(f"\n[BUILDER] 🧠 Adicionando resposta à memória")
        await add_assistant_response_to_memory(session_id, response_content)
        print(f"[BUILDER] ✅ Resposta adicionada à memória")