# features/chat/planner_agent.py
import os
import re
import time
import requests
from textwrap import dedent
from typing import Optional, Dict, Any, List


# ============================================================
# CONFIGURAÇÃO
# ============================================================
PLANNER_MODEL = "deepseek-chat"
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")


def extrair_keywords_raw(texto: str) -> str:
    """Extrai keywords relevantes do texto."""
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
    """Detecta nomes próprios no texto."""
    return re.findall(r"\b[A-ZÀÁÂÃÄÅÇÈÉÊËÌÍÎÏÑÒÓÔÕÖÙÚÛÜ][a-zàáâãäåçèéêëìíîïñòóôõöùúûü]+\b", texto)


def format_tools_for_prompt(tools_meta: list) -> str:
    """Formata ferramentas para o prompt do planner."""
    if not tools_meta:
        return "(Nenhuma ferramenta disponível)"
    
    formatted = []
    for i, tool in enumerate(tools_meta, 1):
        name = tool.get("name", "sem_nome")
        description = tool.get("description", "sem descrição")
        tool_class = tool.get("class_name", "")
        category = tool.get("category", "")
        
        # Status de configuração
        user_config = tool.get("user_config", {})
        has_config = bool(user_config)
        config_status = "✅ Configurada" if has_config else "⚠️  Sem configuração"
        
        formatted.append(f"{i}. {name} ({tool_class}) - {category}")
        formatted.append(f"   Descrição: {description}")
        formatted.append(f"   Status: {config_status}")
        formatted.append("")
    
    return "\n".join(formatted)


def format_mcps_for_prompt(mcp_meta: list) -> str:
    """Formata MCPs para o prompt do planner."""
    if not mcp_meta:
        return "(Nenhum servidor MCP disponível)"
    
    formatted = []
    for i, mcp in enumerate(mcp_meta, 1):
        server_name = mcp.get("server_name", "sem_nome")
        server_description = mcp.get("server_description", "sem descrição")
        transport = mcp.get("transport", "streamable-http")
        category = mcp.get("category", "")
        connected = mcp.get("connected", False)
        
        status = "✅ Conectado" if connected else "❌ Desconectado"
        
        formatted.append(f"{i}. {server_name} - {category}")
        formatted.append(f"   Descrição: {server_description}")
        formatted.append(f"   Status: {status} ({transport})")
        formatted.append("")
    
    return "\n".join(formatted)


def format_kbs_for_prompt(kb_meta: list) -> str:
    """Formata Knowledge Bases para o prompt do planner."""
    if not kb_meta:
        return "(Nenhuma base de conhecimento disponível)"
    
    formatted = []
    for i, kb in enumerate(kb_meta, 1):
        name = kb.get("name", "sem_nome")
        description = kb.get("description", "sem descrição")
        collection = kb.get("vector_collection_name", "")
        language = kb.get("language", "pt")
        status = kb.get("status", "active")
        
        status_emoji = "✅" if status == "active" else "⚠️"
        
        formatted.append(f"{i}. {name} {status_emoji}")
        formatted.append(f"   Descrição: {description}")
        formatted.append(f"   Idioma: {language} | Collection: {collection}")
        formatted.append("")
    
    return "\n".join(formatted)


