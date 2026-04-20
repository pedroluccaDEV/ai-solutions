# features/channels/webhook_saphien/agent/saphien_planner.py
"""
Planner para Saphien Agent.
Usa DeepSeek fixo, igual ao planner do chat e do Telegram.
"""

import os
import re
import time
import requests
from textwrap import dedent
from typing import Dict, Any, List, Optional


# =====================================================
# CONFIGURAÇÃO
# =====================================================
PLANNER_MODEL = "deepseek-chat"
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")


def _extrair_keywords(texto: str) -> str:
    """Extrai keywords relevantes do texto."""
    STOPWORDS = {
        "de","do","da","os","as","um","uma","para","em","no","na",
        "sobre","com","que","por","dos","das","nos","nas","fale",
        "me","diga","conte","explique","mostre","qual","quais","como",
        "oi","olá","ola","bom","boa","dia","tarde","noite","tudo",
        "bem","obrigado","obrigada","por","favor","sim","nao","não",
    }
    limpo = re.sub(r"[^\w\s]", " ", texto.lower())
    palavras = limpo.split()
    return " ".join([p for p in palavras if p not in STOPWORDS and len(p) > 2])


def _detectar_nomes_proprios(texto: str) -> List[str]:
    """Detecta nomes próprios no texto."""
    return re.findall(r"\b[A-ZÀ-ÿ][a-zà-ÿ]+\b", texto)


def _formatar_historico(history: List[Dict]) -> str:
    """Formata histórico para o prompt."""
    if not history:
        return "(Sem histórico anterior)"
    
    formatted = []
    for msg in history[-5:]:  # Últimas 5 mensagens
        role = msg.get("role", "")
        content = msg.get("content", "")[:100]
        sender = "Usuário" if role == "user" else "Assistente"
        formatted.append(f"{sender}: {content}")
    
    return "\n".join(formatted)


def run_saphien_planner(
    user_prompt: str,
    agent_data: Dict[str, Any],
    kb_meta: List[Dict] = None,
    tools_meta: List[Dict] = None,
    mcp_meta: List[Dict] = None,
    conversation_history: List[Dict] = None,
) -> Dict[str, Any]:
    """
    Planner para Saphien Agent.
    Usa DeepSeek fixo, igual ao run_planner do chat e do Telegram.
    """
    
    kb_meta = kb_meta or []
    tools_meta = tools_meta or []
    mcp_meta = mcp_meta or []
    conversation_history = conversation_history or []

    t0 = time.time()
    keywords = _extrair_keywords(user_prompt)
    nomes = _detectar_nomes_proprios(user_prompt)

    historico_texto = _formatar_historico(conversation_history)

    system_prompt = dedent("""
        Você é um Planner Agent especializado em análise de tarefas para Saphien Widget.

        **CONTEXTO DO AGENTE:**
        Nome: {agent_name}
        Descrição: {agent_desc}
        Objetivo: {agent_goal}

        **SEU PAPEL:**
        - Analisar a solicitação do usuário
        - Identificar qual recurso usar (Tool, MCP, Knowledge Base)
        - Criar instruções claras para o Executor Agent
        - Considerar o histórico da conversa

        **FORMATO DA RESPOSTA:**
        Sua resposta deve seguir este formato estruturado:

        ---
        ## ANÁLISE
        [Breve análise da solicitação]

        ## RECURSO
        [Qual recurso usar: tool, mcp, kb ou conhecimento próprio]

        ## INSTRUÇÕES AO EXECUTOR
        [Instruções claras para o executor]

        ## KEYWORDS
        [Keywords otimizadas para busca]
        ---

        Seja preciso, técnico e objetivo.
    """).format(
        agent_name=agent_data.get("name", "Agente"),
        agent_desc=agent_data.get("description", ""),
        agent_goal=agent_data.get("goal", "")
    )

    user_message = dedent(f"""
        **SOLICITAÇÃO DO USUÁRIO:**
        {user_prompt}

        **HISTÓRICO DA CONVERSA:**
        {historico_texto}

        **RECURSOS DISPONÍVEIS:**
        - Knowledge Bases: {len(kb_meta)}
        - Tools: {len(tools_meta)}
        - MCPs: {len(mcp_meta)}

        **TAREFA:**
        Analise a solicitação e crie instruções para o executor.
    """)

    if not DEEPSEEK_API_KEY:
        raise ValueError("DEEPSEEK_API_KEY não configurada")

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
        "max_tokens": 1500,
        "temperature": 0.2
    }

    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=60)

        if response.status_code != 200:
            error_detail = response.text[:200] if response.text else "Sem detalhes"
            raise RuntimeError(f"Erro HTTP {response.status_code}: {error_detail}")

        data = response.json()
        planner_response = data["choices"][0]["message"]["content"].strip()
        
        usage = data.get("usage", {})
        total_tokens = usage.get("total_tokens", 0)

        return {
            "planner_response": planner_response,
            "original_keywords": keywords,
            "proper_nouns": nomes,
            "tokens_used": total_tokens,
            "timing": {"total": round(time.time() - t0, 3)},
            "resources_analyzed": {
                "kbs": len(kb_meta),
                "tools": len(tools_meta),
                "mcps": len(mcp_meta),
                "history": len(conversation_history)
            }
        }

    except Exception as e:
        fallback_plan = dedent(f"""
## ANÁLISE
Usuário solicitou: "{user_prompt}"

## RECURSO
Conhecimento próprio do agente

## INSTRUÇÕES AO EXECUTOR
- Responda de forma direta e amigável
- Use tom conversacional (widget de chat)
- Seja conciso e objetivo
- Considere o histórico: {historico_texto[:100]}

## KEYWORDS
{keywords}
""")
        return {
            "planner_response": fallback_plan,
            "original_keywords": keywords,
            "proper_nouns": nomes,
            "tokens_used": 0,
            "error": str(e),
            "resources_analyzed": {
                "kbs": len(kb_meta),
                "tools": len(tools_meta),
                "mcps": len(mcp_meta),
                "history": len(conversation_history)
            }
        }