import os
import asyncio
import aiohttp
from dotenv import load_dotenv
import jwt
import urllib.parse
from typing import Optional, List, Dict, Any, AsyncGenerator
import traceback

# Importa módulos do planejador e executor com streaming
from utils.agent.planner_agent import run_planner
from utils.agent.executor_agent_streaming import run_executor_streaming

# ==========================================================
# 1️⃣ CONFIGURAÇÃO INICIAL E VARIÁVEIS DE AMBIENTE
# ==========================================================
load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL")
if not API_BASE_URL:
    raise EnvironmentError("[ERRO] API_BASE_URL deve estar definido no ambiente.")

# ==========================================================
# 2️⃣ FUNÇÕES AUXILIARES DE REQUISIÇÃO (reutilizadas)
# ==========================================================
async def fetch_json(session, url, user_jwt):
    headers = {"Authorization": f"Bearer {user_jwt}"}
    async with session.get(url, headers=headers) as response:
        response.raise_for_status()
        return await response.json()

async def resolve_tool_name_to_id(session, tool_name: str, user_jwt: str) -> Optional[str]:
    try:
        url = f"{API_BASE_URL}/v1/tools/"
        tools_data = await fetch_json(session, url, user_jwt)
        if not tools_data:
            return None
        
        search_name = tool_name.strip().lower()
        
        for tool in tools_data:
            tool_info_name = tool.get('name', '').strip().lower()
            if (tool_info_name == search_name or 
                search_name in tool_info_name or 
                tool_info_name in search_name):
                return tool.get('_id')
        
        return None
    except Exception:
        return None

def extract_ids_from_data(data_list, id_fields=['id', '_id', 'mcp_id', 'kb_id']):
    ids = []
    if not data_list:
        return ids
    for item in data_list:
        if isinstance(item, dict):
            for field in id_fields:
                if field in item and item[field]:
                    ids.append(str(item[field]))
                    break
        elif isinstance(item, (str, int)):
            ids.append(str(item))
    return ids

# ==========================================================
# 3️⃣ FUNÇÕES DE FETCH PARA RECURSOS DO AGENTE (reutilizadas)
# ==========================================================
async def fetch_tools(session, tools_data, user_jwt):
    if not tools_data:
        return []
    tool_ids = extract_ids_from_data(tools_data)
    valid_tool_ids, names_to_resolve = [], []
    for tid in tool_ids:
        if len(tid) >= 8 and (tid.isdigit() or all(c in '0123456789abcdef' for c in tid.lower())):
            valid_tool_ids.append(tid)
        else:
            names_to_resolve.append(tid)
    for name in names_to_resolve:
        resolved_id = await resolve_tool_name_to_id(session, name, user_jwt)
        if resolved_id:
            valid_tool_ids.append(resolved_id)
    unique_tool_ids = list(dict.fromkeys(valid_tool_ids))
    tasks = []
    for tid in unique_tool_ids:
        encoded_id = urllib.parse.quote(str(tid), safe='')
        tasks.append(fetch_json(session, f"{API_BASE_URL}/v1/tools/{encoded_id}", user_jwt))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    final_result = []
    for tid, res in zip(unique_tool_ids, results):
        if isinstance(res, Exception):
            final_result.append({"id": tid, "data": None, "error": str(res)})
        else:
            final_result.append({"id": tid, "data": res})
    return final_result

