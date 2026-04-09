from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.models.deepseek import DeepSeek
from agno.tools.mcp import MultiMCPTools
import os
import sys
import re
import asyncio
from textwrap import dedent
from dotenv import load_dotenv
import requests
import importlib
import httpx
import traceback
import json

# Ajusta o sys.path para permitir imports locais
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"[DEBUG] Adicionado {project_root} ao sys.path")

try:
    from features.tests.agents.agent_knowledge.chroma_client_wrapper import ChromaDbWrapper
    print("[DEBUG] ChromaDbWrapper importado com sucesso")
except ImportError as e:
    print(f"[WARN] Não foi possível importar ChromaDbWrapper: {e}")
    ChromaDbWrapper = None

# ---------------- ENV ---------------- #
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

print("[DEBUG] Variáveis de ambiente carregadas")

def get_env_var(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(f"[ERRO] Variável de ambiente '{key}' não encontrada.")
    print(f"[DEBUG] Variável de ambiente '{key}' encontrada")
    return value

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = get_env_var("OPENROUTER_API_KEY")

# ---------------- Limpeza ANSI ---------------- #
def limpar_ansi(texto):
    if not texto:
        return ""
    ansi_regex = r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])'
    return re.sub(ansi_regex, '', texto)

# ---------------- Knowledge Base ---------------- #
def init_knowledge_base(collection_name: str) -> Knowledge | None:
    print(f"[DEBUG] Inicializando Knowledge Base com collection_name='{collection_name}'")
    if not collection_name:
        print("[WARN] Nome da collection não fornecido")
        return None
    if not ChromaDbWrapper:
        print("[WARN] ChromaDbWrapper não disponível, ignorando Knowledge Base")
        return None
    try:
        vector_db = ChromaDbWrapper(collection_name=collection_name)
        print("[DEBUG] Knowledge Base inicializada com sucesso")
        return Knowledge(vector_db=vector_db, embedding_model=vector_db.embedder)
    except Exception as e:
        print(f"[WARN] Falha ao inicializar base de conhecimento: {e}")
        return None

# ---------------- MCP ---------------- #
def get_mcp_connection_details(api_base_url: str, user_jwt: str, server_id: str) -> dict:
    print(f"[DEBUG] Buscando detalhes da conexão MCP: server_id={server_id}")
    url = f"{api_base_url}/v1/mcp/connections/{server_id}"
    headers = {"Authorization": f"Bearer {user_jwt}"}
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        raise RuntimeError(f"[ERRO] Falha ao buscar detalhes da conexão MCP: {resp.text}")
    print("[DEBUG] Conexão MCP encontrada")
    return resp.json()

def init_mcp_tools(api_base_url: str, user_jwt: str, server_id: str) -> MultiMCPTools | None:
    try:
        conn_details = get_mcp_connection_details(api_base_url, user_jwt, server_id)
        if not conn_details:
            print("[WARN] Nenhuma conexão MCP encontrada.")
            return None
        urls = [conn_details["connection"]]
        transports = [conn_details["transport"]]
        print("[DEBUG] MCP Tools inicializadas")
        return MultiMCPTools(urls=urls, urls_transports=transports)
    except Exception as e:
        print(f"[WARN] Falha ao inicializar MCP Tools: {e}")
        return None

# ---------------- User Tools ---------------- #
async def get_user_tool_config(user_id: str, user_token: str) -> dict:
    print(f"[DEBUG] Buscando tool config para o usuário {user_id}")
    api_url = f"http://localhost:8000/v1/tool-config/{user_id}"
    headers = {"Authorization": f"Bearer {user_token}"}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url, headers=headers)
        if response.status_code != 200:
            print(f"[WARN] Falha ao buscar tool config do usuário {user_id}: {response.text}")
            return {}
        data = response.json()
        config = data.get("config", {})
        print(f"[DEBUG] Tool config carregada: {list(config.keys()) if config else 'vazia'}")
        return config
    except Exception as e:
        print(f"[ERRO] Exceção ao buscar tool config do usuário {user_id}: {e}")
        return {}

# ---------------- CONFIGURAÇÃO DINÂMICA DE AMBIENTE ---------------- #
def setup_dynamic_tool_environment(tools_data: list):
    print(f"[DEBUG] === CONFIGURANDO AMBIENTE DINÂMICO ===")
    print(f"[DEBUG] tools_data type: {type(tools_data)}, length: {len(tools_data) if isinstance(tools_data, list) else 'N/A'}")
    if not isinstance(tools_data, list):
        print(f"[WARN] tools_data deveria ser list, convertendo de {type(tools_data)}")
        tools_data = []
    for i, tool_data in enumerate(tools_data):
        try:
            print(f"[DEBUG] === PROCESSANDO TOOL {i} PARA AMBIENTE ===")
            if not isinstance(tool_data, dict):
                print(f"[WARN] Tool {i} não é dict, ignorando")
                continue
            tool_config = tool_data.get('config', {})
            tool_name = tool_data.get('name', f'tool_{i}')
            if not isinstance(tool_config, dict):
                continue
            api_key = tool_config.get('api_key')
            tool_param = tool_config.get('tool_param')
            if api_key and tool_param:
                os.environ[tool_param] = api_key
                print(f"[DEBUG] {tool_param} configurada para tool '{tool_name}'")
        except Exception as e:
            print(f"[ERRO] Erro ao processar configuração de ambiente para tool {i}: {e}")
            traceback.print_exc()
            continue

