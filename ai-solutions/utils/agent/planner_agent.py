import os
import sys
import time
import requests
from textwrap import dedent
from dotenv import load_dotenv

# =====================================================
# Configuração
# =====================================================
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

if not DEEPSEEK_API_KEY:
    print("[ERRO] Variável de ambiente 'DEEPSEEK_API_KEY' não encontrada.")
    sys.exit(1)

# =====================================================
# Funções auxiliares
# =====================================================
def format_kbs_for_prompt(kb_meta):
    if not kb_meta:
        return "(Nenhuma base de conhecimento disponível)"
    return "\n".join(f"• {kb.get('id', 'sem_id')} - {kb.get('description', str(kb))}" for kb in kb_meta)

def format_tools_for_prompt(tools_meta):
    if not tools_meta:
        return "(Nenhuma ferramenta disponível)"
    return "\n".join(f"• {t.get('name', 'sem_nome')}: {t.get('description', '')}" for t in tools_meta)

def format_mcps_for_prompt(mcp_meta):
    if not mcp_meta:
        return "(Nenhum MCP disponível)"
    return "\n".join(f"• {m.get('id', 'sem_id')}: {m.get('description', '')}" for m in mcp_meta)

# =====================================================
# Função principal do planner (DeepSeek direto)
# =====================================================
def run_planner(user_prompt: str, kb_meta: list, tools_meta: list = None, mcp_meta: list = None) -> dict:
    tools_meta = tools_meta or []
    mcp_meta = mcp_meta or []

    kb_block = format_kbs_for_prompt(kb_meta)
    tools_block = format_tools_for_prompt(tools_meta)
    mcp_block = format_mcps_for_prompt(mcp_meta)

    # --------------------------------------------------
    # Prompt completo com todas as instruções detalhadas
    # --------------------------------------------------
    system_prompt = dedent("""
        Você é um planejador técnico. Recebe uma solicitação do usuário e deverá:

        1) Identificar a intenção principal da solicitação.
        2) Gerar um objetivo claro e mensurável.
        3) Decidir cuidadosamente se alguma ferramenta deve ser usada:
           - Priorize sempre a base de conhecimento local (KB) quando a informação estiver nela.
           - Use ferramentas externas (Tools ou MCPs) apenas se a tarefa exigir.
           - Evite usar ferramentas para dados que deveriam estar na KB, como manuais, políticas internas, datas ou preços.
           - Não combine mais de uma funcionalidade (Tool, MCP ou KB) na mesma tarefa, a não ser que seja explicitamente solicitado.
        4) Quando a base de conhecimento (KB) for utilizada:
           - Liste tópicos ou palavras-chave que o Executor deve buscar.
           - Sempre gerar palavras-chave diretas e genéricas, não frases completas.
           - Cada palavra-chave ou conjunto de palavras deve ser independente e capaz de gerar resultados na KB.
           - No prompt final, deixe claro que a busca é por palavras-chave, de forma genérica e independente do contexto.
        5) Quando usar pesquisa externa ou URLs:
           - Oriente o Executor a citar a fonte da informação usando a URL.
        6) Produzir o prompt final que será enviado para o Executor, contendo:
           - Instrução clara de que o Executor deve buscar pelas palavras-chave geradas apenas se a fonte for a KB.
           - Palavras-chave listadas de forma direta.
           - Orientações sobre como formatar a resposta: estrutura clara, subtítulos, explicações detalhadas e exemplos quando aplicáveis.
           - Cite URLs quando usar informação externa.

        Sempre que fizer sentido, use Markdown para formatar o resultado.
    """)

    user_message = dedent(f"""
        Solicitação do usuário:
        {user_prompt}

        Bases de conhecimento disponíveis:
        {kb_block}

        Ferramentas disponíveis:
        {tools_block}

        MCPs disponíveis:
        {mcp_block}

        Gere:
        - Análise objetiva da tarefa
        - Identificação do recurso adequado (KB, Tool ou MCP)
        - Instruções detalhadas para o Executor
        - Palavras-chave finais para busca (quando KB)
        - Exemplo de prompt final: "Busque na base de conhecimento pela query: `Cores da Marca`"
    """)

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.2,
        "max_tokens": 1200,
        "stream": False
    }

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    start = time.time()
    try:
        resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=60)
        elapsed = round(time.time() - start, 2)
        if resp.status_code != 200:
            raise RuntimeError(f"API DeepSeek retornou {resp.status_code}: {resp.text}")

        data = resp.json()
        content = data["choices"][0]["message"]["content"].strip()
        tokens = data.get("usage", {}).get("total_tokens", 0)

        print(f"[INFO] Planner executado em {elapsed}s | Tokens usados: {tokens}")
        return {
            "planner_response": content,
            "tokens_used": tokens,
            "timing": {"total_seconds": elapsed},
            "resources_analyzed": {
                "knowledge_bases": len(kb_meta),
                "tools": len(tools_meta),
                "mcps": len(mcp_meta)
            }
        }

    except Exception as e:
        elapsed = round(time.time() - start, 2)
        print(f"[ERRO] Planner falhou ({elapsed}s): {e}")
        return {
            "planner_response": f"[ERRO] Planner falhou: {e}",
            "tokens_used": 0,
            "timing": {"total_seconds": elapsed},
            "resources_analyzed": {}
        }

# =====================================================
# Teste rápido
# =====================================================
if __name__ == "__main__":
    try:
        user_prompt = input("Digite a solicitação do usuário: ")
        kb_data = [{"id": "kb1", "description": "Base de dados de musculação"}]
        tools_data = [{"name": "ExaSearch", "description": "Busca web estruturada"}]
        mcp_data = [{"id": "mcp1", "description": "Integração Gmail"}]

        result = run_planner(user_prompt, kb_data, tools_data, mcp_data)
        print("\n=== Prompt final para Executor ===\n")
        print(result["planner_response"])
    except KeyboardInterrupt:
        print("\n[INFO] Execução interrompida pelo usuário.")
