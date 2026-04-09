import os
import asyncio
import json
from typing import Dict, Any, AsyncGenerator, List
from dotenv import load_dotenv
from loguru import logger
import traceback

# Importações do Agno para streaming
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.models.deepseek import DeepSeek
from agno.tools.mcp import MultiMCPTools

# Ajusta o sys.path para permitir imports locais
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from features.tests.agents.agent_knowledge.chroma_client_wrapper import ChromaDbWrapper
    print("[DEBUG] ChromaDbWrapper importado com sucesso")
except ImportError as e:
    print(f"[WARN] Não foi possível importar ChromaDbWrapper: {e}")
    ChromaDbWrapper = None

# ==========================================================
# 1️⃣ CONFIGURAÇÃO INICIAL
# ==========================================================
load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise EnvironmentError("[ERRO] DEEPSEEK_API_KEY deve estar definido no ambiente.")

# ==========================================================
# 2️⃣ FUNÇÕES AUXILIARES (reutilizadas do executor_agent.py)
# ==========================================================
def setup_dynamic_tool_environment(tools_data: list):
    """Configura variáveis de ambiente dinamicamente para tools"""
    if not isinstance(tools_data, list):
        return
    
    for tool_data in tools_data:
        if not isinstance(tool_data, dict):
            continue
            
        tool_config = tool_data.get('config', {})
        tool_name = tool_data.get('name', 'unknown_tool')
        
        if not isinstance(tool_config, dict):
            continue
            
        api_key = tool_config.get('api_key')
        tool_param = tool_config.get('tool_param')
        
        if api_key and tool_param:
            os.environ[tool_param] = api_key
            logger.debug(f"[STREAMING] Configurada variável {tool_param} para tool '{tool_name}'")

def init_knowledge_base(collection_name: str) -> Knowledge | None:
    """Inicializa a base de conhecimento"""
    if not collection_name:
        return None
    if not ChromaDbWrapper:
        return None
        
    try:
        vector_db = ChromaDbWrapper(collection_name=collection_name)
        return Knowledge(vector_db=vector_db, embedding_model=vector_db.embedder)
    except Exception as e:
        logger.warning(f"[STREAMING] Falha ao inicializar base de conhecimento: {e}")
        return None

async def init_mcp_tools(api_base_url: str, user_jwt: str, server_id: str) -> MultiMCPTools | None:
    """Inicializa MCP Tools"""
    import requests
    
    try:
        url = f"{api_base_url}/v1/mcp/connections/{server_id}"
        headers = {"Authorization": f"Bearer {user_jwt}"}
        resp = requests.get(url, headers=headers)
        
        if resp.status_code != 200:
            return None
            
        conn_details = resp.json()
        urls = [conn_details["connection"]]
        transports = [conn_details["transport"]]
        
        mcp_tools = MultiMCPTools(urls=urls, urls_transports=transports)
        await mcp_tools.connect()
        return mcp_tools
        
    except Exception as e:
        logger.warning(f"[STREAMING] Falha ao inicializar MCP Tools: {e}")
        return None

async def get_user_tool_config(user_id: str, user_token: str, api_base_url: str) -> dict:
    """Busca configuração de tools do usuário"""
    import httpx
    
    try:
        api_url = f"{api_base_url}/v1/tool-config/{user_id}"
        headers = {"Authorization": f"Bearer {user_token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url, headers=headers)
            
        if response.status_code != 200:
            return {}
            
        data = response.json()
        return data.get("config", {})
        
    except Exception as e:
        logger.error(f"[STREAMING] Erro ao buscar tool config: {e}")
        return {}

def import_tool_class(module_path: str, class_name: str):
    """Importa dinamicamente uma classe de tool"""
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, class_name)

def build_tool_instance(tool_data: dict, user_config: dict):
    """Constrói instância de tool com configuração do usuário"""
    from inspect import signature, Parameter
    
    if not isinstance(tool_data, dict):
        return None
        
    try:
        tool_class = import_tool_class(tool_data["module_path"], tool_data["class_name"])
    except Exception:
        return None
        
    sig = signature(tool_class.__init__)
    filtered_config = {}
    user_tool_conf = user_config.get(tool_data.get('tool_id') or tool_data.get('id') or tool_data.get('name', ''), {})
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

