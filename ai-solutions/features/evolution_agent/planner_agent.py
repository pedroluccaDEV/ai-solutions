# features/agent/planner_agent.py

import os
import sys
import re
import time
import requests
from textwrap import dedent
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List

# ============================================================
# ✅ Configuração inicial
# ============================================================
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"


def get_env_var(key: str) -> str:
    value = os.getenv(key)
    if not value:
        print(f"[ERRO] Variável de ambiente '{key}' não encontrada.")
        sys.exit(1)
    return value


# ============================================================
# 🔧 Utilitários
# ============================================================
def extrair_keywords_raw(texto: str) -> str:
    STOPWORDS = {
        "de", "do", "da", "os", "as", "um", "uma", "para", "em", "no", "na",
        "sobre", "com", "que", "por", "dos", "das", "nos", "nas", "fale",
        "me", "diga", "conte", "explique", "mostre", "qual", "quais", "como"
    }
    limpo = re.sub(r"[^\w\s]", " ", texto.lower())
    palavras = limpo.split()
    keywords = [p for p in palavras if p not in STOPWORDS and len(p) > 2]
    return " ".join(keywords)


def detectar_nomes_proprios(texto: str) -> list:
    return re.findall(r"\b[A-ZÀÁÂÃÄÅÇÈÉÊËÌÍÎÏÑÒÓÔÕÖÙÚÛÜ][a-zàáâãäåçèéêëìíîïñòóôõöùúûü]+\b", texto)


def format_tools_for_prompt(tools_meta: list) -> str:
    """Formata ferramentas de forma clara para o Planner"""
    if not tools_meta:
        return "(Nenhuma ferramenta disponível)"
    
    formatted = []
    for tool in tools_meta:
        # Suporta tanto estrutura antiga quanto nova
        if isinstance(tool, dict):
            # Nova estrutura: dados diretos
            if 'name' in tool:
                name = tool.get('name', 'sem_nome')
                description = tool.get('description', 'sem descrição')
                tool_class = tool.get('class_name', '')
            # Estrutura antiga: aninhada em 'data'
            else:
                tool_data = tool.get('data', {})
                name = tool_data.get('name', 'sem_nome')
                description = tool_data.get('description', 'sem descrição')
                tool_class = tool_data.get('tool_class', '')
            
            formatted.append(f"• {name} ({tool_class}): {description}")
    
    return "\n".join(formatted) if formatted else "(Nenhuma ferramenta disponível)"


def format_mcps_for_prompt(mcp_meta: list) -> str:
    """
    🔥 ATUALIZADO: Formata MCPs usando a nova estrutura de prepare_mcp_connections()
    
    Estrutura esperada:
    [{
        "server_name": str,
        "server_description": str,
        "connection": str,
        "transport": str,
        "active": bool,
        "connected": bool,
        "category": str
    }]
    """
    if not mcp_meta:
        return "(Nenhum servidor MCP disponível)"
    
    formatted = []
    for mcp in mcp_meta:
        # Verifica se é a nova estrutura preparada
        if isinstance(mcp, dict) and 'server_name' in mcp:
            name = mcp.get('server_name', 'sem_nome')
            description = mcp.get('server_description', 'sem descrição')
            transport = mcp.get('transport', 'unknown')
            category = mcp.get('category', '')
            active = mcp.get('active', False)
            connected = mcp.get('connected', False)
            
            # Adiciona status de conexão
            status = "✅ Conectado" if (active and connected) else "⚠️ Não disponível"
            
            formatted.append(
                f"• {name} ({transport}) - {category}\n"
                f"  Status: {status}\n"
                f"  Descrição: {description}"
            )
        
        # Suporte à estrutura antiga (fallback)
        elif isinstance(mcp, dict) and 'name' in mcp:
            name = mcp.get('name', 'sem_nome')
            description = mcp.get('description', 'sem descrição')
            formatted.append(f"• {name}: {description}")
    
    return "\n".join(formatted) if formatted else "(Nenhum servidor MCP disponível)"


def format_kbs_for_prompt(kb_meta: list) -> str:
    """Formata Knowledge Bases de forma clara para o Planner"""
    if not kb_meta:
        return "(Nenhuma base de conhecimento disponível)"
    
    formatted = []
    for i, kb in enumerate(kb_meta, 1):
        name = kb.get('name', 'sem_nome')
        description = kb.get('description', 'sem descrição')
        collection = kb.get('vector_collection_name', '')
        formatted.append(f"• KB{i} - {name} ({collection}): {description}")
    
    return "\n".join(formatted)


