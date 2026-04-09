import os
import asyncio
import aiohttp
from dotenv import load_dotenv
import traceback
import jwt
import urllib.parse
from typing import Optional, List, Dict, Any

# Importa módulos do planejador e executor (ajustados para os arquivos corretos)
from utils.agent.planner_agent import run_planner
from utils.agent.executor_agent import run_executor

# ==========================================================
# 1️⃣ CONFIGURAÇÃO INICIAL E VARIÁVEIS DE AMBIENTE
# ==========================================================
load_dotenv()

os.environ["CHROMA_TELEMETRY_ENABLED"] = "false"

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Chaves para uso das APIs
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
DEEPSSEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

if not OPENROUTER_API_KEY:
    raise EnvironmentError("[ERRO] OPENROUTER_API_KEY deve estar definido no ambiente.")

# ==========================================================
# 2️⃣ FUNÇÕES AUXILIARES DE REQUISIÇÃO
# ==========================================================
async def fetch_json(session, url, user_jwt):
    headers = {"Authorization": f"Bearer {user_jwt}"}
    async with session.get(url, headers=headers) as response:
        response.raise_for_status()
        return await response.json()

async def resolve_tool_name_to_id(session, tool_name: str, user_jwt: str) -> Optional[str]:
    """
    Resolve um nome de ferramenta para seu ID correspondente
    buscando na lista de ferramentas do usuário
    """
    try:
        # Busca todas as ferramentas disponíveis para o usuário
        url = f"{API_BASE_URL}/v1/tool-config"
        tool_configs = await fetch_json(session, url, user_jwt)
        
        print(f"[DEBUG] Buscando ID para ferramenta: '{tool_name}'")
        print(f"[DEBUG] Tool configs disponíveis: {len(tool_configs) if tool_configs else 0}")
        
        if not tool_configs:
            return None
            
        # Busca por nome exato ou parcial
        for config_id in tool_configs:
            try:
                # Busca os detalhes da ferramenta
                tool_url = f"{API_BASE_URL}/v1/tools/{config_id}"
                tool_data = await fetch_json(session, tool_url, user_jwt)
                
                # Verifica se o nome corresponde
                tool_info_name = tool_data.get('name', '').strip().lower()
                search_name = tool_name.strip().lower()
                
                print(f"[DEBUG] Comparando: '{search_name}' com '{tool_info_name}'")
                
                # Verifica correspondências
                if (tool_info_name == search_name or 
                    search_name in tool_info_name or 
                    tool_info_name in search_name):
                    
                    print(f"[SUCCESS] Ferramenta '{tool_name}' resolvida para ID: {config_id}")
                    return config_id
                    
            except Exception as e:
                print(f"[WARNING] Erro ao verificar tool {config_id}: {e}")
                continue
        
        print(f"[ERROR] Não foi possível resolver ferramenta '{tool_name}' para um ID válido")
        return None
        
    except Exception as e:
        print(f"[ERROR] Erro ao resolver nome da ferramenta '{tool_name}': {e}")
        return None

def extract_tool_ids_from_data(tools_data):
    """Extrai IDs das ferramentas independente da estrutura dos dados"""
    if not tools_data:
        return []
    
    tool_ids = []
    for tool in tools_data:
        if isinstance(tool, dict):
            # Tenta diferentes campos que podem conter o ID
            tool_id = tool.get('id') or tool.get('tool_id') or tool.get('_id')
            if tool_id:
                tool_ids.append(str(tool_id))
            else:
                # DEBUG: Se não encontrou ID, mostra as chaves disponíveis
                print(f"[WARNING] Ferramenta sem ID identificável: {tool}")
                print(f"[WARNING] Chaves disponíveis: {list(tool.keys())}")
        elif isinstance(tool, (str, int)):
            # Se já é um ID direto
            tool_ids.append(str(tool))
        else:
            print(f"[WARNING] Tipo de ferramenta não reconhecido: {type(tool)} - {tool}")
    
    return tool_ids

def validate_tool_id(tool_id):
    """Valida se o tool_id é realmente um ID e não um nome"""
    if not tool_id:
        return None
    
    tool_id_str = str(tool_id).strip()
    
    # Se contém espaços, provavelmente é um nome, não um ID
    if ' ' in tool_id_str:
        print(f"[WARNING] Possível nome detectado: '{tool_id_str}' (precisa ser resolvido)")
        return None
    
    # Se é muito longo ou contém caracteres suspeitos, pode ser um nome
    if len(tool_id_str) > 50 or any(word in tool_id_str.lower() for word in ['tool', 'agent', 'service']):
        print(f"[WARNING] ID suspeito (pode ser nome): '{tool_id_str}'")
        # Ainda tenta usar, mas com aviso
    
    # IDs típicos são hexadecimais ou numéricos
    if len(tool_id_str) >= 8 and (tool_id_str.isdigit() or all(c in '0123456789abcdef' for c in tool_id_str.lower())):
        return tool_id_str
    
    print(f"[WARNING] Formato de ID não reconhecido: '{tool_id_str}'")
    return None

