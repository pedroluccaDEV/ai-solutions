# features/chat/agent_builder.py

import asyncio
from typing import Dict, List, Any, Optional
import sys
from pathlib import Path
import uuid
from datetime import datetime

sys.path.append(str(Path(__file__).resolve().parents[2]))

from core.config.database import get_mongo_db, get_postgres_db_context
from dao.mongo.v1.agent_dao import AgentDAO
from dao.mongo.v1.tools_dao import ToolDAO
from dao.mongo.v1.tool_config_dao import ToolConfigDAO
from dao.mongo.v1.mcp_server_dao import MCPServerDAO
from dao.mongo.v1.mcp_connection_dao import MCPConnectionDAO
from dao.mongo.v1.knowledge_base_dao import KnowledgeBaseDAO
from dao.mongo.v1.memory_chat_dao import MemoryDAO
from dao.postgres.v1.llm_dao import ModelDAO, ProviderDAO
from bson import ObjectId

# =============================================================
# CONSTANTES
# =============================================================

DEFAULT_AGENT_NAME = "SaphienAI"
DEFAULT_AGENT_CATEGORY = "default"
DEFAULT_MODEL = "1"

# IDs inválidos expandidos
INVALID_AGENT_IDS = [
    "", " ", "null", "undefined", "none", "0", "false", "true",
    "00000000000", "000000000000000000000000", None
]

# Agente SaphienAI padrão COMPLETO
SAPHIENAI_AGENT_DATA = {
    "category": DEFAULT_AGENT_CATEGORY,
    "isClone": False,
    "name": DEFAULT_AGENT_NAME,
    "description": "Agente padrão SaphienAI para tarefas gerais, adaptável e multifuncional.",
    "roleDefinition": """O SaphienAI é um assistente de inteligência artificial projetado para ser extremamente versátil e adaptável, capaz de lidar com uma ampla gama de tarefas e contextos. Ele atua como um recurso centralizado para resolver problemas, fornecer informações, auxiliar na tomada de decisões e executar funções diversas, sempre buscando a eficiência e a precisão. Sua natureza flexível permite que ele se ajuste a diferentes necessidades, desde questões simples até desafios complexos, sem se limitar a um domínio específico.

Com uma abordagem holística, o SaphienAI integra conhecimentos de múltiplas áreas, como tecnologia, ciência, negócios, educação e criatividade, para oferecer soluções abrangentes. Ele é programado para entender contextos variados e adaptar suas respostas conforme a situação, mantendo um equilíbrio entre profundidade técnica e acessibilidade. Seu papel é ser um parceiro confiável que pode assumir diferentes funções conforme demandado, sempre com foco na utilidade e na satisfação do usuário.""",
    "goal": """O objetivo principal do SaphienAI é maximizar a utilidade e a eficácia em qualquer tarefa atribuída, fornecendo assistência de alta qualidade independentemente do assunto ou complexidade. Ele busca ser um recurso onipresente que pode substituir ou complementar agentes especializados, oferecendo uma solução única para necessidades diversas, desde consultas informativas até execução de processos complexos. Isso envolve aprender e se adaptar rapidamente a novos contextos, garantindo que suas respostas sejam relevantes, precisas e alinhadas com as expectativas do usuário.

Além disso, o SaphienAI visa promover a eficiência e a produtividade, reduzindo a necessidade de múltiplas ferramentas ou especialistas. Ele se esforça para antecipar necessidades, oferecer sugestões proativas e resolver problemas de forma integrada, sempre mantendo um alto padrão de desempenho. Seu meta-objetivo é tornar-se uma solução abrangente que simplifica interações e otimiza resultados em qualquer cenário, contribuindo para uma experiência de usuário fluida e satisfatória.""",
    "agentRules": """O SaphienAI deve sempre priorizar a precisão e a relevância em suas respostas, verificando informações quando necessário e evitando suposições não fundamentadas. Ele deve se adaptar ao tom e ao nível de detalhe solicitado pelo usuário, sendo conciso em consultas simples e detalhado em questões complexas, sem sobrecarregar com excesso de informação. A clareza e a objetividade são essenciais, garantindo que as comunicações sejam facilmente compreensíveis e diretas.

Em situações ambíguas ou com informações insuficientes, o agente deve solicitar esclarecimentos para evitar erros, mantendo uma postura colaborativa e paciente. Ele deve evitar viéses e manter neutralidade, especialmente em tópicos sensíveis, baseando-se em fatos e lógica. A confidencialidade e a ética devem ser respeitadas, não compartilhando dados privados ou engajando em atividades prejudiciais.

O agente deve ser proativo na identificação de necessidades implícitas, oferecendo sugestões ou recursos adicionais que possam enriquecer a interação. Ele deve equilibrar criatividade com praticidade, inovando quando apropriado, mas sempre ancorado em soluções viáveis. A consistência no desempenho é crucial, assegurando que a qualidade do serviço permaneça alta independentemente da frequência ou variedade das tarefas.

Finalmente, o SaphienAI deve aprender com interações passadas para melhorar continuamente, ajustando-se a preferências do usuário e atualizando conhecimentos conforme novas informações surgem. Ele deve manter um foco na resolução de problemas, evitando distrações e mantendo o engajamento até que a tarefa seja concluída satisfatoriamente.""",
    "whenToUse": "Use este agente quando precisar de assistência geral para uma variedade de tarefas, como responder perguntas, resolver problemas, gerar conteúdo, analisar dados ou fornecer suporte em múltiplos domínios, sem a necessidade de um especialista específico. Ele é ideal para situações onde a versatilidade e a adaptabilidade são mais importantes do que a expertise profunda em uma área única, servindo como uma solução abrangente para necessidades cotidianas ou projetos multifacetados.",
    "model": DEFAULT_MODEL,
    "knowledgeBase": [],
    "tools": [],
    "mcps": [],
    "visibility": "public",
    "status": "active",
    "color": "#355C7D",
    "org": "default",
    "type": "playground"
}

