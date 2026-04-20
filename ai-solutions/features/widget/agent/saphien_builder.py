# features/channels/webhook_saphien/agent/saphien_builder.py
"""
Builder para o Saphien Agent.
Responsável por carregar todos os recursos necessários para a execução.
Similar ao Telegram Builder, mas adaptado para Saphien.
"""

import importlib
import os
from typing import Dict, Any, Optional, List

from features.agent.fetch_data import fetch_agent_resources
from dao.postgres.v1.llm_dao import ModelDAO
from core.config.database import get_postgres_db_context, get_mongo_db
from dao.mongo.v1.mcp_server_dao import MCPServerDAO
from dao.mongo.v1.mcp_connection_dao import MCPConnectionDAO


# =====================================================
# LLM LOADER
# =====================================================

async def get_model_with_provider_by_id(model_id: int) -> Optional[Dict]:
    """Busca model + provider do PostgreSQL"""
    try:
        print(f"[SAPHIEN BUILDER] 🔍 Buscando model ID: {model_id}...")
        
        async with get_postgres_db_context() as db:
            model_with_provider = await ModelDAO.get_model_with_provider(db, model_id)
            
            if not model_with_provider:
                print(f"[SAPHIEN BUILDER] ❌ Model {model_id} não encontrado")
                return None
            
            if not hasattr(model_with_provider, 'provider') or not model_with_provider.provider:
                print(f"[SAPHIEN BUILDER] ❌ Provider não carregado")
                return None
            
            provider = model_with_provider.provider
            
            model_data = {
                "id": model_with_provider.id,
                "model_name": model_with_provider.model_name,
                "model_type": getattr(model_with_provider, 'model_type', 'chat'),
                "context_window": getattr(model_with_provider, 'context_window', 16385),
                "max_tokens": getattr(model_with_provider, 'max_tokens', 4096),
                "provider": {
                    "id": provider.id,
                    "name": provider.name,
                    "module_path": provider.module_path or "",
                    "class_name": provider.class_name or "",
                    "config_key": provider.config_key or "",
                    "api_base_url": provider.api_base_url or "",
                }
            }
            
            print(f"[SAPHIEN BUILDER] ✅ Model carregado: {model_data['model_name']} ({provider.name})")
            return model_data
            
    except Exception as e:
        print(f"[SAPHIEN BUILDER] ❌ Erro ao buscar model: {e}")
        return None


def load_llm_from_builder_model(model_config: Dict[str, Any]):
    """Instancia o modelo LLM a partir da configuração"""
    if not model_config:
        raise RuntimeError("model_config não fornecido")

    provider = model_config.get("provider")
    if not provider:
        raise RuntimeError("Provider ausente")

    module_path = provider.get("module_path")
    class_name = provider.get("class_name")
    config_key = provider.get("config_key")
    base_url = provider.get("api_base_url")
    model_name = model_config.get("model_name")

    if not module_path or not class_name:
        raise RuntimeError("module_path ou class_name ausente")

    if not model_name:
        raise RuntimeError("model_name ausente")

    print(f"[SAPHIEN BUILDER] Instanciando LLM: {model_name}")

    try:
        module = importlib.import_module(module_path)
        ProviderClass = getattr(module, class_name)
    except Exception as e:
        raise RuntimeError(f"Erro ao importar {module_path}.{class_name}: {e}")

    kwargs = {"id": model_name}

    if config_key and config_key != "NONE":
        api_key = os.getenv(config_key)
        if not api_key:
            raise RuntimeError(f"API key não encontrada: {config_key}")
        kwargs["api_key"] = api_key

    if base_url:
        kwargs["base_url"] = base_url

    try:
        instance = ProviderClass(**kwargs)
        print(f"[SAPHIEN BUILDER] ✅ LLM instanciado")
        return instance
    except Exception as e:
        raise RuntimeError(f"Falha ao instanciar {class_name}: {e}")


# =====================================================
# NORMALIZAÇÃO DE MCP
# =====================================================

