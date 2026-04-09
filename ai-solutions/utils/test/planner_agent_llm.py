import os
import sys
import requests
from dotenv import load_dotenv
from textwrap import dedent

# Carrega variáveis de ambiente
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    print("[ERRO] Variável DEEPSEEK_API_KEY não encontrada.")
    sys.exit(1)

SYSTEM_DESCRIPTION = dedent("""\
PlannerAgent é um planejador técnico que recebe a solicitação do usuário,
analisa as bases de conhecimento, ferramentas e MCPs disponíveis, e gera um
prompt final estruturado para um Executor.
""")

PLANNER_INSTRUCTIONS = dedent("""\
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
   - No prompt final, deixe claro que a busca é **por palavras-chave**, de forma genérica e independente do contexto.
5) Quando usar pesquisa externa ou URLs:
   - Oriente o Executor a citar **a fonte da informação** usando a URL.
6) Produzir o *prompt final* que será enviado para o Executor, contendo:
   - Instrução clara de que o Executor deve buscar pelas palavras-chave geradas **apenas se a fonte for a KB**.
   - Palavras-chave listadas de forma direta.
   - Orientações sobre como formatar a resposta:  
     - Estrutura clara, com subtítulos quando necessário.  
     - Textos ricos em informação, explicações detalhadas e exemplos quando aplicáveis.  
     - Cite URLs **quando usar informação externa**.

Exemplo de frase no prompt final (quando for usar a KB):  
"Busque na base de conhecimento pela query: `Cores da Marca`"

Evite frases redundantes como "com base nas informações da base de conhecimento".

Sempre que fizer sentido, use Markdown para formatar o resultado.
""")

def call_llm(prompt: str, model_id: str = "deepseek-chat") -> str:
    """
    Chama a LLM DeepSeek via API e retorna a resposta.
    """
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": f"{model_id}",
        "messages": [
            {"role": "system", "content": f"{SYSTEM_DESCRIPTION} + \n + {PLANNER_INSTRUCTIONS}"},
            {"role": "user", "content": f"{prompt}"}
        ],
        "stream": False
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[ERRO] Falha ao chamar LLM: {e}")
        return "[ERRO] Não foi possível obter resposta da LLM."

def run_planner(
    user_prompt: str,
    kb_meta: list = None,
    tools_meta: list = None,
    mcp_meta: list = None,
    model_id: str = "deepseek-chat"
) -> str:
    """
    Executa o planejador com base no prompt do usuário, metadados das KBs, Tools e MCPs.
    """
    kb_meta = kb_meta or []
    tools_meta = tools_meta or []
    mcp_meta = mcp_meta or []

    kb_summary = "\n".join(f"- {kb.get('id', 'sem_id')}: {kb.get('description', str(kb))}" for kb in kb_meta)
    tools_summary = "\n".join(f"- {tool.get('name', 'sem_nome')}: {tool.get('description', '')}" for tool in tools_meta)
    mcp_summary = "\n".join(f"- {mcp.get('id', 'sem_id')}: {mcp.get('description', '')}" for mcp in mcp_meta)

    full_prompt = dedent(f"""
        Solicitação do usuário:
        {user_prompt}

        MCPs disponíveis:
        {mcp_summary}

        Ferramentas disponíveis:
        {tools_summary}

        Bases de conhecimento carregadas:
        {kb_summary}
    """)

    return call_llm(full_prompt, model_id)

# Execução manual pelo terminal
if __name__ == "__main__":
    try:
        prompt = input("Digite a solicitação do usuário: ")
        kb_data = []
        tools_data = []
        mcp_data = []
        result = run_planner(prompt, kb_data, tools_data, mcp_data)
        print("\n=== Prompt final para Executor ===\n")
        print(result)
    except KeyboardInterrupt:
        print("\n[INFO] Execução interrompida pelo usuário.")
