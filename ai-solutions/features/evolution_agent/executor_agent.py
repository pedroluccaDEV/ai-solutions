# executor_agent.py
import os
import asyncio
import json
import traceback
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.models.deepseek import DeepSeek
from agno.tools.mcp import MultiMCPTools

from features.agent.fetch_data import fetch_agent_resources
from dao.mongo.v1.tool_config_dao import ToolConfigDAO

try:
    from features.tests.agents.agent_knowledge.chroma_client_wrapper import ChromaDbWrapper
except ImportError:
    ChromaDbWrapper = None
    print("⚠️ ChromaDbWrapper não disponível")

load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# ========== INSTRUÇÕES DE FORMATAÇÃO WHATSAPP ==========

WHATSAPP_FORMATTING_INSTRUCTIONS = """
📱 FORMATAÇÃO WHATSAPP OBRIGATÓRIA

Ao gerar respostas, siga estritamente estas regras:

• *NEGRITO*: Use *asteriscos* para palavras importantes  
• _ITÁLICO_: Use _sublinhados_ para ênfase suave  
• ~~TACHADO~~: Use ~til~ para correções ou riscos  
• EMOJIS: Use 👍 de forma natural, para expressar sentimentos  
• PARÁGRAFOS: Máximo 2-3 linhas  
• QUEBRAS DE LINHA: Use \\n\\n entre parágrafos, nunca antes ou depois de listas  
• LISTAS: Sempre use • ou - de forma consistente  
• TOM: Conversacional, direto e claro  
• EVITE saudações automáticas como "Olá!" a cada mensagem  
• NUNCA use espaços extras antes de listas ou linhas em branco
"""

# ========== FUNÇÕES AUXILIARES OTIMIZADAS ==========

def init_knowledge_base_hybrid(collection_name: str, enable_hybrid: bool = True) -> Knowledge | None:
    if not collection_name or not ChromaDbWrapper:
        return None
    try:
        print(f"[KB] Inicializando coleção: {collection_name}")
        vector_db = ChromaDbWrapper(
            collection_name=collection_name,
            enable_hybrid_search=enable_hybrid,
            min_similarity_threshold=0.05
        )
        if not vector_db.has_data():
            print(f"⚠️ Coleção '{collection_name}' vazia")
            return None
        return Knowledge(vector_db=vector_db, embedding_model=vector_db.embedder)
    except Exception as e:
        print(f"❌ Erro KB: {e}")
        return None


async def init_mcp_tools(mcp_data: List[dict]) -> Optional[List[MultiMCPTools]]:
    if not mcp_data:
        return None
    tools = []
    for mcp in mcp_data:
        try:
            urls = [mcp.get("connection")] if mcp.get("connection") else []
            transports = [mcp.get("transport")] if mcp.get("transport") else []
            mcp_tool = MultiMCPTools(urls=urls, urls_transports=transports)
            await mcp_tool.connect()
            tools.append(mcp_tool)
        except Exception as e:
            print(f"⚠️ Erro ao inicializar MCP {mcp.get('name', 'unknown')}: {e}")
            continue
    return tools if tools else None


def get_user_tool_config(user_id: str) -> Dict[str, Any]:
    """Busca o tool_config completo do usuário no Mongo."""
    try:
        tool_config_doc = ToolConfigDAO.get_dict_by_user_id(user_id)
        if not tool_config_doc:
            print(f"⚠️ Nenhum tool_config encontrado para user {user_id}")
            return {}
        full_config = tool_config_doc.get("config", {})
        print(f"✅ Tool_config carregado para user {user_id} ({len(full_config)} ferramentas)")
        return full_config
    except Exception as e:
        print(f"❌ Erro ao buscar tool_config: {e}")
        traceback.print_exc()
        return {}


