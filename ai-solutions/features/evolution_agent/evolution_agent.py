import os
import asyncio
from typing import Optional, Dict, Any

from features.agent.fetch_data import fetch_agent_resources
from features.evolution_agent.planner_agent import run_planner
from features.evolution_agent.executor_agent import run_executor_optimized
from agno.knowledge.knowledge import Knowledge

try:
    from features.tests.agents.agent_knowledge.chroma_client_wrapper import ChromaDbWrapper
    from agno.knowledge.knowledge import Knowledge
except ImportError:
    ChromaDbWrapper = None
    Knowledge = None
    print("⚠️ ChromaDbWrapper não disponível")


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


# ========== FUNÇÕES AUXILIARES OTIMIZADAS ==========

def setup_dynamic_tool_environment(tool_data):
    if not isinstance(tool_data, list):
        return
    for tool in tool_data:
        if not isinstance(tool, dict):
            continue
        tool_info = tool.get('data')
        if not tool_info:
            continue
        tool_config = tool_info.get('config', {})
        tool_param = tool_config.get('tool_param')
        api_key = tool_config.get('api_key')
        if tool_param and api_key:
            os.environ[tool_param] = api_key


def init_knowledge_base_optimized(kb_meta: dict):
    """
    Inicializa knowledge base se disponível.
    Retorna Knowledge object ou None.
    """
    if not kb_meta or not ChromaDbWrapper:
        return None
    try:
        collection_name = kb_meta.get("vector_collection_name")
        if not collection_name:
            return None
        vector_db = ChromaDbWrapper(
            collection_name=collection_name,
            enable_hybrid_search=True
        )
        if not vector_db.has_data():
            return None
        return Knowledge(vector_db=vector_db, embedding_model=vector_db.embedder)
    except Exception:
        return None


def build_evolution_prompt(agent_data: dict, prompt: str) -> str:
    parts = []
    role_definition = agent_data.get("roleDefinition")
    if role_definition:
        parts.append(f"**Papel do Agente**: {role_definition}")
    goal = agent_data.get("goal")
    if goal:
        parts.append(f"**Objetivo Principal**: {goal}")
    agent_rules = agent_data.get("agentRules")
    if agent_rules:
        parts.append(f"**Regras de Comportamento**: {agent_rules}")
    extra_context = "\n\n".join(parts) + "\n\n" if parts else ""
    return f"{extra_context}**Consulta do Usuário**:\n{prompt}"


# ========== PLANNER OTIMIZADO ==========

async def run_planner_optimized(user_prompt, kb_meta, tools_meta, mcp_meta, model_id="deepseek-chat"):
    try:
        print(f"[PLANNER] Iniciando análise - Model: {model_id}")
        planner_result = await asyncio.to_thread(
            run_planner,
            user_prompt,
            kb_meta,
            tools_meta,
            mcp_meta,
            model_id
        )
        if not isinstance(planner_result, dict):
            planner_result = {
                "planner_response": str(planner_result),
                "original_keywords": "",
                "proper_nouns": [],
                "timing": {},
                "tokens_used": 0
            }
        planner_metadata = {
            "tokens_used": planner_result.get("tokens_used", 0),
            "timing": planner_result.get("timing", {}),
            "model_used": model_id
        }
        return {
            "planner_response": planner_result.get("planner_response", ""),
            "original_keywords": planner_result.get("original_keywords", ""),
            "proper_nouns": planner_result.get("proper_nouns", []),
            "planner_metadata": planner_metadata
        }
    except Exception as e:
        print(f"❌ [PLANNER ERRO] {e}")
        return {
            "planner_response": f"Erro na análise. Entrada: {user_prompt[:200]}",
            "original_keywords": user_prompt[:50],
            "proper_nouns": [],
            "planner_metadata": {"tokens_used": 0, "timing": {}, "model_used": model_id},
            "error": str(e)
        }


# ========== EVOLUTION AGENT SIMPLIFICADO ==========

class EvolutionAgent:

    @staticmethod
    async def run_evolution_flow(agent_id, prompt, user_id: Optional[str] = None):
        try:
            print(f"\n{'='*60}")
            print(f"EVOLUTION AGENT - PROCESSANDO {agent_id}")
            print(f"{'='*60}\n")

            # ✅ User ID simples — fallback se não fornecido
            final_user_id = user_id or "anonymous_user"
            print(f"✅ User identificado: {final_user_id}")

            # Carrega recursos do agente
            resources = fetch_agent_resources(agent_id, final_user_id)
            agent_data = resources.get("agent", {})
            tool_data = resources.get("tools", [])
            mcp_data = resources.get("mcps", [])
            knowledge_data = resources.get("knowledge_bases", [])

            setup_dynamic_tool_environment(tool_data)
            refined_prompt = build_evolution_prompt(agent_data, prompt)

            # Planner
            print("[EVOLUTION] Executando Planner...")
            planner_result = await run_planner_optimized(
                refined_prompt,
                knowledge_data,
                tool_data,
                mcp_data
            )

            # Executor
            print("[EVOLUTION] Executando Executor...")
            executor_result = await run_executor_optimized(
                agent_id=agent_id,
                prompt=planner_result["planner_response"],
                user_id=final_user_id,
                original_keywords=planner_result["original_keywords"],
                proper_nouns=planner_result["proper_nouns"]
            )

            return {
                "success": True,
                "planner_analysis": planner_result,
                "executor_response": executor_result.get("response", ""),
                "metadata": {
                    **executor_result.get("metadata", {}),
                    "flow": "evolution_optimized"
                }
            }

        except Exception as e:
            print(f"❌ [EVOLUTION ERRO] {e}")
            return {"success": False, "error": str(e)}


async def execute_evolution_agent(agent_id, prompt, user_id=None):
    return await EvolutionAgent.run_evolution_flow(agent_id, prompt, user_id)


async def execute_playground_agent(agent_id, prompt, user_id=None):
    evolution_result = await execute_evolution_agent(agent_id, prompt, user_id)
    if evolution_result["success"]:
        pr = evolution_result["planner_analysis"]
        return {
            "planner_response": pr["planner_response"],
            "original_keywords": pr["original_keywords"],
            "proper_nouns": pr["proper_nouns"],
            "executor_result": evolution_result["executor_response"],
            "used_resources": evolution_result["metadata"]
        }
    return {"error": evolution_result["error"], "planner_response": "", "executor_result": ""}