def format_files_for_prompt(files_meta: Optional[Dict[str, Any]] = None) -> str:
    """Formata informações dos arquivos para o planner (formato novo: apenas resumo)."""
    if not files_meta or not files_meta.get('file_count') or files_meta.get('file_count') == 0:
        return "(Nenhum arquivo anexado)"
    
    formatted = []
    
    # 🔥 NOVO FORMATO: Apenas resumo dos arquivos
    formatted.append(f"📁 **RESUMO DOS ARQUIVOS:**")
    formatted.append(f"   • Total: {files_meta.get('file_count', 0)} arquivo(s)")
    formatted.append(f"   • Resumo: {files_meta.get('total_summary', 'Sem resumo')}")
    
    # Dicas de relevância
    relevance_hints = files_meta.get('relevance_hints', [])
    if relevance_hints:
        formatted.append(f"   • Tipo predominante: {', '.join(relevance_hints)}")
    
    # Tabelas
    if files_meta.get('has_tables', False):
        formatted.append(f"   • Contém tabelas: {files_meta.get('table_count', 0)} tabela(s)")
    
    # Arquivos individuais (apenas títulos/previews)
    files_list = files_meta.get('files', [])
    if files_list:
        formatted.append("")
        formatted.append("📄 **DETALHES DOS ARQUIVOS:**")
        
        for i, file_info in enumerate(files_list, 1):
            filename = file_info.get('filename', 'sem_nome')
            file_type = file_info.get('type', 'desconhecido')
            title_preview = file_info.get('title_preview', 'Sem título')
            
            # Limitar preview do título
            if len(title_preview) > 80:
                title_preview = title_preview[:77] + "..."
            
            formatted.append(f"{i}. {filename} ({file_type})")
            formatted.append(f"   • Preview: {title_preview}")
    
    # Instruções para o planner
    formatted.append("")
    formatted.append("💡 **COMO USAR ESTAS INFORMAÇÕES:**")
    formatted.append("   • Considere o tipo de arquivo (PDF, tabela, código, etc.)")
    formatted.append("   • Use os previews para entender o conteúdo geral")
    formatted.append("   • O executor terá acesso ao conteúdo completo")
    formatted.append("   • Seu papel é planejar COMO usar esses arquivos")
    
    return "\n".join(formatted)


def format_conversation_history_for_prompt(conversation_history: List[Dict]) -> str:
    """Formata o histórico da conversa para o planner."""
    if not conversation_history:
        return "(Sem histórico de conversa anterior)"
    
    formatted = ["## 📜 HISTÓRICO DA CONVERSA:"]
    
    for msg in conversation_history[-8:]:  # Últimas 8 mensagens (balance entre contexto e tokens)
        sender = msg.get("sender", "unknown")
        content = msg.get("content", "")
        
        # Formatar o papel
        if sender == "user":
            role = "👤 USUÁRIO"
        elif sender == "assistant":
            role = "🤖 ASSISTENTE"
        else:
            role = f"❓ {sender.upper()}"
        
        # Formatar conteúdo (limitar tamanho)
        if len(content) > 150:
            content_preview = content[:150] + "..."
        else:
            content_preview = content
        
        formatted.append(f"\n{role}:")
        formatted.append(f"{content_preview}")
    
    formatted.append(f"\n📊 Total de mensagens no histórico: {len(conversation_history)}")
    
    return "\n".join(formatted)


def format_agent_info_for_prompt(agent_data: Dict[str, Any]) -> str:
    """Formata informações do agente para o planner."""
    if not agent_data:
        return "(Informações do agente não disponíveis)"
    
    agent_info = []
    
    # Informações essenciais
    name = agent_data.get("name", "Agente sem nome")
    category = agent_data.get("category", "Sem categoria")
    description = agent_data.get("description", "Sem descrição")
    
    agent_info.append(f"🤖 AGENTE: {name}")
    agent_info.append(f"   Categoria: {category}")
    agent_info.append(f"   Descrição: {description}")
    
    # Informações adicionais (apenas se relevantes e concisas)
    role = agent_data.get("roleDefinition", "")
    if role:
        # Limitar tamanho do role
        if len(role) > 150:
            role = role[:147] + "..."
        agent_info.append(f"   Papel: {role}")
    
    goal = agent_data.get("goal", "")
    if goal:
        if len(goal) > 100:
            goal = goal[:97] + "..."
        agent_info.append(f"   Objetivo: {goal}")
    
    return "\n".join(agent_info)