def _normalize_mcp_entry(raw: Any, user_id: str, idx: int) -> Optional[Dict]:
    """
    Normaliza uma entrada de MCP para o formato interno padronizado.

    fetch_agent_resources pode retornar:
      - uma string (ID puro)
      - um dict com chaves 'server' e 'connection' já populadas
      - um dict já no formato interno (com 'server_name', 'connection', etc.)
    """

    # ── Caso 1: já vem como dict populado {server: {...}, connection: {...}} ──
    if isinstance(raw, dict) and "server" in raw and "connection" in raw:
        server = raw["server"]
        connection = raw["connection"]

        server_id = str(
            server.get("id") or
            server.get("_id") or
            connection.get("server_id") or
            f"mcp_{idx}"
        )
        server_name = server.get("name", f"MCP_{idx}")
        connected = connection.get("connected", False)
        url = connection.get("connection", "")
        transport = connection.get("transport", "streamable-http")
        user_token = connection.get("user_token")

        connection_error = None
        if connected and not url:
            connected = False
            connection_error = "Conexão ativa mas sem URL configurada"

        mcp_data = {
            "server_id": server_id,
            "server_name": server_name,
            "server_description": server.get("description", ""),
            "transport": transport,
            "active": server.get("active", True),
            "connected": connected,
            "category": server.get("category", ""),
            "connection": url,
            "img_url": server.get("imgUrl", server.get("img_url", "")),
            "fornecedores": server.get("foornecedores", server.get("fornecedores", [])),
            "show": server.get("show", True),
            "user_token": user_token,
            "connection_error": connection_error,
            # sub-estruturas para compatibilidade com o executor
            "server": {
                "name": server_name,
                "description": server.get("description", ""),
                "img_url": server.get("imgUrl", server.get("img_url", "")),
                "category": server.get("category", ""),
                "active": server.get("active", True),
            },
            "connection_data": {
                "active": server.get("active", True),
                "connected": connected,
                "connection": url,
                "transport": transport,
                "user_token": user_token,
            },
        }

        status = "✅" if connected else "❌"
        suffix = f" — {connection_error}" if connection_error else ""
        print(f"[SAPHIEN BUILDER] {status} MCP '{server_name}' (pre-populado){suffix}")
        return mcp_data

    # ── Caso 2: é uma string com o ID do MCP ──
    mcp_id = None
    if isinstance(raw, str):
        mcp_id = raw
    elif isinstance(raw, dict):
        # dict parcial que só tem o ID
        mcp_id = str(
            raw.get("id") or raw.get("_id") or
            raw.get("server_id") or raw.get("mcp_id") or ""
        )

    if not mcp_id:
        print(f"[SAPHIEN BUILDER] ⚠️ Entrada MCP #{idx} não reconhecida: {type(raw)} — ignorada")
        return None

    return _fetch_mcp_by_id(mcp_id, user_id)


def _fetch_mcp_by_id(mcp_id: str, user_id: str) -> Optional[Dict]:
    """Busca MCP por ID no banco, monta estrutura normalizada."""
    try:
        db = get_mongo_db()
        mcp_server_dao = MCPServerDAO()
        server = mcp_server_dao.getById(mcp_id)

        if not server:
            print(f"[SAPHIEN BUILDER] ❌ MCP Server não encontrado no banco: {mcp_id}")
            return None

        mcp_conn_dao = MCPConnectionDAO(db)
        connection = mcp_conn_dao.get_by_user_and_server(user_id, mcp_id)

        server_name = server.get("name", mcp_id)
        connected = connection.get("connected", False) if connection else False
        url = connection.get("connection", "") if connection else ""
        transport = connection.get("transport", "streamable-http") if connection else "streamable-http"
        user_token = connection.get("user_token") if connection else None

        connection_error = None
        if connected and not url:
            connected = False
            connection_error = "Conexão ativa mas sem URL configurada"

        mcp_data = {
            "server_id": str(server.get("_id", mcp_id)),
            "server_name": server_name,
            "server_description": server.get("description", ""),
            "transport": transport,
            "active": server.get("active", True),
            "connected": connected,
            "category": server.get("category", ""),
            "connection": url,
            "img_url": server.get("img_url", ""),
            "fornecedores": server.get("fornecedores", []),
            "show": server.get("show", True),
            "user_token": user_token,
            "connection_error": connection_error,
            "server": {
                "name": server_name,
                "description": server.get("description", ""),
                "img_url": server.get("img_url", ""),
                "category": server.get("category", ""),
                "active": server.get("active", True),
            },
            "connection_data": {
                "active": server.get("active", True),
                "connected": connected,
                "connection": url,
                "transport": transport,
                "user_token": user_token,
            },
        }

        status = "✅" if connected else "❌"
        suffix = f" — {connection_error}" if connection_error else ""
        print(f"[SAPHIEN BUILDER] {status} MCP '{server_name}'{suffix}")
        return mcp_data

    except Exception as e:
        print(f"[SAPHIEN BUILDER] ❌ Erro ao carregar MCP {mcp_id}: {e}")
        return None


# =====================================================
# TOOLS / KB
# =====================================================