async def fetch_tools(session, tools_data, user_jwt):
    """Versão corrigida que resolve nomes para IDs quando necessário"""
    if not tools_data:
        return []
    
    print(f"[DEBUG] Dados de ferramentas recebidos: {tools_data}")
    
    # Extrai IDs dos dados
    tool_ids = extract_tool_ids_from_data(tools_data)
    print(f"[DEBUG] IDs de ferramentas extraídos: {tool_ids}")
    
    # Separa IDs válidos dos que precisam ser resolvidos
    valid_tool_ids = []
    names_to_resolve = []
    
    for tid in tool_ids:
        validated_id = validate_tool_id(tid)
        if validated_id:
            valid_tool_ids.append(validated_id)
        else:
            # Se não é um ID válido, pode ser um nome que precisa ser resolvido
            names_to_resolve.append(str(tid))
    
    print(f"[DEBUG] IDs válidos encontrados: {valid_tool_ids}")
    print(f"[DEBUG] Nomes para resolver: {names_to_resolve}")
    
    # Resolve nomes para IDs
    for name in names_to_resolve:
        resolved_id = await resolve_tool_name_to_id(session, name, user_jwt)
        if resolved_id:
            valid_tool_ids.append(resolved_id)
        else:
            print(f"[ERROR] Não foi possível resolver '{name}' para um ID válido")
    
    print(f"[DEBUG] IDs finais após resolução: {valid_tool_ids}")
    
    if not valid_tool_ids:
        print("[WARNING] Nenhum ID de ferramenta válido encontrado após resolução")
        return []
    
    # Remove duplicatas mantendo ordem
    unique_tool_ids = list(dict.fromkeys(valid_tool_ids))
    print(f"[DEBUG] IDs únicos para buscar: {unique_tool_ids}")
    
    # Faz as requisições
    tasks = []
    for tid in unique_tool_ids:
        # URL encode para segurança
        encoded_id = urllib.parse.quote(str(tid), safe='')
        url = f"{API_BASE_URL}/v1/tools/{encoded_id}"
        print(f"[DEBUG] Fazendo requisição para: {url}")
        tasks.append(fetch_json(session, url, user_jwt))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    final_result = []
    
    for tid, res in zip(unique_tool_ids, results):
        if isinstance(res, Exception):
            print(f"[ERROR] Falha ao carregar ferramenta {tid}: {res}")
            final_result.append({"id": tid, "data": None, "error": str(res)})
        else:
            print(f"[SUCCESS] Ferramenta {tid} carregada com sucesso")
            final_result.append({"id": tid, "data": res})
    
    return final_result

def extract_ids_from_data(data_list, id_fields=['id', '_id', 'mcp_id', 'kb_id']):
    """Função genérica para extrair IDs de diferentes tipos de dados"""
    if not data_list:
        return []
    
    ids = []
    for item in data_list:
        if isinstance(item, dict):
            for field in id_fields:
                if field in item and item[field]:
                    ids.append(str(item[field]))
                    break
        elif isinstance(item, (str, int)):
            ids.append(str(item))
    
    return ids

async def fetch_mcps(session, mcps_data, user_jwt):
    """Versão corrigida para MCPs"""
    if not mcps_data:
        return []
    
    mcp_ids = extract_ids_from_data(mcps_data, ['id', '_id', 'mcp_id'])
    print(f"[DEBUG] IDs de MCP extraídos: {mcp_ids}")
    
    if not mcp_ids:
        return []
    
    tasks = []
    for mid in mcp_ids:
        encoded_id = urllib.parse.quote(str(mid), safe='')
        url = f"{API_BASE_URL}/v1/mcp/{encoded_id}"
        tasks.append(fetch_json(session, url, user_jwt))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    final_result = []
    
    for mid, res in zip(mcp_ids, results):
        if isinstance(res, Exception):
            print(f"[ERROR] Falha ao carregar MCP {mid}: {res}")
            final_result.append({"id": mid, "data": None, "error": str(res)})
        else:
            print(f"[SUCCESS] MCP {mid} carregado com sucesso")
            final_result.append({"id": mid, "data": res})
    
    return final_result