# =============================================================
# FUNÇÕES PARA MODEL + PROVIDER (POSTGRES) - USANDO LLM_DAO
# =============================================================

async def get_model_with_provider_by_id(model_id: int) -> Optional[Dict]:
    """
    Busca model + provider usando ModelDAO com campos corrigidos
    """
    try:
        print(f"[BUILDER] 🔍 Buscando model ID: {model_id} via LLM DAO (campos corrigidos)...")
        
        async with get_postgres_db_context() as db:
            # Usa o método específico que carrega o provider junto
            model_with_provider = await ModelDAO.get_model_with_provider(db, model_id)
            
            if not model_with_provider:
                print(f"[BUILDER] ❌ Model {model_id} não encontrado ou sem provider")
                return None
            
            print(f"[BUILDER] ✅ Model encontrado: {model_with_provider.model_name}")
            
            # Verifica se o provider foi carregado
            if not hasattr(model_with_provider, 'provider') or not model_with_provider.provider:
                print(f"[BUILDER] ❌ Provider não carregado para model {model_id}")
                return None
            
            provider = model_with_provider.provider
            print(f"[BUILDER] ✅ Provider encontrado: {provider.name}")
            
            # Monta o resultado com os campos CORRETOS da sua tabela
            model_data = {
                "id": model_with_provider.id,
                "model_name": model_with_provider.model_name,
                "model_type": getattr(model_with_provider, 'model_type', 'chat'),
                "context_window": getattr(model_with_provider, 'context_window', 16385),
                "max_tokens": getattr(model_with_provider, 'max_tokens', 4096),
                "capabilities": getattr(model_with_provider, 'capabilities', []) or [],
                "description": getattr(model_with_provider, 'description', ''),
                "created_at": model_with_provider.created_at.isoformat() if model_with_provider.created_at else None,
                "updated_at": model_with_provider.updated_at.isoformat() if model_with_provider.updated_at else None,
                "provider": {
                    "id": provider.id,
                    "name": provider.name,
                    "module_path": provider.module_path or "",  # CAMPO CORRETO
                    "class_name": provider.class_name or "",    # CAMPO CORRETO
                    "config_key": provider.config_key or "",
                    "api_base_url": provider.api_base_url or "",
                    "is_active": getattr(provider, 'is_active', True),
                    "created_at": provider.created_at.isoformat() if provider.created_at else None,
                }
            }
            
            print(f"[BUILDER] ✅ Model + Provider carregados com sucesso!")
            print(f"  ├─ Model: {model_data['model_name']}")
            print(f"  ├─ Provider: {model_data['provider']['name']}")
            print(f"  ├─ Module: {model_data['provider']['module_path']}")
            print(f"  ├─ Class: {model_data['provider']['class_name']}")
            print(f"  └─ Config Key: {model_data['provider']['config_key']}")
            
            return model_data
            
    except Exception as e:
        print(f"[BUILDER] ❌ ERRO ao buscar model {model_id}: {str(e)[:200]}")
        import traceback
        traceback.print_exc()
        return None
    

