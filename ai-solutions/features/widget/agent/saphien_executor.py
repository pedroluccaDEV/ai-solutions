# features/channels/webhook_saphien/agent/saphien_executor.py
"""
Executor para Saphien Agent.

Diferenças do executor do Telegram:
- Formatação de resposta otimizada para widget web
- Instruções de formatação injetadas no system prompt
- Token tracking mantido
- Suporte a tools, MCPs e knowledge base via Agno
"""

import os
import asyncio
import importlib
import re
import traceback
import tiktoken
from datetime import datetime
from typing import Optional, List, Dict, Any, AsyncGenerator

from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.tools.mcp import MultiMCPTools

from dao.mongo.v1.tool_config_dao import ToolConfigDAO

try:
    from features.tests.agents.agent_knowledge.chroma_client_wrapper import ChromaDbWrapper
except ImportError:
    ChromaDbWrapper = None

from features.channels.webhook_saphien.agent.saphien_builder import load_llm_from_builder_model


# =====================================================
# HELPERS
# =====================================================

def _extract_executor_instructions(planner_text: str) -> str:
    """Extrai SOMENTE a parte relevante do planner."""
    if not planner_text:
        return ""

    match = re.search(
        r"## INSTRUÇÕES AO EXECUTOR(.*?)(##|$)",
        planner_text,
        re.S | re.I
    )

    if match:
        return match.group(1).strip()
    
    return planner_text.strip()


def _safe_truncate(text: str, max_chars: int) -> str:
    """Trunca texto de forma segura sem quebrar palavras no meio."""
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    
    truncated = text[:max_chars]
    last_space = truncated.rfind(' ')
    if last_space > max_chars * 0.8:
        return truncated[:last_space] + "..."
    
    return truncated + "..."


def _count_tokens(text: str) -> int:
    """Conta tokens usando tiktoken (cl100k_base)."""
    try:
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return int(len(text.split()) * 1.3)


def _token_event(input_t: int, output_t: int, stage: str, model: str = None) -> Dict:
    """Cria evento de token usage."""
    return {
        "type": "token_usage",
        "data": {
            "input_tokens":  input_t,
            "output_tokens": output_t,
            "total_tokens":  input_t + output_t,
            "stage":         stage,
            "timestamp":     datetime.now().isoformat(),
            "model_used":    model,
        },
    }


# =====================================================
# FORMATAÇÃO SAPHIEN WIDGET
# =====================================================

SAPHIEN_SYSTEM_INSTRUCTIONS = """
## FORMATAÇÃO OBRIGATÓRIA — Saphien Widget

Você está respondendo via widget de chat web. Siga SEMPRE estas regras:

• **negrito**: Use **asteriscos duplos** para palavras ou termos importantes
• *itálico*: Use *asteriscos simples* para ênfase suave
• `código`: Use crases para comandos ou trechos de código
• Emojis: Use de forma natural e contextual (sem exagerar)
• Parágrafos: Máximo 2-3 linhas por parágrafo
• Listas: Use • ou - de forma consistente
• Tom: Conversacional, direto, humano e claro
• NUNCA use blocos de código longos (```) a menos que seja realmente necessário
• Quebre linhas com \n\n entre parágrafos
• Evite saudações repetitivas
• Respostas concisas são melhores do que longas e detalhadas demais

Adapte o tamanho da resposta ao contexto:
- Saudações/agradecimentos: 1-2 linhas
- Perguntas simples: 2-4 linhas
- Perguntas complexas: Parágrafos curtos, máx. 10-12 linhas
"""


# =====================================================
# SYSTEM PROMPT OTIMIZADO
# =====================================================