def format_files_for_prompt(files_meta: Optional[Dict[str, Any]] = None) -> str:
    """
    🔥 NOVA FUNÇÃO: Formata informações dos arquivos para o Planner
    """
    if not files_meta or not files_meta.get('files'):
        return "(Nenhum arquivo anexado)"
    
    files_list = files_meta.get('files', [])
    formatted = []
    
    for file_info in files_list:
        name = file_info.get('name', 'sem_nome')
        file_type = file_info.get('type', 'desconhecido')
        size = file_info.get('size', 0)
        mime_type = file_info.get('mime_type', 'desconhecido')
        
        # Converter bytes para KB/MB
        if size > 1024 * 1024:
            size_str = f"{size / (1024 * 1024):.1f} MB"
        elif size > 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size} bytes"
        
        formatted.append(f"• {name} ({file_type}, {size_str}, {mime_type})")
    
    return "\n".join(formatted) if formatted else "(Nenhum arquivo anexado)"


# ============================================================
# 🧠 Função principal ATUALIZADA
# ============================================================
def run_planner(
    user_prompt: str, 
    kb_meta: list, 
    tools_meta: list = None, 
    mcp_meta: list = None,
    model_id: str = "deepseek-chat",
    files_meta: Optional[Dict[str, Any]] = None  # 🔥 NOVO PARÂMETRO ADICIONADO
) -> dict:
    """
    Analisa a solicitação do usuário e cria instruções para o Executor.
    NÃO gera resultados fictícios, apenas analisa e delega.
    
    Args:
        user_prompt: Pergunta/solicitação do usuário
        kb_meta: Lista de knowledge bases disponíveis
        tools_meta: Lista de tools disponíveis (estrutura do DAO)
        mcp_meta: Lista de MCPs preparados (estrutura de prepare_mcp_connections)
        model_id: Modelo DeepSeek a usar
        files_meta: Metadados dos arquivos anexados (nova funcionalidade)
    """
    etapas = {}
    t0 = time.time()

    if tools_meta is None:
        tools_meta = []
    if mcp_meta is None:
        mcp_meta = []
    if files_meta is None:
        files_meta = {}

    # ------------------------------------------------------------
    # ETAPA 1 — Pré-processamento local
    # ------------------------------------------------------------
    t1 = time.time()
    keywords_originais = extrair_keywords_raw(user_prompt)
    nomes_proprios = detectar_nomes_proprios(user_prompt)
    etapas["pré_processamento"] = round(time.time() - t1, 3)

    print(f"\n[PLANNER] Keywords: {keywords_originais}")
    print(f"[PLANNER] Nomes próprios: {nomes_proprios}")
    print(f"[PLANNER] Recursos disponíveis:")
    print(f"  - Knowledge Bases: {len(kb_meta)}")
    print(f"  - Tools: {len(tools_meta)}")
    print(f"  - MCPs: {len(mcp_meta)}")
    print(f"  - Arquivos: {len(files_meta.get('files', []))}")  # 🔥 NOVO LOG

    # ------------------------------------------------------------
    # ETAPA 2 — Construção do prompt ATUALIZADA
    # ------------------------------------------------------------
    t2 = time.time()
    
    kb_summary = format_kbs_for_prompt(kb_meta)
    tools_summary = format_tools_for_prompt(tools_meta)
    mcp_summary = format_mcps_for_prompt(mcp_meta)
    files_summary = format_files_for_prompt(files_meta)  # 🔥 NOVA SEÇÃO

    system_prompt = dedent("""\
        Você é um Planner Agent especializado em análise de tarefas e delegação.
        
        **SEU PAPEL:**
        - Analisar a solicitação do usuário
        - Identificar qual recurso usar (Tool, MCP, Knowledge Base ou Arquivos)
        - Criar instruções claras e específicas para o Executor Agent
        
        **SOBRE OS RECURSOS:**
        
        1. **Knowledge Bases (KB)**: Use para buscar informações em documentos internos/privados
           - Melhor para: consultas sobre documentos próprios, políticas, informações históricas
           
        2. **Tools**: Ferramentas específicas como busca web, análise de dados, etc
           - Melhor para: pesquisas web, cálculos, análises específicas
           
        3. **MCPs (Model Context Protocol)**: Servidores de integração com serviços externos
           - Melhor para: integrações com Gmail, calendário, CRM, etc
           - Status de conexão é mostrado - só recomende MCPs conectados (✅)
           
        4. **Arquivos Anexados**: Documentos, imagens, áudios enviados pelo usuário
           - Melhor para: análise de documentos específicos, processamento de arquivos
           - Considere o tipo e tamanho dos arquivos ao planejar a execução
        
        **IMPORTANTE:**
        - NUNCA invente ou fabrique resultados
        - NUNCA crie dados fictícios como URLs, títulos ou snippets
        - Seu trabalho é APENAS analisar e instruir o Executor
        - O Executor é quem executará as ferramentas e buscará os dados reais
        - Se um MCP não estiver conectado (⚠️), NÃO o recomende
        - Considere os arquivos anexados como fonte de informação quando relevante
        
        **FORMATO DA RESPOSTA:**
        Sua resposta deve seguir este formato estruturado:
        
        ---
        ## 🎯 ANÁLISE DA TAREFA
        [Descreva brevemente o que o usuário está solicitando, incluindo menção aos arquivos se aplicável]
        
        ## 🔧 RECURSO IDENTIFICADO
        [Especifique qual recurso deve ser usado: Tool específica, MCP, Knowledge Base ou processamento de arquivos]
        
        ## 📋 INSTRUÇÕES PARA O EXECUTOR
        [Instruções claras e específicas sobre:
        - Qual ferramenta/recurso usar exatamente
        - Como processar os arquivos anexados (se houver)
        - Quais parâmetros passar
        - Como formatar a resposta final
        - Quaisquer considerações especiais]
        
        ## 🔑 KEYWORDS PARA BUSCA
        [Se for usar Knowledge Base, liste as keywords otimizadas para a busca vetorial]
        ---
        
        Seja preciso, técnico e objetivo. Não invente dados.
    """)

    user_message = dedent(f"""
        **SOLICITAÇÃO DO USUÁRIO:**
        {user_prompt}

        **KEYWORDS EXTRAÍDAS:**
        {keywords_originais}

        **NOMES PRÓPRIOS DETECTADOS:**
        {', '.join(nomes_proprios) if nomes_proprios else 'Nenhum'}

        **RECURSOS DISPONÍVEIS:**
        
        ### Knowledge Bases:
        {kb_summary}
        
        ### Ferramentas (Tools):
        {tools_summary}
        
        ### Servidores MCP:
        {mcp_summary}
        
        ### Arquivos Anexados:
        {files_summary}

        **TAREFA:**
        Analise a solicitação acima e os recursos disponíveis (incluindo arquivos anexados). 
        Determine qual recurso deve ser usado e crie instruções detalhadas para o Executor Agent executar a tarefa corretamente.
        
        ATENÇÃO ESPECIAL:
        - Verifique o status de conexão dos MCPs (✅ Conectado vs ⚠️ Não disponível)
        - Só recomende MCPs que estejam conectados
        - Considere os arquivos anexados como fonte de informação quando relevante
        - Para arquivos, especifique como devem ser processados (leitura, análise, etc)
        
        Lembre-se: você está PLANEJANDO a execução, não executando. O Executor é quem vai usar as ferramentas e gerar os resultados reais.
    """)
    
    etapas["construção_prompt"] = round(time.time() - t2, 3)

    # ------------------------------------------------------------
    # ETAPA 3 — Requisição HTTP (chamada à API)
    # ------------------------------------------------------------
    t3 = time.time()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "stream": False,
        "max_tokens": 1500,  # Aumentado para incluir mais detalhes sobre MCPs
        "temperature": 0.3  # Mais determinístico para análise técnica
    }

    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=90)
        etapas["requisição_api"] = round(time.time() - t3, 3)

        if response.status_code != 200:
            raise RuntimeError(f"Erro HTTP {response.status_code}: {response.text}")

        # --------------------------------------------------------
        # ETAPA 4 — Processamento da resposta
        # --------------------------------------------------------
        t4 = time.time()
        data = response.json()
        planner_response = data["choices"][0]["message"]["content"].strip()
        usage = data.get("usage", {})
        total_tokens = usage.get("total_tokens") or (
            usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)
        )
        etapas["pós_processamento"] = round(time.time() - t4, 3)

        # --------------------------------------------------------
        # ETAPA FINAL — Total
        # --------------------------------------------------------
        total = round(time.time() - t0, 3)
        etapas["total"] = total

        print("\n[PLANNER] --- TEMPO POR ETAPA ---")
        for nome, dur in etapas.items():
            print(f"  {nome:<20}: {dur} s")

        print(f"[PLANNER] Tokens usados: {total_tokens}\n")

        return {
            "planner_response": planner_response,
            "original_keywords": keywords_originais,
            "proper_nouns": nomes_proprios,
            "timing": etapas,
            "tokens_used": total_tokens,
            "resources_analyzed": {
                "knowledge_bases": len(kb_meta),
                "tools": len(tools_meta),
                "mcps": len(mcp_meta),
                "mcps_connected": sum(1 for m in mcp_meta if m.get('connected', False)),
                "files": len(files_meta.get('files', []))  # 🔥 NOVA INFORMAÇÃO
            }
        }

    except Exception as e:
        etapas["erro_total"] = round(time.time() - t0, 3)
        print(f"[PLANNER ERRO] {e}")
        print(f"[PLANNER] Tempo até erro: {etapas['erro_total']} s")
        import traceback
        traceback.print_exc()
        
        return {
            "planner_response": f"[ERRO] Falha na chamada à API DeepSeek: {str(e)}",
            "original_keywords": keywords_originais,
            "proper_nouns": nomes_proprios,
            "timing": etapas,
            "tokens_used": 0,
            "resources_analyzed": {
                "knowledge_bases": len(kb_meta),
                "tools": len(tools_meta),
                "mcps": len(mcp_meta),
                "mcps_connected": 0,
                "files": len(files_meta.get('files', []))  # 🔥 NOVA INFORMAÇÃO
            }
        }