async def fetch_knowledge_bases(session, kb_data, user_jwt):
    """Versão corrigida para Knowledge Bases"""
    if not kb_data:
        return []
    
    kb_ids = extract_ids_from_data(kb_data, ['id', '_id', 'kb_id', 'knowledge_id'])
    print(f"[DEBUG] IDs de Knowledge Base extraídos: {kb_ids}")
    
    if not kb_ids:
        return []
    
    tasks = []
    for kid in kb_ids:
        encoded_id = urllib.parse.quote(str(kid), safe='')
        url = f"{API_BASE_URL}/v1/kb/{encoded_id}"
        tasks.append(fetch_json(session, url, user_jwt))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    final_result = []
    
    for kid, res in zip(kb_ids, results):
        if isinstance(res, Exception):
            print(f"[ERROR] Falha ao carregar Knowledge Base {kid}: {res}")
            final_result.append({"id": kid, "data": None, "error": str(res)})
        else:
            print(f"[SUCCESS] Knowledge Base {kid} carregado com sucesso")
            final_result.append({"id": kid, "data": res})
    
    return final_result

# ==========================================================
# 3️⃣ OBTENÇÃO DE DADOS COMPLETOS DO AGENTE (COM DEBUG MELHORADO)
# ==========================================================
async def get_agent_data(agent_id: str, user_jwt: str):
    async with aiohttp.ClientSession() as session:
        agent_data = await fetch_json(session, f"{API_BASE_URL}/v1/agents/{agent_id}", user_jwt)
        
        # DEBUG: Mostra a estrutura dos dados do agente
        print(f"\n[DEBUG] Dados do agente carregados:")
        print(f"  Agent ID: {agent_id}")
        print(f"  Tools raw: {agent_data.get('tools', [])}")
        print(f"  MCP raw: {agent_data.get('mcp', [])}")
        print(f"  Knowledge Base raw: {agent_data.get('knowledgeBase', [])}")
        
        # Carrega os recursos do agente
        tool_data = await fetch_tools(session, agent_data.get("tools", []), user_jwt)
        mcp_data = await fetch_mcps(session, agent_data.get("mcp", []), user_jwt)
        knowledge_data = await fetch_knowledge_bases(session, agent_data.get("knowledgeBase", []), user_jwt)
        
        # Log final dos recursos carregados
        print(f"\n[DEBUG] Recursos carregados com sucesso:")
        print(f"  Tools: {len(tool_data)} carregadas")
        print(f"  MCPs: {len(mcp_data)} carregados")
        print(f"  Knowledge Bases: {len(knowledge_data)} carregadas")
        
        return agent_data, tool_data, mcp_data, knowledge_data

# ==========================================================
# 4️⃣ RESTO DO CÓDIGO PERMANECE IGUAL MAS COM MELHORIAS DE LOG
# ==========================================================
def setup_dynamic_tool_environment(tool_data):
    """Configura variáveis de ambiente para as ferramentas"""
    if not isinstance(tool_data, list):
        return
    
    print(f"[DEBUG] Configurando ambiente para {len(tool_data)} ferramentas...")
    
    for i, tool in enumerate(tool_data):
        if not isinstance(tool, dict):
            continue
        tool_info = tool.get('data')
        if not tool_info or not isinstance(tool_info, dict):
            continue
        tool_config = tool_info.get('config', {})
        tool_param = tool_config.get('tool_param')
        api_key = tool_config.get('api_key')
        
        if tool_param and api_key:
            os.environ[tool_param] = api_key
            print(f"[DEBUG] Variável de ambiente configurada: {tool_param}")
        else:
            print(f"[WARNING] Ferramenta {i} não tem configuração de API key válida")

def extract_user_id_from_jwt(user_jwt: str) -> str:
    """
    Extrai o user_id do JWT sem verificar a assinatura.
    Em produção, você deveria verificar a assinatura do JWT.
    """
    try:
        # Decodifica o JWT sem verificar a assinatura (apenas para extrair dados)
        # Em produção, use verify=True com a chave correta
        decoded = jwt.decode(user_jwt, options={"verify_signature": False})
        return decoded.get("user_id") or decoded.get("sub") or decoded.get("uid")
    except Exception as e:
        raise ValueError(f"Erro ao decodificar JWT: {e}")

def print_loaded_data(agent_data, tool_data, mcp_data, knowledge_data):
    """Imprime dados carregados para debug"""
    print("\n=== DADOS DO AGENTE ===")
    for k, v in agent_data.items():
        if k not in ['tools', 'mcp', 'knowledgeBase']:  # Já logados separadamente
            print(f"{k}: {v}")
    
    print(f"\n=== FERRAMENTAS CARREGADAS ({len(tool_data)}) ===")
    for i, tool in enumerate(tool_data):
        tool_name = tool.get('data', {}).get('name', 'N/A') if tool.get('data') else 'ERROR'
        print(f"  {i+1}. {tool.get('id')} -> {tool_name}")
    
    print(f"\n=== MCPs CARREGADOS ({len(mcp_data)}) ===")
    for i, mcp in enumerate(mcp_data):
        mcp_name = mcp.get('data', {}).get('name', 'N/A') if mcp.get('data') else 'ERROR'
        print(f"  {i+1}. {mcp.get('id')} -> {mcp_name}")
    
    print(f"\n=== KNOWLEDGE BASES CARREGADAS ({len(knowledge_data)}) ===")
    for i, kb in enumerate(knowledge_data):
        kb_name = kb.get('data', {}).get('name', 'N/A') if kb.get('data') else 'ERROR'
        print(f"  {i+1}. {kb.get('id')} -> {kb_name}")