def _build_system_prompt(
    agent_data: Dict,
    planner_instructions: str,
    conversation_history: List[Dict],
    session_id: Optional[str],
    resources_warning: Optional[str] = None,
) -> str:
    """Constrói system prompt com tokens reduzidos e avisos de recursos."""
    parts = []

    role = _safe_truncate(agent_data.get("roleDefinition", ""), 500)
    goal = _safe_truncate(agent_data.get("goal", ""), 300)
    rules = _safe_truncate(agent_data.get("agentRules", ""), 500)
    personality = _safe_truncate(agent_data.get("personalityInstructions", ""), 300)

    if role:
        parts.append(f"**Seu Papel:**\n{role}")
    if goal:
        parts.append(f"**Seu Objetivo:**\n{goal}")
    if rules:
        parts.append(f"**Suas Regras:**\n{rules}")
    if personality:
        parts.append(f"**Personalidade:**\n{personality}")

    if conversation_history:
        recent = conversation_history[-6:]
        history_lines = ["**Histórico Recente:**"]
        for msg in recent:
            role_label = "Usuário" if msg.get("role") == "user" else "Assistente"
            content = msg.get("content", "")
            preview = _safe_truncate(content, 120)
            history_lines.append(f"{role_label}: {preview}")
        parts.append("\n".join(history_lines))

    clean_instructions = _extract_executor_instructions(planner_instructions)
    parts.append(f"**Instruções de Execução:**\n{clean_instructions}")

    # 🔥 Adiciona aviso sobre recursos com falha
    if resources_warning:
        parts.append(f"**⚠️ AVISO SOBRE RECURSOS:**\n{resources_warning}")

    parts.append(SAPHIEN_SYSTEM_INSTRUCTIONS)

    return "\n\n".join(parts)


# =====================================================
# RECURSOS — KB / MCP / TOOLS
# =====================================================

def _init_knowledge_base(collection_name: str) -> Optional[Knowledge]:
    """Inicializa knowledge base com ChromaDB."""
    if not collection_name or not ChromaDbWrapper:
        return None
    try:
        vdb = ChromaDbWrapper(
            collection_name=collection_name,
            enable_hybrid_search=True,
            min_similarity_threshold=0.05,
        )
        if not vdb.has_data():
            print(f"[SAPHIEN EXEC] ⚠️ KB '{collection_name}' vazia")
            return None
        return Knowledge(vector_db=vdb)
    except Exception as e:
        print(f"[SAPHIEN EXEC] ❌ Erro ao inicializar KB: {e}")
        return None


async def _init_mcp_tools(mcp_data: List[Dict]) -> Optional[List[MultiMCPTools]]:
    """
    Inicializa conexões MCP com logs detalhados.
    """
    print(f"\n[SAPHIEN EXEC] 🔌 Inicializando MCPs...")
    print(f"[SAPHIEN EXEC] 📋 Total de MCPs recebidos: {len(mcp_data)}")
    
    if not mcp_data:
        print(f"[SAPHIEN EXEC] ⚠️ Nenhum MCP fornecido")
        return None
    
    active = []
    for idx, mcp in enumerate(mcp_data):
        # 🔥 Extrai nome de múltiplas fontes possíveis
        name = (
            mcp.get("server_name") or 
            mcp.get("name") or 
            mcp.get("server", {}).get("name") or 
            f"MCP_{idx}"
        )
        
        # 🔥 Extrai URL de múltiplas fontes
        url = (
            mcp.get("connection") or 
            mcp.get("connection_data", {}).get("connection") or
            mcp.get("url")
        )
        
        # 🔥 Extrai transport
        transport = (
            mcp.get("transport") or 
            mcp.get("connection_data", {}).get("transport") or 
            "streamable-http"
        )
        
        # 🔥 Extrai status de conexão
        connected = (
            mcp.get("connected", False) or 
            mcp.get("connection_data", {}).get("connected", False)
        )
        
        print(f"\n[SAPHIEN EXEC] 📍 Processando MCP {idx + 1}/{len(mcp_data)}:")
        print(f"  ├─ Nome: {name}")
        print(f"  ├─ URL: {url[:50] if url else 'N/A'}...")
        print(f"  ├─ Transport: {transport}")
        print(f"  └─ Conectado: {connected}")

        if not connected:
            print(f"[SAPHIEN EXEC] ⚠️ MCP '{name}' desconectado — ignorado")
            continue
            
        if not url:
            print(f"[SAPHIEN EXEC] ⚠️ MCP '{name}' sem URL — ignorado")
            continue

        try:
            print(f"[SAPHIEN EXEC] 🔌 Conectando ao MCP '{name}'...")
            tool = MultiMCPTools(urls=[url], urls_transports=[transport])
            await tool.connect()
            active.append(tool)
            print(f"[SAPHIEN EXEC] ✅ MCP '{name}' conectado com sucesso!")
        except Exception as e:
            print(f"[SAPHIEN EXEC] ❌ MCP '{name}' falhou: {e}")
    
    print(f"\n[SAPHIEN EXEC] 📊 Resumo MCPs: {len(active)}/{len(mcp_data)} conectados")
    return active if active else None


