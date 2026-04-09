import asyncio
import json
import os
import sys
import requests
import importlib
import traceback
import httpx
from dotenv import load_dotenv
from inspect import signature

from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.tools.mcp import MultiMCPTools
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.models.openai import OpenAIChat
from agno.models.openrouter import OpenRouter
from agno.tools.mcp import MultiMCPTools
from features.tests.agents.agent_knowledge.chroma_client_wrapper import ChromaDbWrapper

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL")
USER_JWT = os.getenv("USER_JWT")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

HEADERS = {"Authorization": f"Bearer {USER_JWT}"} if USER_JWT else {}

# -------- API Fetch Helpers --------
async def fetch_json(url: str, headers: dict = None):
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()

async def get_agent_data(agent_id: str):
    return await fetch_json(f"{API_BASE_URL}/v1/agents/{agent_id}", headers=HEADERS)

async def get_tool_data(tool_id: str):
    return await fetch_json(f"{API_BASE_URL}/v1/tools/{tool_id}", headers=HEADERS)

async def get_user_tool_config(user_id: str):
    data = await fetch_json(f"{API_BASE_URL}/v1/tool-config/{user_id}", headers=HEADERS)
    return data.get("config", {})

def get_mcp_connections():
    resp = requests.get(f"{API_BASE_URL}/v1/mcp/connections", headers=HEADERS)
    resp.raise_for_status()
    return resp.json()

async def get_kb_data(kb_id: str):
    return await fetch_json(f"{API_BASE_URL}/v1/kb/{kb_id}", headers=HEADERS)

# -------- Tool Loader --------
def import_tool_class(module_path: str, class_name: str):
    module = importlib.import_module(module_path)
    return getattr(module, class_name)

def build_tool_instance(tool_data: dict, user_config: dict):
    tool_class = import_tool_class(tool_data["module_path"], tool_data["class_name"])
    valid_params = signature(tool_class.__init__).parameters
    filtered_config = {k: v for k, v in user_config.items() if k in valid_params and k != "self"}
    return tool_class(**filtered_config)

# -------- Agent Builder --------
async def build_agent(agent_id: str, user_id: str):
    agent_data = await get_agent_data(agent_id)

    tool_instances = []
    if agent_data.get("tools"):
        user_tool_configs = await get_user_tool_config(user_id)
        for tool_id in agent_data["tools"]:
            config = user_tool_configs.get(tool_id, {})
            if config.get("enabled"):
                try:
                    tool_data = await get_tool_data(tool_id)
                    instance = build_tool_instance(tool_data, config)
                    tool_instances.append(instance)
                except Exception as e:
                    print(f"[ERRO] Falha ao carregar tool {tool_id}: {e}")
                    traceback.print_exc()

    mcp_tools = None
    if agent_data.get("mcp"):
        connections = get_mcp_connections()
        if connections:
            urls = [conn["connection"] for conn in connections]
            transports = [conn["transport"] for conn in connections]
            mcp_tools = MultiMCPTools(urls=urls, urls_transports=transports)

    kb_obj = None
    if agent_data.get("knowledgeBase"):
        for kb_id in agent_data["knowledgeBase"]:
            try:
                kb_data = await get_kb_data(kb_id)
                vector_db = ChromaDbWrapper(collection_name=kb_data.get("collectionName", kb_id))
                kb_obj = Knowledge(vector_db=vector_db, embedding_model=vector_db.embedder)
            except Exception as e:
                print(f"[ERRO] Falha ao carregar KB {kb_id}: {e}")

    model_data = agent_data.get("model", {})
    provider = model_data.get("provider", "openai")
    model_id = model_data.get("full", "gpt-3.5-turbo")

    if provider == "openai":
        model = OpenAIChat(id=model_id, api_key=OPENAI_API_KEY)
    elif provider == "openrouter":
        model = OpenRouter(id=model_id, api_key=OPENROUTER_API_KEY)
    else:
        raise ValueError(f"Provider {provider} não suportado.")

    tools_final = tool_instances[:]
    if mcp_tools:
        tools_final.append(mcp_tools)

    agent = Agent(
        model=model,
        tools=tools_final if tools_final else None,
        knowledge=kb_obj,
        description=agent_data.get("description"),
        instructions=agent_data.get("personalityInstructions"),
        markdown=True,
        debug_mode=True
    )

    return agent, mcp_tools

# -------- Runner --------
async def run_agent(agent_id: str, user_id: str, prompt: str):
    agent, mcp_tools = await build_agent(agent_id, user_id)

    if mcp_tools:
        await mcp_tools.connect()

    try:
        result = await agent.arun(prompt)
        print(result.content if hasattr(result, "content") else result)
    finally:
        if mcp_tools:
            await mcp_tools.close()

# -------- Main --------
if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(f"Uso: python {sys.argv[0]} <agent_id> <user_id> '<prompt>'")
        sys.exit(1)

    agent_id = sys.argv[1]
    user_id = sys.argv[2]
    prompt = sys.argv[3]
    asyncio.run(run_agent(agent_id, user_id, prompt))


def get_agent_data(agent_id):
    """Busca dados do agente"""
    resp = requests.get(f"{BASE_URL}/agents/{agent_id}")
    resp.raise_for_status()
    return resp.json()

def get_tool_data(tool_id):
    """Busca dados de uma ferramenta"""
    resp = requests.get(f"{BASE_URL}/tools/{tool_id}")
    resp.raise_for_status()
    return resp.json()

def get_kb_data(kb_id):
    """Busca dados de uma base de conhecimento"""
    resp = requests.get(f"{BASE_URL}/kb/{kb_id}")
    resp.raise_for_status()
    return resp.json()

def get_mcp_data(mcp_id):
    """Busca dados de um MCP"""
    resp = requests.get(f"{BASE_URL}/mcp/{mcp_id}")
    resp.raise_for_status()
    return resp.json()

def build_agent_from_api(agent_id):
    """Monta um agente Agno com base nos dados da API"""
    # 1. Pega dados do agente
    agent_info = get_agent_data(agent_id)

    # 2. Monta Tools
    tools = []
    for tool_id in agent_info.get("tools", []):
        tool_data = get_tool_data(tool_id)
        tools.append(tool_data)

    # 3. Monta MCPs
    mcps = []
    for mcp_id in agent_info.get("mcp", []):
        mcp_data = get_mcp_data(mcp_id)
        mcps.append(mcp_data)

    # 4. Monta Knowledge Base
    knowledge_bases = []
    for kb_id in agent_info.get("knowledgeBase", []):
        kb_data = get_kb_data(kb_id)
        knowledge_bases.append(kb_data)

    # 5. Constrói o agente no Agno
    agno_agent = Agent(
        name=agent_info.get("name"),
        description=agent_info.get("description"),
        personality_instructions=agent_info.get("personalityInstructions"),
        tools=tools,
        mcp=mcps,
        knowledge_base=knowledge_bases,
        color=agent_info.get("color", "#ffffff"),
        rules_file=agent_info.get("rulesFile"),
        memory_config=agent_info.get("memoryConfig"),
        model=agent_info.get("model", {}).get("full", "gpt-3.5-turbo"),
    )

    return agno_agent

if __name__ == "__main__":
    agent_id = "6890d580048ba0eddc74dc5e"  # exemplo

    # Monta o agente
    agente = build_agent_from_api(agent_id)

    # Prompt do usuário
    user_prompt = input("Digite seu prompt: ")

    # Roda o agente
    resposta = agente.run(user_prompt)
    print("\n--- Resposta do agente ---\n")
    print(resposta)