def run_planner(
    user_prompt: str, 
    kb_meta: list, 
    tools_meta: list = None, 
    mcp_meta: list = None,
    model_id: str = "deepseek-chat",
    files_meta: Optional[Dict[str, Any]] = None,
    agent_data: Optional[Dict[str, Any]] = None,
    conversation_history: Optional[List[Dict]] = None
) -> dict:
    """
    Analisa a solicitação do usuário e cria instruções para o Executor.
    
    Args:
        user_prompt: Mensagem do usuário
        kb_meta: Lista de knowledge bases (formato normalizado)
        tools_meta: Lista de ferramentas (formato normalizado)
        mcp_meta: Lista de MCPs (formato normalizado)
        model_id: ID do modelo (ignorado, usado apenas para compatibilidade)
        files_meta: Resumo dos arquivos (formato novo: apenas metadados)
        agent_data: Dados do agente
        conversation_history: Histórico da conversa
    
    Returns:
        Dict com plano estruturado
    """
    
    # Inicializar valores padrão
    if tools_meta is None:
        tools_meta = []
    if mcp_meta is None:
        mcp_meta = []
    if files_meta is None:
        files_meta = {}
    if agent_data is None:
        agent_data = {}
    if conversation_history is None:
        conversation_history = []
    
    # ETAPA 1: Pré-processamento
    etapas = {}
    t0 = time.time()
    
    t1 = time.time()
    keywords_originais = extrair_keywords_raw(user_prompt)
    nomes_proprios = detectar_nomes_proprios(user_prompt)
    etapas["pré_processamento"] = round(time.time() - t1, 3)
    
    # ETAPA 2: Construção do prompt
    t2 = time.time()
    
    # Formatar todas as seções
    agent_info = format_agent_info_for_prompt(agent_data)
    kb_summary = format_kbs_for_prompt(kb_meta)
    tools_summary = format_tools_for_prompt(tools_meta)
    mcp_summary = format_mcps_for_prompt(mcp_meta)
    files_summary = format_files_for_prompt(files_meta)
    history_summary = format_conversation_history_for_prompt(conversation_history)
    
    system_prompt = dedent("""\
        Você é um Planner Agent especializado em análise de tarefas e delegação.
        
        **CONTEXTO IMPORTANTE:**
        Você está planejando para um agente específico. Considere:
        
        {agent_info}
        
        **SEU PAPEL:**
        - Analisar a solicitação do usuário considerando o contexto do agente e o histórico da conversa
        - Identificar qual recurso usar (Tool, MCP, Knowledge Base ou Arquivos)
        - Criar instruções claras e específicas para o Executor Agent
        - Considerar o histórico da conversa para manter continuidade
        
        **SOBRE OS RECURSOS:**
        
        1. **Knowledge Bases (KB)**: Para buscar informações em documentos internos/privados
           - Só use se houver KBs disponíveis e ativas
           
        2. **Tools**: Ferramentas específicas como busca web, análise de dados, etc
           - Só recomende tools configuradas (✅ Configurada)
           - Ignore tools não configuradas (⚠️ Sem configuração)
           
        3. **MCPs (Model Context Protocol)**: Servidores de integração com serviços externos
           - Só recomende MCPs conectados (✅ Conectado)
           - Ignore MCPs desconectados (❌ Desconectado)
           
        4. **Arquivos Anexados**: Documentos enviados pelo usuário
           - Você recebe apenas RESUMO dos arquivos (não o conteúdo completo)
           - Use o resumo para entender o tipo e tema dos arquivos
           - O executor terá acesso ao conteúdo completo
        
        **IMPORTANTE:**
        - NUNCA invente ou fabrique resultados
        - Seu trabalho é APENAS analisar e instruir o Executor
        - O Executor é quem executará as ferramentas e buscará os dados reais
        - Só recomende MCPs que estejam conectados
        - Só recomende Tools que estejam configuradas
        - Considere os arquivos anexados quando relevante
        - Considere o histórico da conversa para evitar repetições
        
        **FORMATO DA RESPOSTA:**
        Sua resposta deve seguir este formato estruturado:
        
        ---
        ## 🎯 ANÁLISE DA TAREFA
        [Breve análise considerando contexto do agente e histórico]
        
        ## 🔧 RECURSO(S) IDENTIFICADO(S)
        [Especifique qual recurso deve ser usado, justifique brevemente]
        
        ## 📋 INSTRUÇÕES PARA O EXECUTOR
        [Instruções claras sobre:
        - Qual ferramenta/recurso usar exatamente
        - Como usar os arquivos anexados (se houver)
        - Como considerar o histórico da conversa
        - Formato da resposta esperada]
        
        ## 🔑 KEYWORDS PARA BUSCA
        [Se usar KB, liste keywords otimizadas]
        ---
        
        Seja preciso, técnico e objetivo.
    """).format(agent_info=agent_info)

    user_message = dedent(f"""
        **SOLICITAÇÃO DO USUÁRIO:**
        {user_prompt}

        **KEYWORDS EXTRAÍDAS:**
        {keywords_originais}

        **HISTÓRICO DA CONVERSA:**
        {history_summary}

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
        Analise a solicitação considerando o contexto do agente e o histórico da conversa.
        Determine qual recurso deve ser usado e crie instruções detalhadas para o Executor.
        
        ATENÇÃO:
        - Só recomende recursos disponíveis (conectados/configurados)
        - Considere os arquivos anexados quando relevante
        - Mantenha continuidade com o histórico da conversa
    """)
    
    etapas["construção_prompt"] = round(time.time() - t2, 3)
    
    # ETAPA 3: Chamada à API
    t3 = time.time()
    
    if not DEEPSEEK_API_KEY:
        raise ValueError("DEEPSEEK_API_KEY não configurada no ambiente")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    
    payload = {
        "model": PLANNER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "stream": False,
        "max_tokens": 2000,
        "temperature": 0.2,
        "top_p": 0.9
    }
    
    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=90)
        etapas["requisição_api"] = round(time.time() - t3, 3)
        
        if response.status_code != 200:
            error_detail = response.text[:200] if response.text else "Sem detalhes"
            raise RuntimeError(f"Erro HTTP {response.status_code}: {error_detail}")
        
        # Processar resposta
        t4 = time.time()
        data = response.json()
        planner_response = data["choices"][0]["message"]["content"].strip()
        
        # Calcular tokens
        usage = data.get("usage", {})
        total_tokens = usage.get("total_tokens") or (
            usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)
        )
        
        etapas["pós_processamento"] = round(time.time() - t4, 3)
        
        # Tempo total
        total = round(time.time() - t0, 3)
        etapas["total"] = total
        
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
                "tools_configured": sum(1 for t in tools_meta if t.get('user_config')),
                "files_count": files_meta.get('file_count', 0),
                "conversation_history": len(conversation_history)
            },
            "agent_info": {
                "name": agent_data.get('name', 'N/A'),
                "category": agent_data.get('category', 'N/A')
            },
            "planner_model_used": PLANNER_MODEL,
            "conversation_context": {
                "has_history": len(conversation_history) > 0,
                "history_count": len(conversation_history)
            }
        }
        
    except Exception as e:
        # Fallback: plano básico
        etapas["erro_total"] = round(time.time() - t0, 3)
        
        # Contexto do histórico para fallback
        history_context = ""
        if conversation_history:
            last_messages = conversation_history[-2:]
            history_summary_fallback = "\n".join([
                f"{'Usuário' if m.get('sender') == 'user' else 'Assistente'}: {m.get('content', '')[:80]}..."
                for m in last_messages
            ])
            history_context = f"\nContexto do histórico: {history_summary_fallback}"
        
        fallback_plan = dedent(f"""
        ---
        ## 🎯 ANÁLISE DA TAREFA
        Usuário solicitou: "{user_prompt}"
        {history_context if conversation_history else "Sem histórico anterior."}
        
        ## 🔧 RECURSO(S) IDENTIFICADO(S)
        Use conhecimento interno do agente para responder.
        
        ## 📋 INSTRUÇÕES PARA O EXECUTOR
        - Analise a solicitação: "{user_prompt}"
        - Considere o contexto do histórico da conversa
        - Use as keywords: "{keywords_originais}"
        - Forneça uma resposta útil baseada no conhecimento do agente
        - Seja claro e objetivo
        
        ## 🔑 KEYWORDS PARA BUSCA
        {keywords_originais}
        ---
        """)
        
        return {
            "planner_response": fallback_plan,
            "original_keywords": keywords_originais,
            "proper_nouns": nomes_proprios,
            "timing": etapas,
            "tokens_used": 0,
            "resources_analyzed": {
                "knowledge_bases": len(kb_meta),
                "tools": len(tools_meta),
                "mcps": len(mcp_meta),
                "mcps_connected": sum(1 for m in mcp_meta if m.get('connected', False)),
                "tools_configured": sum(1 for t in tools_meta if t.get('user_config')),
                "files_count": files_meta.get('file_count', 0),
                "conversation_history": len(conversation_history)
            },
            "agent_info": {
                "name": agent_data.get('name', 'N/A'),
                "category": agent_data.get('category', 'N/A')
            },
            "planner_model_used": PLANNER_MODEL,
            "status": "fallback",
            "error": str(e),
            "conversation_context": {
                "has_history": len(conversation_history) > 0,
                "history_count": len(conversation_history)
            }
        }