class PlaygroundAgent:
    @staticmethod
    async def run_agent_flow(
        agent_data, 
        tool_data, 
        mcp_data, 
        knowledge_data, 
        prompt: str, 
        user_jwt: str, 
        user_id: str
    ):
        print("\n[DEBUG] Iniciando fluxo do agente...")
        
        # Configura ambiente das ferramentas
        setup_dynamic_tool_environment(tool_data)
        
        # Log dos recursos disponíveis
        print_loaded_data(agent_data, tool_data, mcp_data, knowledge_data)

        refined_prompt = f"Agente carregado.\n\n{prompt}"

        print("\n[DEBUG] Executando planner...")
        planner_response = run_planner(
            user_prompt=refined_prompt,
            kb_meta=[k["data"] for k in knowledge_data if k.get("data")],
            tools_meta=[t["data"] for t in tool_data if t.get("data")],
            mcp_meta=[m["data"] for m in mcp_data if m.get("data")],
            model_id="deepseek-chat"
        )

        # Prepara dados do agente com ferramentas para o executor
        agent_data_with_tools = agent_data.copy()
        tools_for_executor = [
            t["data"] for t in tool_data if isinstance(t, dict) and t.get("data")
        ]
        agent_data_with_tools["tools"] = tools_for_executor
        
        print(f"[DEBUG] Ferramentas passadas para o executor: {len(tools_for_executor)}")

        # Determina collection da knowledge base
        knowledge_collection_name = None
        if knowledge_data and knowledge_data[0].get("data"):
            knowledge_collection_name = knowledge_data[0]["data"].get("vector_collection_name")
            print(f"[DEBUG] Knowledge collection: {knowledge_collection_name}")

        # Determina servidor MCP
        mcp_server_id = mcp_data[0]["id"] if mcp_data else None
        if mcp_server_id:
            print(f"[DEBUG] MCP server ID: {mcp_server_id}")

        print("\n[DEBUG] Executando executor...")
        executor_result = await run_executor(
            agent_data=agent_data_with_tools,
            prompt=planner_response,
            user_token=user_jwt,
            user_id=user_id,
            knowledge_collection_name=knowledge_collection_name,
            api_base_url=API_BASE_URL,
            mcp_server_id=mcp_server_id
        )

        return {
            "planner_response": planner_response,
            "executor_result": executor_result
        }

async def execute_playground_agent(
    agent_id: str, 
    prompt: str, 
    user_jwt: str,
    user_id: Optional[str] = None
):
    """
    Função principal para ser chamada via API.
    """
    try:
        print(f"\n[INFO] Executando playground agent para agente: {agent_id}")
        
        # Se user_id não foi fornecido, extrair do JWT
        if not user_id:
            user_id = extract_user_id_from_jwt(user_jwt)
            if not user_id:
                raise ValueError("Não foi possível extrair user_id do JWT")
        
        print(f"[INFO] User ID: {user_id}")
        
        # Buscar dados do agente
        agent_data, tool_data, mcp_data, knowledge_data = await get_agent_data(agent_id, user_jwt)
        
        # Executar o fluxo do agente
        result = await PlaygroundAgent.run_agent_flow(
            agent_data, 
            tool_data, 
            mcp_data, 
            knowledge_data, 
            prompt, 
            user_jwt, 
            user_id
        )
        
        print(f"[SUCCESS] Execução do agente concluída com sucesso")
        return result
        
    except Exception as e:
        print(f"[ERRO] Falha na execução do playground agent: {e}")
        traceback.print_exc()
        raise

async def main():
    import sys
    
    if len(sys.argv) < 4:
        print("Uso: python playground_agent.py <agent_id> <prompt> <user_jwt> [user_id]")
        sys.exit(1)

    agent_id = sys.argv[1]
    prompt = sys.argv[2]
    user_jwt = sys.argv[3]
    user_id = sys.argv[4] if len(sys.argv) > 4 else None

    result = await execute_playground_agent(agent_id, prompt, user_jwt, user_id)

    print("\n=== Resposta do Planner ===")
    print(result["planner_response"])
    print("\n=== Resposta do Executor ===")
    print(result["executor_result"])

if __name__ == "__main__":
    asyncio.run(main())