# ============================================================
# 🔧 Execução manual (para testes)
# ============================================================
if __name__ == "__main__":
    try:
        prompt = input("Digite a solicitação do usuário: ")
        
        # Dados de teste simulando recursos reais
        kb_data = [
            {
                "name": "Base Educação IA", 
                "description": "Base de conhecimento sobre inteligência artificial na educação",
                "vector_collection_name": "education_ai_kb"
            }
        ]
        
        tools_data = [
            {
                "name": "Exa Search",
                "description": "Ferramenta de busca web avançada com suporte a snippets e URLs",
                "class_name": "ExaSearchTool"
            }
        ]
        
        # 🔥 Nova estrutura de MCPs (da prepare_mcp_connections)
        mcp_data = [
            {
                "server_name": "Gmail",
                "server_description": "Servidor MCP para integração com Gmail",
                "connection": "https://mcp.composio.dev/...",
                "transport": "streamable-http",
                "active": True,
                "connected": True,
                "category": "Comunicação"
            },
            {
                "server_name": "Slack",
                "server_description": "Servidor MCP para integração com Slack",
                "connection": "https://mcp.example.com/...",
                "transport": "streamable-http",
                "active": True,
                "connected": False,  # Exemplo de MCP não conectado
                "category": "Comunicação"
            }
        ]
        
        # 🔥 Dados de teste para arquivos
        files_data = {
            "files": [
                {
                    "name": "relatorio.pdf",
                    "type": "document",
                    "size": 2048576,
                    "mime_type": "application/pdf"
                },
                {
                    "name": "dados.csv",
                    "type": "document", 
                    "size": 15360,
                    "mime_type": "text/csv"
                }
            ],
            "total_files": 2,
            "total_size": 2063936
        }
        
        result = run_planner(
            prompt, 
            kb_data, 
            tools_meta=tools_data, 
            mcp_meta=mcp_data,
            files_meta=files_data  # 🔥 TESTANDO COM ARQUIVOS
        )

        print("\n" + "="*70)
        print("=== RESULTADO DO PLANNER ===")
        print("="*70)
        print(f"\nKeywords Originais: {result['original_keywords']}")
        print(f"Nomes Próprios: {result['proper_nouns']}")
        print(f"\n📊 Recursos Analisados: {result['resources_analyzed']}")
        print(f"\n⏱️ TEMPOS DE EXECUÇÃO:")
        for k, v in result["timing"].items():
            print(f"  {k:<20}: {v} s")
        print(f"\n📊 Tokens Usados: {result.get('tokens_used', 'N/A')}")
        print(f"\n📋 Resposta do Planner:\n")
        print("-" * 70)
        print(result["planner_response"])
        print("-" * 70)

    except KeyboardInterrupt:
        print("\n[INFO] Execução interrompida pelo usuário.")