def _get_user_tool_config(user_id: str) -> Dict:
    """Busca configuração de tools do usuário."""
    try:
        doc = ToolConfigDAO.get_dict_by_user_id(user_id)
        return doc.get("config", {}) if doc else {}
    except Exception as e:
        print(f"[SAPHIEN EXEC] Erro ao buscar tool_config: {e}")
        return {}


def _build_tool_instances(tools_data: List[Dict], user_tool_config: Dict) -> List:
    """
    Instancia ferramentas a partir da configuração com logs detalhados.
    """
    print(f"\n[SAPHIEN EXEC] 🔧 Inicializando Tools...")
    print(f"[SAPHIEN EXEC] 📋 Total de Tools recebidas: {len(tools_data)}")
    
    instances = []
    for idx, tool in enumerate(tools_data):
        if not isinstance(tool, dict):
            continue

        name = tool.get("name", f"Tool_{idx}")
        module_path = tool.get("module_path", "")
        class_name = tool.get("class_name", "")

        if not module_path or not class_name:
            print(f"[SAPHIEN EXEC] ⚠️ Tool '{name}' sem module_path/class_name — ignorada")
            continue
            
        if not tool.get("active", True):
            print(f"[SAPHIEN EXEC] ⚠️ Tool '{name}' inativa — ignorada")
            continue

        user_config = tool.get("user_config", {})
        is_configured = any(
            cfg.get("enabled", False)
            for cfg in user_config.values()
            if isinstance(cfg, dict)
        ) if user_config else not tool.get("requires_auth", False)

        if tool.get("requires_auth", False) and not is_configured:
            print(f"[SAPHIEN EXEC] ⚠️ Tool '{name}' sem config — ignorada")
            continue

        try:
            module = importlib.import_module(module_path)
            tool_class = getattr(module, class_name)
            kwargs = dict(tool.get("tool_param") or {})

            api_key = tool.get("api_key")
            if api_key and tool.get("requires_auth", False):
                kwargs.setdefault("api_key", api_key)

            instance = tool_class(**kwargs) if kwargs else tool_class()
            instances.append(instance)
            print(f"[SAPHIEN EXEC] ✅ Tool '{name}' instanciada")
        except Exception as e:
            print(f"[SAPHIEN EXEC] ❌ Tool '{name}' falhou: {e}")

    print(f"[SAPHIEN EXEC] 📊 Resumo Tools: {len(instances)}/{len(tools_data)} instanciadas")
    return instances


# =====================================================
# EXECUTOR PRINCIPAL (NÃO-STREAMING)
# =====================================================