# ==========================================================
# 3️⃣ IMPLEMENTAÇÃO PRINCIPAL COM AGNO STREAMING NATIVO
# ==========================================================
async def run_executor_streaming(
    agent_data: Dict[str, Any],
    prompt: str,
    user_token: str,
    user_id: str,
    knowledge_collection_name: str = None,
    api_base_url: str = None,
    mcp_server_id: str = None
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Executa o agente executor com streaming usando Agno nativo
    """
    logger.info(f"[STREAMING] Iniciando executor com streaming para agente: {agent_data.get('name')}")
    
    if not isinstance(agent_data, dict):
        yield {"error": "agent_data inválido", "complete": True}
        return

    # Configura ambiente dinâmico
    tools_from_agent = agent_data.get("tools", [])
    setup_dynamic_tool_environment(tools_from_agent)

    try:
        # Configurar modelo DeepSeek
        model = DeepSeek(
            api_key=DEEPSEEK_API_KEY,
            id="deepseek-chat",
            temperature=agent_data.get("model", {}).get("temperature", 0.7),
            max_tokens=agent_data.get("model", {}).get("maxTokens", 2000)
        )
        
        # Configurar Knowledge Base
        knowledge = init_knowledge_base(knowledge_collection_name)
        
        # Configurar MCP Tools
        mcp_tools = None
        if mcp_server_id:
            mcp_tools = await init_mcp_tools(api_base_url, user_token, mcp_server_id)
        
        # Configurar Tools do usuário
        tool_instances = []
        user_config = await get_user_tool_config(user_id, user_token, api_base_url)
        
        if isinstance(tools_from_agent, list):
            for tool_data in tools_from_agent:
                instance = build_tool_instance(tool_data, user_config)
                if instance:
                    tool_instances.append(instance)
        
        # Combinar todas as tools
        all_tools = [mcp_tools] if mcp_tools else []
        all_tools.extend(tool_instances)
        
        # Criar agente Agno com streaming
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
        
        logger.info("[STREAMING] Executando agente com streaming...")
        
        # Executar com streaming usando Agno nativo - correção baseada na documentação
        try:
            # O método arun com stream=True retorna um AsyncIterator[RunResponse]
            # Precisamos usar await para obter o async iterator
            response_stream = await agente_executor.arun(prompt, stream=True)
            
            async for response_chunk in response_stream:
                if hasattr(response_chunk, 'content') and response_chunk.content:
                    yield {"token": response_chunk.content, "complete": False}
                elif isinstance(response_chunk, str) and response_chunk:
                    yield {"token": response_chunk, "complete": False}
            
            # Finalizar stream
            yield {"token": "", "complete": True}
            logger.info("[STREAMING] Stream completo")
            
        except Exception as e:
            logger.error(f"[STREAMING] Erro no streaming Agno: {e}")
            yield {"error": str(e), "complete": True}
        
    except Exception as e:
        logger.error(f"[STREAMING] Erro durante execução: {e}")
        logger.debug(traceback.format_exc())
        yield {"error": str(e), "complete": True}
    finally:
        # Fechar conexões MCP (se foram inicializadas)
        if 'mcp_tools' in locals() and mcp_tools:
            await mcp_tools.close()

# ==========================================================
# 4️⃣ TESTE LOCAL
# ==========================================================
async def main():
    """Função main para testes locais"""
    import sys
    if len(sys.argv) < 2:
        print("Uso: python executor_agent_streaming.py <prompt>")
        sys.exit(1)
    
    prompt = " ".join(sys.argv[1:])
    
    agent_data = {
        "name": "Test Agent",
        "description": "Agente de teste com streaming",
        "model": {"temperature": 0.7, "maxTokens": 2000},
        "tools": [],
        "personalityInstructions": "Responda de forma clara e concisa em português"
    }
    
    print(f"Executando streaming para prompt: {prompt}")
    
    try:
        async for chunk in run_executor_streaming(
            agent_data=agent_data,
            prompt=prompt,
            user_token="test-token",
            user_id="test-user",
            knowledge_collection_name=None,
            api_base_url="http://localhost:8080",
            mcp_server_id=None
        ):
            if chunk.get("complete"):
                print("\n✅ Stream completo")
                break
            elif chunk.get("error"):
                print(f"\n❌ Erro: {chunk.get('error')}")
                break
            else:
                print(chunk.get("token", ""), end="", flush=True)
    
    except Exception as e:
        print(f"\n❌ Erro durante execução: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())