async def fetch_mcps(session, mcps_data, user_jwt):
    mcp_ids = extract_ids_from_data(mcps_data, ['id', '_id', 'mcp_id'])
    if not mcp_ids:
        return []
    tasks = [fetch_json(session, f"{API_BASE_URL}/v1/mcp/{urllib.parse.quote(mid, safe='')}", user_jwt) for mid in mcp_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    final_result = []
    for mid, res in zip(mcp_ids, results):
        if isinstance(res, Exception):
            final_result.append({"id": mid, "data": None, "error": str(res)})
        else:
            final_result.append({"id": mid, "data": res})
    return final_result

async def fetch_knowledge_bases(session, kb_data, user_jwt):
    kb_ids = extract_ids_from_data(kb_data, ['id', '_id', 'kb_id', 'knowledge_id'])
    if not kb_ids:
        return []
    tasks = [fetch_json(session, f"{API_BASE_URL}/v1/kb/{urllib.parse.quote(kid, safe='')}", user_jwt) for kid in kb_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    final_result = []
    for kid, res in zip(kb_ids, results):
        if isinstance(res, Exception):
            final_result.append({"id": kid, "data": None, "error": str(res)})
        else:
            final_result.append({"id": kid, "data": res})
    return final_result

# ==========================================================
# 4️⃣ OBTENÇÃO DE DADOS DO AGENTE (reutilizada)
# ==========================================================
async def get_agent_data(agent_id: str, user_jwt: str):
    async with aiohttp.ClientSession() as session:
        agent_data = await fetch_json(session, f"{API_BASE_URL}/v1/agents/{agent_id}", user_jwt)
        tool_data = await fetch_tools(session, agent_data.get("tools", []), user_jwt)
        mcp_data = await fetch_mcps(session, agent_data.get("mcp", []), user_jwt)
        knowledge_data = await fetch_knowledge_bases(session, agent_data.get("knowledgeBase", []), user_jwt)
        return agent_data, tool_data, mcp_data, knowledge_data

# ==========================================================
# 5️⃣ EXECUÇÃO DO AGENTE COM STREAMING
# ==========================================================
def setup_dynamic_tool_environment(tool_data):
    if not isinstance(tool_data, list):
        return
    for tool in tool_data:
        tool_info = tool.get('data')
        if tool_info and isinstance(tool_info, dict):
            config = tool_info.get('config', {})
            param = config.get('tool_param')
            api_key = config.get('api_key')
            if param and api_key:
                os.environ[param] = api_key

def extract_user_id_from_jwt(user_jwt: str) -> str:
    try:
        decoded = jwt.decode(user_jwt, options={"verify_signature": False})
        return decoded.get("user_id") or decoded.get("sub") or decoded.get("uid")
    except Exception:
        return None

class PlaygroundAgentStreaming:
    @staticmethod
    async def run_agent_flow_streaming(
        agent_data, tool_data, mcp_data, knowledge_data, prompt: str, user_jwt: str, user_id: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Executa o fluxo do agente com streaming
        """
        setup_dynamic_tool_environment(tool_data)
        refined_prompt = f"Agente carregado.\n\n{prompt}"

        # Executar planner (ainda síncrono, mas rápido)
        planner_response = run_planner(
            user_prompt=refined_prompt,
            kb_meta=[k["data"] for k in knowledge_data if k.get("data")],
            tools_meta=[t["data"] for t in tool_data if t.get("data")],
            mcp_meta=[m["data"] for m in mcp_data if m.get("data")],
            model_id="deepseek-chat"
        )

        # Preparar dados para executor com streaming
        agent_data_with_tools = agent_data.copy()
        agent_data_with_tools["tools"] = [t["data"] for t in tool_data if t.get("data")]

        knowledge_collection_name = knowledge_data[0]["data"].get("vector_collection_name") if knowledge_data and knowledge_data[0].get("data") else None
        mcp_server_id = mcp_data[0]["id"] if mcp_data else None

        # Executar executor com streaming
        async for chunk in run_executor_streaming(
            agent_data=agent_data_with_tools,
            prompt=planner_response,
            user_token=user_jwt,
            user_id=user_id,
            knowledge_collection_name=knowledge_collection_name,
            api_base_url=API_BASE_URL,
            mcp_server_id=mcp_server_id
        ):
            yield chunk

async def execute_playground_agent_streaming(
    agent_id: str, prompt: str, user_jwt: str, user_id: Optional[str] = None
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Executa o agente playground com streaming
    """
    if not user_id:
        user_id = extract_user_id_from_jwt(user_jwt)
        if not user_id:
            raise ValueError("Não foi possível extrair user_id do JWT")
    
    agent_data, tool_data, mcp_data, knowledge_data = await get_agent_data(agent_id, user_jwt)
    
    async for chunk in PlaygroundAgentStreaming.run_agent_flow_streaming(
        agent_data, tool_data, mcp_data, knowledge_data, prompt, user_jwt, user_id
    ):
        yield chunk

# ==========================================================
# 6️⃣ FUNÇÃO MAIN PARA TESTES
# ==========================================================
async def main():
    import sys
    if len(sys.argv) < 4:
        print("Uso: python playground_agent_streaming.py <agent_id> <prompt> <user_jwt> [user_id]")
        sys.exit(1)
    
    agent_id = sys.argv[1]
    prompt = sys.argv[2]
    user_jwt = sys.argv[3]
    user_id = sys.argv[4] if len(sys.argv) > 4 else None

    print(f"Executando agente {agent_id} com streaming...")
    
    try:
        async for chunk in execute_playground_agent_streaming(agent_id, prompt, user_jwt, user_id):
            if chunk.get("complete"):
                print("\n✅ Stream completo")
                break
            elif chunk.get("error"):
                print(f"\n❌ Erro: {chunk.get('token')}")
                break
            else:
                print(chunk.get("token", ""), end="", flush=True)
    
    except Exception as e:
        print(f"\n❌ Erro durante execução: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())