def import_tool_class(module_path: str, class_name: str):
    print(f"[DEBUG] Importando {class_name} de {module_path}")
    module = importlib.import_module(module_path)
    return getattr(module, class_name)

def build_tool_instance(tool_data: dict, user_config: dict):
    from inspect import signature, Parameter
    if not isinstance(tool_data, dict):
        return None
    if not isinstance(user_config, dict):
        user_config = {}
    tool_id = tool_data.get('tool_id') or tool_data.get('id') or tool_data.get('name', '<desconhecida>')
    try:
        tool_class = import_tool_class(tool_data["module_path"], tool_data["class_name"])
    except Exception:
        return None
    sig = signature(tool_class.__init__)
    filtered_config = {}
    user_tool_conf = user_config.get(tool_id, {})
    tool_internal_config = tool_data.get('config', {})
    for name, param in sig.parameters.items():
        if name == "self":
            continue
        if name in user_tool_conf:
            filtered_config[name] = user_tool_conf[name]
        elif name == "api_key" and tool_internal_config.get("api_key"):
            filtered_config[name] = tool_internal_config["api_key"]
        elif name in tool_internal_config:
            filtered_config[name] = tool_internal_config[name]
        elif param.default is not Parameter.empty:
            filtered_config[name] = param.default
    try:
        return tool_class(**filtered_config)
    except Exception:
        return None

# ---------------- Executor Runner ---------------- #
async def run_executor(agent_data: dict,
                       prompt: str,
                       user_token: str,
                       user_id: str,
                       knowledge_collection_name: str = None,
                       api_base_url: str = None,
                       mcp_server_id: str = None) -> str:
    print(f"[DEBUG] === INICIANDO run_executor ===")
    if not isinstance(agent_data, dict):
        return "[ERRO] agent_data inválido"

    tools_from_agent = agent_data.get("tools", [])
    setup_dynamic_tool_environment(tools_from_agent)

    model_info = agent_data.get("model", {})
    print(f"[DEBUG] Inicializando modelo DeepSeek")

    provider = DeepSeek
    model = provider(
        api_key=DEEPSEEK_API_KEY,
        id="deepseek-chat",
    )

    knowledge = init_knowledge_base(knowledge_collection_name)

    mcp_tools = None
    if mcp_server_id:
        mcp_tools = init_mcp_tools(api_base_url, user_token, mcp_server_id)
        if mcp_tools:
            await mcp_tools.connect()

    tool_instances = []
    user_config = await get_user_tool_config(user_id, user_token)
    if isinstance(tools_from_agent, list):
        for tool_data in tools_from_agent:
            instance = build_tool_instance(tool_data, user_config)
            if instance:
                tool_instances.append(instance)

    all_tools = [mcp_tools] if mcp_tools else []
    all_tools.extend(tool_instances)

    try:
        agente_executor = Agent(
            model=model,
            knowledge=knowledge,
            search_knowledge=True if knowledge else False,
            add_references=True if knowledge else False,
            tools=all_tools,
            description=agent_data.get("description", "Agente técnico"),
            instructions=agent_data.get("personalityInstructions", ""),
            markdown=True,
            debug_mode=False
        )

        print("[INFO] Executando agente (consulta KB + Tools)...")
        resposta = await agente_executor.arun(prompt)

        # --- Contabilização de tokens ---
        total_tokens = None
        if hasattr(resposta, "metrics") and resposta.metrics:
            total_tokens = resposta.metrics.get("total_tokens")
        if total_tokens is None and hasattr(resposta, "raw"):
            if isinstance(resposta.raw, dict):
                usage = resposta.raw.get("usage")
                if usage:
                    total_tokens = usage.get("total_tokens") or (
                        (usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0))
                    )
        if total_tokens is not None:
            print(f"\n[INFO] Tokens totais usados (entrada + saída): {total_tokens}\n")
        else:
            print("\n[INFO] Não foi possível recuperar informações de tokens.")
            print("[DEBUG] Conteúdo de resposta.raw:")
            print(resposta.raw)

        resposta_limpa = resposta.content.strip()
        try:
            parsed = json.loads(resposta_limpa)
            final = {"response": parsed}
        except json.JSONDecodeError:
            final = {"response": resposta_limpa}

        resposta_json = json.dumps(final, ensure_ascii=False, indent=2)
        print(resposta_json)
        return resposta_limpa

    except Exception as e:
        print(f"[ERRO] Falha ao executar executor: {e}")
        traceback.print_exc()
        return f"[ERRO] {str(e)}"
    finally:
        if mcp_tools:
            await mcp_tools.close()

# ---------------- Main ---------------- #
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❗ Informe o caminho de um arquivo JSON com agent_data ou mensagem como argumento.")
        sys.exit(1)

    arg = sys.argv[1]
    if arg.endswith(".json"):
        with open(arg, "r", encoding="utf-8") as f:
            agent_data = json.load(f)
        prompt = input("Digite sua mensagem para o agente: ")
    else:
        agent_data = {
            "description": "Agente genérico",
            "model": {},
            "rulesFile": {},
            "personalityInstructions": ""
        }
        prompt = " ".join(sys.argv[1:])

    asyncio.run(run_executor(
        agent_data=agent_data,
        prompt=prompt,
        knowledge_collection_name=os.getenv("KNOWLEDGE_COLLECTION"),
        user_token=os.getenv("USER_JWT"),
        user_id=os.getenv("USER_ID"),
        api_base_url=os.getenv("API_BASE_URL"),
        mcp_server_id=os.getenv("MCP_SERVER_ID")
    ))