async def run_saphien_executor(
    agent_id: str,
    prompt: str,
    user_id: str,
    resources: Dict[str, Any],
    resources_analyzed: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Versão síncrona/não-streaming do executor.
    Coleta toda a resposta antes de retornar.
    """
    full_response = ""
    total_input_t = 0
    total_output_t = 0
    model_used = None

    try:
        print(f"\n[SAPHIEN EXEC] 🚀 Iniciando execução (modo síncrono) para agente {agent_id}")

        agent_data = resources.get("agent", {})
        tool_data = resources.get("tools", [])
        mcp_data = resources.get("mcps", [])
        
        kb_data = (
            resources.get("knowledge_bases") 
            or resources.get("knowledgeBase") 
            or []
        )
        
        builder_model = resources.get("builder_model")
        context = resources.get("context", {})

        session_id = context.get("session_id")
        conversation_history = context.get("conversation_history", [])

        # 🔥 Pega avisos do builder
        resources_warning = resources.get("resources_warning")
        failed_tools = resources.get("failed_tools", [])
        failed_mcps = resources.get("failed_mcps", [])
        failed_kbs = resources.get("failed_kbs", [])

        if not builder_model:
            raise RuntimeError("builder_model não encontrado nos recursos")

        model_used = builder_model.get("model_name")

        # 🔥 Log detalhado dos recursos
        print(f"\n[SAPHIEN EXEC] 📦 RECURSOS RECEBIDOS:")
        print(f"  ├─ Tools: {len(tool_data)}/{len(failed_tools) + len(tool_data)} carregadas")
        print(f"  ├─ MCPs: {len(mcp_data)}/{len(failed_mcps) + len(mcp_data)} carregados")
        print(f"  ├─ KBs: {len(kb_data)}/{len(failed_kbs) + len(kb_data)} carregadas")
        print(f"  └─ Model: {model_used}")

        # 🔥 Log de falhas
        if failed_tools:
            print(f"\n[SAPHIEN EXEC] ⚠️ Tools com falha:")
            for tool in failed_tools:
                print(f"  ❌ {tool.get('name', tool.get('id', '?'))}: {tool.get('error', 'Erro desconhecido')}")

        if failed_mcps:
            print(f"\n[SAPHIEN EXEC] ⚠️ MCPs com falha:")
            for mcp in failed_mcps:
                print(f"  ❌ {mcp.get('name', mcp.get('id', '?'))}: {mcp.get('error', 'Erro desconhecido')}")

        if failed_kbs:
            print(f"\n[SAPHIEN EXEC] ⚠️ KBs com falha:")
            for kb in failed_kbs:
                print(f"  ❌ {kb.get('name', kb.get('id', '?'))}: {kb.get('error', 'Erro desconhecido')}")

        # 🔥 Log detalhado dos MCPs recebidos
        if mcp_data:
            print(f"\n[SAPHIEN EXEC] 📋 Detalhes dos MCPs recebidos:")
            for idx, mcp in enumerate(mcp_data):
                print(f"  {idx + 1}. Nome: {mcp.get('server_name', mcp.get('name', '?'))}")
                print(f"     Conectado: {mcp.get('connected', False)}")
                print(f"     URL: {mcp.get('connection', 'N/A')[:50]}...")
        
        user_tool_config = _get_user_tool_config(user_id)
        tool_instances = _build_tool_instances(tool_data, user_tool_config)
        mcp_tools = await _init_mcp_tools(mcp_data)

        knowledge = None
        if kb_data:
            # Pega a primeira KB que tem dados
            for kb in kb_data:
                collection = kb.get("vector_collection_name")
                if collection and kb.get("has_data", True):
                    knowledge = _init_knowledge_base(collection)
                    if knowledge:
                        break
                    else:
                        print(f"[SAPHIEN EXEC] ⚠️ Falha ao inicializar KB '{kb.get('name', collection)}'")

        all_tools = tool_instances + (mcp_tools or [])

        print(f"\n[SAPHIEN EXEC] 📊 RECURSOS INICIALIZADOS:")
        print(f"  ├─ Tools instanciadas: {len(tool_instances)}")
        print(f"  ├─ MCPs conectados: {len(mcp_tools) if mcp_tools else 0}")
        print(f"  ├─ KB inicializada: {bool(knowledge)}")
        print(f"  └─ Total ferramentas: {len(all_tools)}")

        # 🔥 Constrói system prompt com avisos
        system_prompt = _build_system_prompt(
            agent_data=agent_data,
            planner_instructions=prompt,
            conversation_history=conversation_history,
            session_id=session_id,
            resources_warning=resources_warning,
        )

        total_input_t = _count_tokens(system_prompt)
        print(f"\n[SAPHIEN EXEC] 📝 System prompt construído: {total_input_t} tokens")

        model = load_llm_from_builder_model(builder_model)

        agent = Agent(
            model=model,
            tools=all_tools if all_tools else None,
            knowledge=knowledge,
            description=agent_data.get("description", "Agente Saphien Widget"),
            markdown=True,  # Widget suporta markdown básico
            debug_mode=False,
        )

        print(f"\n[SAPHIEN EXEC] 📡 Executando agente...")
        response = await agent.arun(system_prompt, stream=False)

        full_response = response.content if hasattr(response, "content") else str(response)
        total_output_t = _count_tokens(full_response)

        print(f"\n[SAPHIEN EXEC] ✅ Execução concluída:")
        print(f"  ├─ Tokens input: {total_input_t}")
        print(f"  ├─ Tokens output: {total_output_t}")
        print(f"  ├─ Total tokens: {total_input_t + total_output_t}")
        print(f"  └─ Resposta: {len(full_response)} caracteres")

        return {
            "response": full_response,
            "input_tokens": total_input_t,
            "output_tokens": total_output_t,
            "model_used": model_used,
        }

    except Exception as e:
        print(f"\n[SAPHIEN EXEC] ❌ ERRO na execução: {e}")
        traceback.print_exc()
        return {
            "response": full_response or f"Erro: {str(e)}",
            "input_tokens": total_input_t,
            "output_tokens": total_output_t,
            "model_used": model_used,
            "error": str(e),
        }