def build_tool_instances(tools_data: list, user_tool_config: Dict[str, Any]) -> List:
    """Constrói instâncias de tools com injeção de API keys igual ao validate_tool.py."""
    import importlib
    instances = []

    for tool_data in tools_data:
        if not isinstance(tool_data, dict):
            continue

        tool_id = str(tool_data.get("_id", ""))
        tool_name = tool_data.get("name", "Unknown")

        # === Importa a classe da tool ===
        try:
            module_path = tool_data["module_path"]
            class_name = tool_data["class_name"]
            module = importlib.import_module(module_path)
            tool_class = getattr(module, class_name)
        except Exception as e:
            print(f"⚠️ Falha ao importar tool {tool_name}: {e}")
            continue

        # === Busca a configuração do usuário ===
        tool_config = user_tool_config.get(tool_id)
        if not tool_config:
            print(f"⚠️ Tool '{tool_name}' sem configuração no banco para este usuário")
            continue

        try:
            inner_key = list(tool_config.keys())[0]
            actual_config = tool_config[inner_key]
            required = actual_config.get("required", {})
            preferences = actual_config.get("preferences", {})
            enabled = actual_config.get("enabled", True)

            if not enabled:
                print(f"⚠️ Tool '{tool_name}' está desabilitada")
                continue
        except Exception as e:
            print(f"⚠️ Estrutura inválida para '{tool_name}': {e}")
            continue

        # === Injeta API key conforme necessidade ===
        kwargs = {}
        if tool_data.get("tool_param"):
            api_key = required.get("api_key")
            if not api_key:
                print(f"⚠️ Tool '{tool_name}' requer API key, mas não foi fornecida")
                continue
            kwargs["api_key"] = api_key
            print(f"🔑 API key injetada para '{tool_name}'")

        # === Instancia e aplica preferências ===
        try:
            instance = tool_class(**kwargs)
            for key, value in preferences.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            instances.append(instance)
            print(f"✅ Tool '{tool_name}' instanciada com sucesso")
        except Exception as e:
            print(f"❌ Erro ao instanciar '{tool_name}': {e}")
            traceback.print_exc()
            continue

    return instances


def build_optimized_prompt(agent_data: dict, prompt: str, original_keywords: Optional[str] = None, proper_nouns: Optional[List[str]] = None) -> str:
    parts = []
    if agent_data.get("roleDefinition"):
        parts.append(f"**Papel**: {agent_data['roleDefinition']}")
    if agent_data.get("goal"):
        parts.append(f"**Objetivo**: {agent_data['goal']}")
    if agent_data.get("agentRules"):
        parts.append(f"**Regras**: {agent_data['agentRules']}")
    if original_keywords:
        search_context = ["**[BUSCA NA KB]**", f"Use estas keywords: `{original_keywords}`"]
        if proper_nouns:
            search_context.append(f"Nomes próprios: {', '.join(proper_nouns)}")
        parts.append("\n".join(search_context))
    parts.append(WHATSAPP_FORMATTING_INSTRUCTIONS)
    extra_context = "\n\n".join(parts) + "\n\n" if parts else ""
    return f"{extra_context}**Instruções do Planner:**\n{prompt}"


# ========== EXECUTOR PRINCIPAL OTIMIZADO ==========