async def get_model_fallback() -> Dict:
    """Retorna um modelo fallback padrão caso PostgreSQL falhe"""
    print(f"[BUILDER] ⚠️  Usando modelo fallback padrão")
    return {
        "id": 1,
        "model_name": "gpt-3.5-turbo",
        "model_type": "chat",
        "context_window": 16385,
        "max_tokens": 4096,
        "capabilities": ["text"],
        "description": "Modelo fallback - GPT-3.5 Turbo",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "provider": {
            "id": 1,
            "name": "OpenAI",
            "module_path": "agno.models.openai",
            "class_name": "OpenAI",
            "config_key": "OPENAI_API_KEY",
            "api_base_url": "https://api.openai.com/v1",
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        }
    }


async def list_all_models_from_postgres() -> List[Dict]:
    """Lista todos os models do PostgreSQL para debugging"""
    try:
        print(f"[BUILDER] 📋 Listando todos os models do PostgreSQL...")
        
        async with get_postgres_db_context() as db:
            models = await ModelDAO.list_models(db)
            
            result = []
            for model in models:
                provider = await ProviderDAO.get_provider_by_id(db, model.provider_id)
                
                model_data = {
                    "id": model.id,
                    "model_name": model.model_name,
                    "model_type": model.model_type,
                    "provider_id": model.provider_id,
                    "provider_name": provider.name if provider else "Desconhecido",
                    "capabilities": model.capabilities or []
                }
                result.append(model_data)
            
            print(f"[BUILDER] ✅ Encontrados {len(result)} models no PostgreSQL")
            return result
            
    except Exception as e:
        print(f"[BUILDER] ❌ Erro ao listar models: {e}")
        return []

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
    
    if not session_id or not session_id.strip():
        print(f"[BUILDER] ⚠️  Sem session_id válido, memória não será carregada")
        return memory_data
    
    try:
        print(f"[BUILDER] 🧠 Buscando memória para sessão: {session_id}")
        
        db = get_mongo_db()
        memory_dao = MemoryDAO(db)
        
        memory = memory_dao.get_memory_by_session_id(session_id)
        
        if memory:
            print(f"[BUILDER] ✅ Memória encontrada: {memory.get('_id')}")
            memory_data["memory_object"] = memory
            memory_data["memory_loaded"] = True
            
            conversation_history = memory_dao.get_conversation_history(session_id)
            memory_data["conversation_history"] = conversation_history
            memory_data["total_messages"] = len(conversation_history)
            print(f"[BUILDER] 📜 Histórico carregado: {len(conversation_history)} mensagens")
        else:
            print(f"[BUILDER] ⚠️  Nenhuma memória encontrada para sessão: {session_id}")
        
        return memory_data
        
    except Exception as e:
        print(f"[BUILDER] ❌ Erro ao carregar memória: {e}")
        return memory_data


async def add_assistant_response_to_memory(session_id: str, response: str):
    """
    Adiciona a resposta do assistente à memória
    """
    if not session_id or not response:
        return
    
    try:
        print(f"[BUILDER] ✍️  Adicionando resposta do assistente à memória")
        
        db = get_mongo_db()
        memory_dao = MemoryDAO(db)
        
        memory_dao.add_message_to_memory(
            session_id=session_id,
            sender="assistant",
            content=response
        )
        
        print(f"[BUILDER] ✅ Resposta do assistente adicionada à memória")
        
    except Exception as e:
        print(f"[BUILDER] ❌ Erro ao adicionar resposta: {e}")