def get_tool_with_config(tool_id: str, user_id: str) -> Optional[Dict]:
    """Busca tool com configuração do usuário"""
    try:
        from dao.mongo.v1.tools_dao import ToolDAO
        from dao.mongo.v1.tool_config_dao import ToolConfigDAO
        
        tool = ToolDAO.get_tool_by_id(tool_id)
        if not tool:
            print(f"[SAPHIEN BUILDER] ❌ Tool não encontrada: {tool_id}")
            return None
        
        tool_config = ToolConfigDAO.get_tool_by_id(user_id, tool_id)
        
        api_key = None
        config_enabled = False
        config_error = None
        
        if tool_config:
            for config_data in tool_config.values():
                if config_data.get('enabled', False):
                    config_enabled = True
                    required = config_data.get('required', {})
                    if 'api_key' in required:
                        api_key = required['api_key']
                    break
        else:
            if tool.get("requires_auth", False):
                config_error = "Tool requer autenticação mas não foi configurada"
                print(f"[SAPHIEN BUILDER] ⚠️ Tool '{tool.get('name', tool_id)}' — {config_error}")
        
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
            "config_error": config_error,
        }
        
        status = "✅" if config_enabled or not tool_data["requires_auth"] else "❌"
        print(f"[SAPHIEN BUILDER] {status} Tool carregada: {tool_data['name']}")
        return tool_data
        
    except Exception as e:
        print(f"[SAPHIEN BUILDER] ❌ Erro ao carregar tool {tool_id}: {e}")
        return None


def get_knowledge_base_data(kb_id: str) -> Optional[Dict]:
    """Busca knowledge base"""
    try:
        from dao.mongo.v1.knowledge_base_dao import KnowledgeBaseDAO
        
        kb = KnowledgeBaseDAO.get_by_id(kb_id)
        if not kb:
            print(f"[SAPHIEN BUILDER] ❌ KB não encontrada: {kb_id}")
            return None
        
        vector_collection = kb.get("vector_collection_name", "")
        has_data = bool(vector_collection)
        
        kb_data = {
            "_id": str(kb.get("_id", kb_id)),
            "id": str(kb.get("_id", kb_id)),
            "name": kb.get("name", ""),
            "description": kb.get("description", ""),
            "language": kb.get("language", "pt"),
            "tags": kb.get("tags", []),
            "origin": kb.get("origin", []),
            "metadata": kb.get("metadata", {}),
            "vector_collection_name": vector_collection,
            "status": kb.get("status", "active"),
            "active": True,
            "has_data": has_data,
            "kb_error": None if has_data else "Knowledge Base sem vetores configurados",
        }
        
        if not has_data:
            print(f"[SAPHIEN BUILDER] ⚠️ KB '{kb_data['name']}' sem vetores configurados")
        else:
            print(f"[SAPHIEN BUILDER] ✅ KB carregada: {kb_data['name']}")
        return kb_data
        
    except Exception as e:
        print(f"[SAPHIEN BUILDER] ❌ Erro ao carregar KB {kb_id}: {e}")
        return None


# =====================================================
# HELPERS — extração segura de nome de recurso
# =====================================================

def _resource_name(item: Any, fallback: str = "?") -> str:
    """Extrai o nome legível de um item de falha ou recurso."""
    if isinstance(item, dict):
        return (
            item.get("name") or
            item.get("server_name") or
            item.get("id") or
            fallback
        )
    return str(item) if item else fallback


# =====================================================
# BUILD PRINCIPAL
# =====================================================