async def run_executor_optimized(
    agent_id: str,
    prompt: str,
    user_id: str,
    original_keywords: Optional[str] = None,
    proper_nouns: Optional[List[str]] = None
) -> Dict[str, Any]:
    try:
        print(f"[EXECUTOR OTIMIZADO] Iniciando para agente: {agent_id}")

        resources = fetch_agent_resources(agent_id, user_id)
        agent_data = resources.get("agent", {})
        tool_data = resources.get("tools", [])
        mcp_data = resources.get("mcps", [])
        knowledge_data = resources.get("knowledge_bases", [])

        # === BUSCA CONFIGURAÇÕES DE TOOLS DO USUÁRIO ===
        user_tool_config = get_user_tool_config(user_id)

        # === Inicializa KB, MCP e TOOLS ===
        knowledge = init_knowledge_base_hybrid(
            knowledge_data[0].get("vector_collection_name") if knowledge_data else None
        ) if knowledge_data else None

        mcp_tools = await init_mcp_tools(mcp_data) if mcp_data else None
        tool_instances = build_tool_instances(tool_data, user_tool_config)

        all_tools = [*tool_instances]
        if mcp_tools:
            all_tools.extend(mcp_tools)

        print(f"[EXECUTOR OTIMIZADO] Total de tools carregadas: {len(all_tools)}")

        full_prompt = build_optimized_prompt(agent_data, prompt, original_keywords, proper_nouns)

        model = DeepSeek(api_key=DEEPSEEK_API_KEY, id="deepseek-chat")

        # CORREÇÃO: Removido o parâmetro 'add_references' que não existe nesta versão
        agent_kwargs = {
            "model": model,
            "tools": all_tools if all_tools else None,
            "description": agent_data.get("description", "Agente executor"),
            "instructions": agent_data.get("personalityInstructions", "") + "\n\n" + WHATSAPP_FORMATTING_INSTRUCTIONS,
            "markdown": True,
            "debug_mode": False
        }

        # Adiciona knowledge apenas se existir e se a versão suportar
        if knowledge:
            agent_kwargs["knowledge"] = knowledge
            agent_kwargs["search_knowledge"] = True
            # Se a versão suportar, pode adicionar também:
            # agent_kwargs["read_chat_history"] = True
            # agent_kwargs["add_context"] = True

        agent_executor = Agent(**agent_kwargs)

        print(f"[EXECUTOR OTIMIZADO] Executando agente...")
        start_time = asyncio.get_event_loop().time()
        
        # Tenta diferentes métodos de execução dependendo da versão
        try:
            # Método novo (arun)
            response = await agent_executor.arun(full_prompt, stream=False)
        except AttributeError:
            try:
                # Método antigo (run)
                response = await agent_executor.run(full_prompt)
            except AttributeError:
                # Método síncrono como fallback
                response = agent_executor.run_sync(full_prompt)
        
        execution_time = asyncio.get_event_loop().time() - start_time
        print(f"[EXECUTOR OTIMIZADO] Execução concluída em {execution_time:.2f}s")

        # Extrai resposta de diferentes formatos possíveis
        if hasattr(response, "content"):
            resposta_limpa = response.content.strip()
        elif hasattr(response, "message"):
            resposta_limpa = response.message.content.strip()
        elif isinstance(response, dict) and "content" in response:
            resposta_limpa = response["content"].strip()
        else:
            resposta_limpa = str(response).strip()

        metadata = {
            "agent_id": agent_id,
            "execution_time_seconds": round(execution_time, 2),
            "used_knowledge_base": bool(knowledge),
            "keywords_used": original_keywords,
            "proper_nouns": proper_nouns,
            "tools_count": len(all_tools),
            "response_type": "complete",
            "whatsapp_formatting": True
        }

        try:
            parsed_response = json.loads(resposta_limpa)
            return {"response": parsed_response, "metadata": metadata}
        except json.JSONDecodeError:
            return {"response": resposta_limpa, "metadata": metadata}

    except Exception as e:
        print(f"❌ [EXECUTOR OTIMIZADO ERRO] {e}")
        traceback.print_exc()
        return {
            "response": f"Desculpe, ocorreu um erro ao processar sua mensagem: {str(e)}",
            "metadata": {
                "agent_id": agent_id,
                "execution_time_seconds": 0,
                "used_knowledge_base": False,
                "tools_count": 0,
                "response_type": "error",
                "whatsapp_formatting": False,
                "error": str(e)
            }
        }


async def run_executor(agent_id: str, prompt: str, user_id: str,
                       original_keywords: Optional[str] = None,
                       proper_nouns: Optional[List[str]] = None) -> str:
    result = await run_executor_optimized(
        agent_id=agent_id,
        prompt=prompt,
        user_id=user_id,
        original_keywords=original_keywords,
        proper_nouns=proper_nouns
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import sys
    async def test_optimized():
        if len(sys.argv) < 3:
            print("Uso: python executor_agent_optimized.py <agent_id> <user_id>")
            sys.exit(1)
        agent_id = sys.argv[1]
        user_id = sys.argv[2]
        prompt = input("Digite sua mensagem: ")
        result = await run_executor_optimized(agent_id, prompt, user_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    asyncio.run(test_optimized())