# =============================================================
# FUNÇÕES PRINCIPAIS CORRIGIDAS
# =============================================================

def get_default_agent_document(user_id: str = "") -> Dict:
    """
    Retorna APENAS o agente SaphienAI padrão.
    Se não existir no banco, cria um em memória.
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
            # Converte ObjectId para string
            if "_id" in default_agent and isinstance(default_agent["_id"], ObjectId):
                default_agent["_id"] = str(default_agent["_id"])
            return default_agent
        
        # Se não encontrou, NÃO busca outros agentes - cria o SaphienAI em memória
        print(f"[BUILDER] ⚠️  SaphienAI não encontrado no banco, criando em memória...")
        
        memory_agent = SAPHIENAI_AGENT_DATA.copy()
        memory_agent["_id"] = str(ObjectId())
        memory_agent["uid"] = user_id if user_id else "system"
        memory_agent["createdAt"] = {"$date": datetime.utcnow().isoformat() + "Z"}
        memory_agent["updatedAt"] = {"$date": datetime.utcnow().isoformat() + "Z"}
        
        print(f"[BUILDER] ✅ SaphienAI criado em memória")
        return memory_agent
        
    except Exception as e:
        print(f"[BUILDER] ❌ Erro ao buscar agente padrão: {e}")
        
        # Fallback absoluto
        fallback_agent = SAPHIENAI_AGENT_DATA.copy()
        fallback_agent["_id"] = "saphienai_fallback_" + str(uuid.uuid4())[:8]
        fallback_agent["uid"] = user_id if user_id else "system"
        print(f"[BUILDER] ⚠️  Retornando SaphienAI de fallback devido a erro")
        return fallback_agent


def should_use_default_agent(agent_id: Any) -> bool:
    """
    Determina se deve usar o agente padrão SaphienAI
    """
    if agent_id is None:
        print(f"[BUILDER] ✅ Usando padrão: agent_id é None")
        return True
    
    if isinstance(agent_id, str):
        agent_id_str = agent_id.strip()
        
        # String vazia ou apenas espaços
        if not agent_id_str:
            print(f"[BUILDER] ✅ Usando padrão: agent_id string vazia")
            return True
        
        # String com valores inválidos
        if agent_id_str.lower() in ["null", "undefined", "none", "default"]:
            print(f"[BUILDER] ✅ Usando padrão: agent_id = '{agent_id_str}'")
            return True
        
        # IDs zerados ou muito curtos
        if (agent_id_str == "0" or 
            agent_id_str == "000000000000000000000000" or
            len(agent_id_str) < 3):
            print(f"[BUILDER] ✅ Usando padrão: agent_id inválido = '{agent_id_str}'")
            return True
        
        # Verifica se parece ser um ObjectId válido
        if ObjectId.is_valid(agent_id_str):
            # É um ObjectId válido, não usar padrão
            print(f"[BUILDER] ❌ NÃO usar padrão: agent_id é ObjectId válido")
            return False
        else:
            # Não é ObjectId válido, verificar se é um ID string válido
            # Se não for ObjectId e tiver menos de 10 chars, provavelmente inválido
            if len(agent_id_str) < 10:
                print(f"[BUILDER] ✅ Usando padrão: agent_id muito curto = '{agent_id_str}'")
                return True
    
    # Se chegou aqui e não é string, verifica outros tipos
    if agent_id is False or agent_id == 0:
        print(f"[BUILDER] ✅ Usando padrão: agent_id = {agent_id}")
        return True
    
    print(f"[BUILDER] ❌ NÃO usar padrão: agent_id parece válido = {agent_id}")
    return False


def get_agent_document(agent_id: str, user_id: str = "") -> Optional[Dict]:
    """
    Busca o documento do agente - VERSÃO CORRIGIDA
    """
    print(f"\n[BUILDER] 🔍 GET_AGENT_DOCUMENT")
    print(f"[BUILDER] agent_id recebido: '{agent_id}' (tipo: {type(agent_id)})")
    
    # 1. Verifica se deve usar o agente padrão
    if should_use_default_agent(agent_id):
        print(f"[BUILDER] 🎯 Usando agente padrão SaphienAI")
        return get_default_agent_document(user_id)
    
    # 2. Se chegou aqui, agent_id parece válido, tentar buscar
    agent_id_str = str(agent_id).strip()
    print(f"[BUILDER] 🔎 Buscando agente específico: {agent_id_str}")
    
    try:
        # Primeiro tenta como ObjectId
        if ObjectId.is_valid(agent_id_str):
            print(f"[BUILDER] 📍 Tentando buscar como ObjectId")
            agent = AgentDAO.get_agent_by_id(agent_id_str)
            
            if not agent:
                # Tenta buscar diretamente
                db = get_mongo_db()
                agent = db.agents.find_one({"_id": ObjectId(agent_id_str)})
            
            if agent:
                print(f"[BUILDER] ✅ Agente encontrado via ObjectId: {agent.get('name', 'Sem nome')}")
                if "_id" in agent and isinstance(agent["_id"], ObjectId):
                    agent["_id"] = str(agent["_id"])
                return agent
        
        # Se não encontrou como ObjectId, tenta como string
        print(f"[BUILDER] 📍 Tentando buscar como string ID")
        db = get_mongo_db()
        agent = db.agents.find_one({"_id": agent_id_str})
        
        if agent:
            print(f"[BUILDER] ✅ Agente encontrado via string ID: {agent.get('name', 'Sem nome')}")
            return agent
        
        # Se ainda não encontrou, retorna padrão
        print(f"[BUILDER] ⚠️  Agente {agent_id_str} não encontrado, usando padrão")
        return get_default_agent_document(user_id)
        
    except Exception as e:
        print(f"[BUILDER] ❌ Erro ao buscar agente: {e}")
        print(f"[BUILDER] 🔄 Retornando agente padrão devido a erro")
        return get_default_agent_document(user_id)


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
        print(f"[BUILDER] ⚠️  Nenhum override fornecido")
        return result
    
    print(f"[BUILDER] Overrides recebidos: {overrides}")
    
    # Aplica cada override individualmente
    if "tools" in overrides and overrides["tools"]:
        result["tools"] = overrides["tools"]
        print(f"[BUILDER] ✅ Tools substituídas: {len(result['tools'])} tools")
    
    if "mcps" in overrides and overrides["mcps"]:
        # Merge: mantém os do agente e adiciona os overrides
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

# =============================================================
# FUNÇÕES PARA CARREGAR RECURSOS (MONGODB)
# =============================================================

def get_tool_with_config(tool_id: str, user_id: str) -> Optional[Dict]:
    """Busca tool com configuração do usuário"""
    try:
        tool = ToolDAO.get_tool_by_id(tool_id)
        if not tool:
            print(f"[BUILDER] ❌ Tool não encontrada: {tool_id}")
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
        
        print(f"[BUILDER] ✅ Tool carregada: {tool_data['name']}")
        return tool_data
        
    except Exception as e:
        print(f"[BUILDER] ❌ Erro ao carregar tool {tool_id}: {e}")
        return None


def get_mcp_with_connection(mcp_id: str, user_id: str) -> Optional[Dict]:
    """Busca MCP com conexão do usuário"""
    try:
        db = get_mongo_db()
        mcp_server_dao = MCPServerDAO()
        server = mcp_server_dao.getById(mcp_id)
        
        if not server:
            print(f"[BUILDER] ❌ MCP Server não encontrado: {mcp_id}")
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
        
        status = "✅" if mcp_data["connected"] else "❌"
        print(f"[BUILDER] {status} MCP carregado: {mcp_data['server_name']}")
        return mcp_data
        
    except Exception as e:
        print(f"[BUILDER] ❌ Erro ao carregar MCP {mcp_id}: {e}")
        return None


def get_knowledge_base_data(kb_id: str) -> Optional[Dict]:
    """Busca knowledge base"""
    try:
        kb = KnowledgeBaseDAO.get_by_id(kb_id)
        if not kb:
            print(f"[BUILDER] ❌ KB não encontrada: {kb_id}")
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
        
        print(f"[BUILDER] ✅ KB carregada: {kb_data['name']}")
        return kb_data
        
    except Exception as e:
        print(f"[BUILDER] ❌ Erro ao carregar KB {kb_id}: {e}")
        return None

# =============================================================
# FUNÇÃO PRINCIPAL COMPLETA USANDO LLM_DAO
# =============================================================

async def build_agent_for_chat(
    agent_id: str, 
    user_id: str, 
    agent_overrides: Dict = None,
    message: str = "",
    session_id: str = None,
    org_id: str = None,
    project_id: str = None,
    app_id: str = None,
    db=None 
) -> Dict[str, Any]:
    """
    Constrói o agente completo com Model + Provider usando LLM DAO
    """
    print(f"\n{'='*60}")
    print(f"🏗️  AGENT BUILDER v7.0 - COM LLM DAO INTEGRADO")
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
        
        # 2. Buscar agente com lógica corrigida
        print(f"\n[BUILDER] 🔍 BUSCANDO AGENTE...")
        agent_doc = get_agent_document(agent_id, user_id)
        
        if not agent_doc:
            print(f"[BUILDER] ❌ agent_doc é None, usando fallback")
            agent_doc = get_default_agent_document(user_id)
        
        agent_name = agent_doc.get('name', 'Sem nome')
        agent_category = agent_doc.get('category', 'Sem categoria')
        
        # Verifica se é o SaphienAI padrão
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
        
        # 5. CARREGAR MODEL + PROVIDER DO POSTGRES USANDO LLM DAO
        print(f"\n[BUILDER] 🤖 CARREGANDO MODEL + PROVIDER VIA LLM DAO...")
        
        model_data = None
        model_id_str = final_agent.get("model", DEFAULT_MODEL)
        
        # DEBUG: Verifica o valor do model
        print(f"[BUILDER] 📍 Model ID original: '{model_id_str}' (tipo: {type(model_id_str)})")
        
        # Se o model_id estiver vazio, usa o DEFAULT_MODEL
        if not model_id_str or str(model_id_str).strip() == "":
            print(f"[BUILDER] ⚠️  Model ID está vazio, usando padrão: {DEFAULT_MODEL}")
            model_id_str = DEFAULT_MODEL
        
        print(f"[BUILDER] 📍 Model ID após tratamento: '{model_id_str}'")
        
        try:
            # Converter para int
            model_id_int = int(model_id_str)
            
            # Verifica se é um ID válido (maior que 0)
            if model_id_int <= 0:
                print(f"[BUILDER] ⚠️  Model ID inválido ({model_id_int}), usando fallback")
                model_data = await get_model_fallback()
            else:
                print(f"[BUILDER] 🔍 Buscando model ID: {model_id_int} via ModelDAO...")
                
                # USANDO O LLM DAO PARA BUSCAR OS DADOS
                model_data = await get_model_with_provider_by_id(model_id_int)
                
                if not model_data:
                    print(f"[BUILDER] ⚠️  Model {model_id_int} não encontrado, usando fallback")
                    model_data = await get_model_fallback()
                else:
                    print(f"[BUILDER] ✅ Model carregado via LLM DAO")
                    print(f"[BUILDER]   ├─ Nome: {model_data['model_name']}")
                    print(f"[BUILDER]   ├─ Provider: {model_data['provider']['name']}")
                    print(f"[BUILDER]   ├─ Module: {model_data['provider']['module_path']}")
                    print(f"[BUILDER]   ├─ Class: {model_data['provider']['class_name']}")
                    print(f"[BUILDER]   ├─ Config Key: {model_data['provider']['config_key']}")
                    if model_data.get('capabilities'):
                        print(f"[BUILDER]   └─ Capabilities: {model_data['capabilities']}")
        
        except ValueError as e:
            print(f"[BUILDER] ⚠️  Model ID inválido: '{model_id_str}' - {e}, usando fallback")
            model_data = await get_model_fallback()
        except Exception as e:
            print(f"[BUILDER] ❌ Erro ao carregar model: {e}, usando fallback")
            model_data = await get_model_fallback()
        
        print(f"\n[BUILDER] 📊 AGENTE FINAL:")
        print(f"  • Nome: {final_agent['name']}")
        print(f"  • Modelo: {model_data['model_name']}")
        print(f"  • Provider: {model_data['provider']['name']}")
        print(f"  • Tools: {len(final_agent.get('tools', []))}")
        print(f"  • MCPs: {len(final_agent.get('mcps', []))}")
        print(f"  • KBs: {len(final_agent.get('knowledgeBase', []))}")
        
        # 6. Carregar recursos do MongoDB
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
            "model": model_data,  # ⬅️ MODEL + PROVIDER COMPLETO VIA LLM DAO
            "resources": {
                "tools": tools_loaded,
                "mcps": mcps_loaded,
                "knowledgeBase": kbs_loaded,
                # 🔥 ESSENCIAL PARA O EXECUTOR
                "builder_model": model_data
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
                "model_id": model_data.get("id", 1),
                "model_name": model_data.get("model_name", "unknown"),
                "model_type": model_data.get("model_type", "chat"),
                "provider_name": model_data.get("provider", {}).get("name", "unknown"),
                "provider_module": model_data.get("provider", {}).get("module_path", "unknown"),
                "provider_class": model_data.get("provider", {}).get("class_name", "unknown"),
                "provider_config_key": model_data.get("provider", {}).get("config_key", ""),
                "capabilities": model_data.get("capabilities", []),
                "context_window": model_data.get("context_window", 16385),
                "max_tokens": model_data.get("max_tokens", 4096),
                "is_default_agent": is_saphienai,
                "builder_version": "7.0",
                "has_memory": memory_data.get("memory_loaded", False),
                "session_id": session_id,
                "tools_count": len(tools_loaded),
                "mcps_count": len(mcps_loaded),
                "kbs_count": len(kbs_loaded),
                "debug_info": {
                    "input_agent_id": agent_id,
                    "used_default_agent": is_saphienai,
                    "agent_source": "database" if agent_doc.get("_id") else "memory",
                    "model_source": "postgres" if model_data.get("id") and model_data.get("id") != 1 else "fallback",
                    "model_id_used": model_id_str,
                    "model_id_converted": model_data.get("id", 1),
                    "postgres_available": model_data.get("id") != 1 or model_data.get("provider", {}).get("name") != "OpenAI"
                }
            }
        }
        
        # 8. Log final
        print(f"\n{'='*60}")
        print(f"✅ AGENT BUILDER FINALIZADO")
        print(f"{'='*60}")
        print(f"📊 RESUMO:")
        print(f"  • Agente: {final_agent['name']}")
        print(f"  • Modelo: {model_data['model_name']}")
        print(f"  • Provider: {model_data['provider']['name']}")
        print(f"  • É padrão: {is_saphienai}")
        print(f"  • Tools: {len(tools_loaded)}")
        print(f"  • MCPs: {len(mcps_loaded)}")
        print(f"  • KBs: {len(kbs_loaded)}")
        print(f"  • Memória: {memory_data.get('memory_loaded', False)}")
        print(f"  • Source: {'PostgreSQL via LLM DAO' if model_data.get('id') != 1 else 'Fallback'}")
        print(f"{'='*60}")
        
        return result
        
    except Exception as e:
        print(f"[BUILDER] ❌ ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        raise


async def build_agent_from_request(request_data: Dict, db=None) -> Dict[str, Any]:
    """
    Versão simplificada para receber o request diretamente.
    """
    print(f"\n[BUILDER] 📨 REQUEST_DATA:")
    for key, value in request_data.items():
        if key == 'message':
            print(f"  • {key}: '{value[:50]}...'")
        elif key == 'agent_overrides':
            print(f"  • {key}: {value}")
        else:
            print(f"  • {key}: {value}")
 
    flow_type = request_data.get("flow_type", "chat")
    print(f"[BUILDER] 📍 flow_type: '{flow_type}'")
 
    agent_id        = request_data.get("agent_id", "")
    user_id         = request_data.get("user_id", "")
    agent_overrides = request_data.get("agent_overrides", {})
    message         = request_data.get("message", "")
    session_id      = request_data.get("session_id")
    org_id          = request_data.get("org_id")
    project_id      = request_data.get("project_id")
    app_id          = request_data.get("app_id")
 
    # ── Agente base ──────────────────────────────────────────────────────────
    result = await build_agent_for_chat(
        agent_id=agent_id,
        user_id=user_id,
        agent_overrides=agent_overrides,
        message=message,
        session_id=session_id,
        org_id=org_id,
        project_id=project_id,
        app_id=app_id,
        db=db,
    )
 
    # ── Fluxo de imagem: resolve modelo de imagem ────────────────────────────
    if flow_type == "image":
        print(f"\n[BUILDER] 🖼️  PROCESSANDO FLUXO DE IMAGEM")
 
        image_model_id = request_data.get("image_model")
        print(f"[BUILDER] 📍 image_model recebido: '{image_model_id}'")
 
        if not image_model_id:
            raise ValueError("image_model é obrigatório para flow_type = 'image'")
 
        try:
            image_model_id_int = int(image_model_id)
            if image_model_id_int <= 0:
                raise ValueError(f"image_model inválido: {image_model_id}")
 
            print(f"[BUILDER] 🔍 Buscando modelo de imagem ID: {image_model_id_int}")
 
            image_model_data = await get_model_with_provider_by_id(image_model_id_int)
 
            if not image_model_data:
                raise RuntimeError(f"Modelo de imagem {image_model_id} não encontrado")
 
            print(f"[BUILDER] ✅ Modelo de imagem encontrado: {image_model_data['model_name']}")
 
            if "image_models" not in result["resources"]:
                result["resources"]["image_models"] = []
 
            result["resources"]["image_models"].append(image_model_data)
 
            print(f"[BUILDER] ✅ image_models adicionado aos recursos")
            print(f"[BUILDER]   ├─ ID: {image_model_data['id']}")
            print(f"[BUILDER]   ├─ Nome: {image_model_data['model_name']}")
            print(f"[BUILDER]   ├─ Provider: {image_model_data['provider']['name']}")
            print(f"[BUILDER]   └─ Type: {image_model_data.get('model_type', 'image')}")
 
        except ValueError as e:
            raise ValueError(f"image_model deve ser um número inteiro válido: {e}")
        except Exception as e:
            print(f"[BUILDER] ❌ Erro ao carregar modelo de imagem: {e}")
            raise RuntimeError(f"Falha ao carregar modelo de imagem: {str(e)}")
 
    # ── Fluxo de skill: injeta skill_ids no context ──────────────────────────
    # NOVO: garante que skill_ids chegue no builder_result["context"]
    # para que o _run_skill_flow e o SkillAgent possam acessá-los.
    if flow_type == "skill":
        print(f"\n[BUILDER] 🎯 PROCESSANDO FLUXO DE SKILL")
 
        skill_ids = request_data.get("skill_ids", [])
 
        # Aceita tanto lista quanto string simples
        if isinstance(skill_ids, str):
            skill_ids = [s.strip() for s in skill_ids.split(",") if s.strip()]
 
        result["context"]["skill_ids"] = skill_ids
        print(f"[BUILDER] 📍 skill_ids injetados no context: {skill_ids}")
 
        if not skill_ids:
            print(f"[BUILDER] ⚠️  Nenhum skill_id encontrado no request — "
                  f"o skill flow irá falhar mais adiante.")
 
    return result


async def add_assistant_response(request_data: Dict, response_content: str):
    """
    Adiciona a resposta do assistente à memória
    """
    session_id = request_data.get("session_id")
    
    if session_id and response_content:
        print(f"\n[BUILDER] 🧠 Adicionando resposta à memória")
        await add_assistant_response_to_memory(session_id, response_content)
        print(f"[BUILDER] ✅ Resposta adicionada à memória")