async def build_saphien_agent(
    agent_id: str,
    user_id: str,
    session_id: str,
    db=None,
) -> Dict[str, Any]:
    """
    Carrega recursos para execução do Saphien Agent.
    """
    print(f"\n[SAPHIEN BUILDER] Iniciando build para agente {agent_id}")
    print(f"[SAPHIEN BUILDER] user_id: {user_id} | session_id: {session_id}")

    # 1. Fetch recursos do agente (tools, mcps, kbs)
    fetched = fetch_agent_resources(agent_id, user_id)

    agent_data = fetched.get("agent", {})
    tools_ids = fetched.get("tools", [])
    mcps_raw = fetched.get("mcps", [])          # pode ser lista de IDs ou dicts populados
    knowledge_base_ids = fetched.get("knowledge_bases", [])
    conversation_history = fetched.get("conversation_history", [])
    model_id = fetched.get("model_id", 1)

    if not agent_data:
        raise RuntimeError(f"Agente {agent_id} não encontrado")

    # 2. Buscar modelo do PostgreSQL
    print(f"[SAPHIEN BUILDER] Buscando modelo ID: {model_id}")
    model_data = await get_model_with_provider_by_id(int(model_id))
    if not model_data:
        raise RuntimeError(f"Modelo {model_id} não encontrado no PostgreSQL")

    # 3. Carregar recursos com validação
    print(f"\n[SAPHIEN BUILDER] 📦 Carregando recursos...")

    failed_tools: List[Dict] = []
    failed_mcps: List[Dict] = []
    failed_kbs: List[Dict] = []

    # ── Tools ──
    tools_loaded = []
    for tool_id in tools_ids:
        tool = get_tool_with_config(tool_id, user_id)
        if tool:
            tools_loaded.append(tool)
            if tool.get("config_error"):
                failed_tools.append({
                    "id": tool_id,
                    "name": tool.get("name", tool_id),
                    "error": tool["config_error"],
                })
        else:
            failed_tools.append({
                "id": tool_id,
                "name": str(tool_id),
                "error": "Falha ao carregar tool",
            })

    # ── MCPs — normalização robusta ──
    mcps_loaded = []
    for idx, raw in enumerate(mcps_raw):
        mcp = _normalize_mcp_entry(raw, user_id, idx)
        if mcp:
            mcps_loaded.append(mcp)
            if not mcp.get("connected", False):
                failed_mcps.append({
                    "id": mcp.get("server_id", f"mcp_{idx}"),
                    "name": mcp.get("server_name", f"MCP_{idx}"),
                    "error": mcp.get("connection_error", "MCP desconectado"),
                })
        else:
            # raw era um ID string ou dict parcial sem dados úteis
            raw_id = raw if isinstance(raw, str) else str(raw.get("id", f"mcp_{idx}"))
            failed_mcps.append({
                "id": raw_id,
                "name": raw_id,
                "error": "Falha ao carregar MCP",
            })

    # ── KBs ──
    kbs_loaded = []
    for kb_id in knowledge_base_ids:
        kb = get_knowledge_base_data(kb_id)
        if kb:
            kbs_loaded.append(kb)
            if not kb.get("has_data", True):
                failed_kbs.append({
                    "id": kb_id,
                    "name": kb.get("name", kb_id),
                    "error": kb.get("kb_error", "KB sem dados"),
                })
        else:
            failed_kbs.append({
                "id": kb_id,
                "name": str(kb_id),
                "error": "Falha ao carregar KB",
            })

    # 4. Builder model
    builder_model = {
        "model_name": model_data["model_name"],
        "provider": model_data["provider"],
        "model_type": model_data.get("model_type", "chat"),
        "context_window": model_data.get("context_window", 16385),
        "max_tokens": model_data.get("max_tokens", 4096),
    }

    # 5. Mensagens de aviso — usando _resource_name para garantir strings
    warning_messages = []

    if failed_tools:
        names = [_resource_name(t) for t in failed_tools]
        warning_messages.append(f"⚠️ Ferramentas com falha: {', '.join(names)}")
        for t in failed_tools:
            warning_messages.append(
                f"   • {_resource_name(t)}: {t.get('error', 'Erro desconhecido') if isinstance(t, dict) else '?'}"
            )

    if failed_mcps:
        names = [_resource_name(m) for m in failed_mcps]
        warning_messages.append(f"⚠️ MCPs com falha: {', '.join(names)}")
        for m in failed_mcps:
            warning_messages.append(
                f"   • {_resource_name(m)}: {m.get('error', 'Erro desconhecido') if isinstance(m, dict) else '?'}"
            )

    if failed_kbs:
        names = [_resource_name(k) for k in failed_kbs]
        warning_messages.append(f"⚠️ Bases de conhecimento com falha: {', '.join(names)}")
        for k in failed_kbs:
            warning_messages.append(
                f"   • {_resource_name(k)}: {k.get('error', 'Erro desconhecido') if isinstance(k, dict) else '?'}"
            )

    resources_warning = "\n".join(warning_messages) if warning_messages else None

    # 6. Resumo
    print(f"\n[SAPHIEN BUILDER] ✅ Build concluído:")
    print(f"  • Agente: {agent_data.get('name')}")
    print(f"  • Modelo: {model_data['model_name']} ({model_data['provider']['name']})")
    print(f"  • Tools: {len(tools_loaded)}/{len(tools_ids)} carregadas")
    print(f"  • MCPs: {len(mcps_loaded)}/{len(mcps_raw)} carregados")
    print(f"  • KBs: {len(kbs_loaded)}/{len(knowledge_base_ids)} carregadas")
    print(f"  • Histórico: {len(conversation_history)} mensagens")

    if resources_warning:
        print(f"\n[SAPHIEN BUILDER] ⚠️ AVISOS DE RECURSOS:")
        print(resources_warning)

    return {
        "agent": agent_data,
        "resources": {
            "builder_model": builder_model,
            "tools": tools_loaded,
            "mcps": mcps_loaded,
            "knowledgeBase": kbs_loaded,
            "resources_warning": resources_warning,
            "failed_tools": failed_tools,
            "failed_mcps": failed_mcps,
            "failed_kbs": failed_kbs,
        },
        "context": {
            "session_id": session_id,
            "conversation_history": conversation_history,
        },
        "model_id": str(model_id),
    }