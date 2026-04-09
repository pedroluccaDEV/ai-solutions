import os
import aiohttp
import asyncio
import jwt

API_BASE_URL = os.getenv("API_BASE_URL")

# ==========================================================
# 🔹 Requisições genéricas
# ==========================================================
async def fetch_json(session, url, user_jwt):
    headers = {"Authorization": f"Bearer {user_jwt}"}
    async with session.get(url, headers=headers) as response:
        response.raise_for_status()
        return await response.json()

async def fetch_tools(session, tool_ids, user_jwt):
    if not isinstance(tool_ids, list):
        tool_ids = list(tool_ids) if tool_ids else []
    tasks = [fetch_json(session, f"{API_BASE_URL}/v1/tools/{tid}", user_jwt) for tid in tool_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [{"id": tid, "data": res if not isinstance(res, Exception) else None} for tid, res in zip(tool_ids, results)]

async def fetch_mcps(session, mcp_ids, user_jwt):
    if not isinstance(mcp_ids, list):
        mcp_ids = list(mcp_ids) if mcp_ids else []
    tasks = [fetch_json(session, f"{API_BASE_URL}/v1/mcp/{mid}", user_jwt) for mid in mcp_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [{"id": mid, "data": res if not isinstance(res, Exception) else None} for mid, res in zip(mcp_ids, results)]

async def fetch_knowledge_bases(session, kb_ids, user_jwt):
    if not isinstance(kb_ids, list):
        kb_ids = list(kb_ids) if kb_ids else []
    tasks = [fetch_json(session, f"{API_BASE_URL}/v1/kb/{kid}", user_jwt) for kid in kb_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [{"id": kid, "data": res if not isinstance(res, Exception) else None} for kid, res in zip(kb_ids, results)]

# ==========================================================
# 🔹 Carregar agente completo (com tools, MCP e KB)
# ==========================================================
async def get_agent_data(agent_id: str, user_jwt: str):
    async with aiohttp.ClientSession() as session:
        agent_data = await fetch_json(session, f"{API_BASE_URL}/v1/agents/{agent_id}", user_jwt)
        tool_data = await fetch_tools(session, agent_data.get("tools", []), user_jwt)
        mcp_data = await fetch_mcps(session, agent_data.get("mcp", []), user_jwt)
        knowledge_data = await fetch_knowledge_bases(session, agent_data.get("knowledgeBase", []), user_jwt)

        # 🔹 Configuração dinâmica do ambiente (substituindo custom builders)
        for tool in tool_data:
            if tool_data_item := tool.get("data"):
                config = tool_data_item.get("config", {})
                if tool_param := config.get("tool_param"):
                    if api_key := config.get("api_key"):
                        os.environ[tool_param] = api_key

        return agent_data, tool_data, mcp_data, knowledge_data

# ==========================================================
# 🔹 JWT → user_id
# ==========================================================
def extract_user_id_from_jwt(user_jwt: str) -> str:
    try:
        decoded = jwt.decode(user_jwt, options={"verify_signature": False})
        return decoded.get("user_id") or decoded.get("sub") or decoded.get("uid")
    except Exception as e:
        raise ValueError(f"Erro ao decodificar JWT: {e}")

# ==========================================================
# 🔹 Impressão organizada (debug)
# ==========================================================
def print_loaded_data(agent_data, tool_data, mcp_data, knowledge_data):
    print("\n=== DADOS DO AGENTE ===")
    for k, v in agent_data.items():
        print(f"{k}: {v}")
    print("\n=== TOOLS ===")
    for t in tool_data:
        print(f"- {t['id']}: {t['data']}")
    print("\n=== MCP ===")
    for m in mcp_data:
        print(f"- {m['id']}: {m['data']}")
    print("\n=== KNOWLEDGE BASES ===")
    for kb in knowledge_data:
        print(f"- {kb['id']}: {kb['data']}")
