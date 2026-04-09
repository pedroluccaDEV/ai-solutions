import os
import asyncio
from agno.team import Team
from agno.agent import Agent
from agno.models.deepseek import DeepSeek

# === Imports utilitários do fetch_data ===
from utils.team.fetch_data import (
    get_agent_data,
    extract_user_id_from_jwt,
)

# ==========================================================
# 🔹 Montar um Agent a partir do banco
# ==========================================================
async def build_agent_from_db(agent_id, user_jwt, user_id, api_base_url):
    """Monta um Agent completo a partir dos dados do banco."""
    agent_data, tool_data, mcp_data, knowledge_data = await get_agent_data(agent_id, user_jwt)

    print(f"\n--- Carregando agente {agent_data.get('name', agent_id)} ---")

    # 1. Configuração dinâmica de ambiente
    for tool in tool_data:
        if tool_data_item := tool.get("data"):
            config = tool_data_item.get("config", {})
            if tool_param := config.get("tool_param"):
                if api_key := config.get("api_key"):
                    os.environ[tool_param] = api_key

    # 2. Modelo
    model_info = agent_data.get("model", {})
    model = DeepSeek(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        id="deepseek-chat",
        temperature=model_info.get("temperature"),
        max_tokens=model_info.get("maxTokens"),
    )
    print("Modelo:", model_info or "padrão")

    # 3. Knowledge
    knowledge = None
    if knowledge_data and knowledge_data[0].get("data"):
        collection_name = knowledge_data[0]["data"].get("vector_collection_name")
        # Placeholder para KB
        knowledge = {"collection_name": collection_name}
        print("Knowledge Base:", collection_name)
    else:
        print("Knowledge Base: nenhuma")

    # 4. MCP (opcional)
    mcp_tools = None
    if mcp_data and mcp_data[0].get("data"):
        mcp_tools = {"id": mcp_data[0]["id"], "data": mcp_data[0]["data"]}
        print("MCP:", mcp_data[0]["id"])
    else:
        print("MCP: nenhum")

    # 5. Tools (simples)
    valid_tools = [t["data"] for t in tool_data if t.get("data")]
    print("Tools:", [t.get("name", "unknown") for t in valid_tools] or "nenhuma")

    all_tools = []
    if mcp_tools:
        all_tools.append(mcp_tools)
    all_tools.extend(valid_tools)

    # 6. Criação do Agent
    agent = Agent(
        model=model,
        knowledge=knowledge,
        search_knowledge=True if knowledge else False,
        add_references=True if knowledge else False,
        tools=all_tools,
        description=agent_data.get("description", "Agente técnico"),
        instructions=agent_data.get("personalityInstructions", ""),
        markdown=True,
        name=agent_data.get("name", f"Agent-{agent_id}"),
    )

    print(f"Agente {agent.name} pronto ✅")
    return agent


# ==========================================================
# 🔹 Montar um Time completo (sem líder)
# ==========================================================
async def execute_team_flow(team_id: str, user_jwt: str, user_id: str, db):
    """Monta o Team a partir do banco e imprime todos os dados carregados."""
    team_entity = await db["teams"].find_one({"_id": team_id})
    if not team_entity:
        raise ValueError("Time não encontrado")

    print("\n==========================")
    print(f"Montando Time: {team_entity['name']}")
    print("Descrição:", team_entity.get("description", ""))
    print("Modo:", team_entity.get("mode", "collaborate"))
    print("==========================")

    # Membros
    members = []
    for aid in team_entity["memberAgentIds"]:
        agent = await build_agent_from_db(aid, user_jwt, user_id, os.getenv("API_BASE_URL"))
        members.append(agent)

    # Criação do Team sem líder
    team = Team(
        name=team_entity["name"],
        description=team_entity.get("description", ""),
        mode=team_entity.get("mode", "collaborate"),
        leader=None,
        members=members,
        shared_state={},  # no futuro: colocar KBs ou ferramentas globais
    )

    print("\n--- Time montado com sucesso ---")
    print("Nome:", team.name)
    print("Modo:", team.mode)
    print("Líder:", "nenhum")
    print("Membros:", [m.name for m in members])
    print("-------------------------------")

    return team
