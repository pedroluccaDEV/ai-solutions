# features/crm/crm_planner.py
"""
CRM Planner — analisa o contexto do lead e monta as instruções
que o Executor vai receber como prompt estruturado.

Papel: transformar dados brutos em contexto rico e direcionado.
NÃO chama LLM — é lógica de negócio pura e rápida.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


# =====================================================
# MAPEAMENTO DE INTENÇÕES (heurística rápida)
# Serve como dica para o LLM — não substitui a análise dele.
# =====================================================

INTENT_KEYWORDS = {
    "buy_interest": ["preço", "valor", "comprar", "contratar", "plano", "quanto custa", "assinar"],
    "doubt":        ["como", "funciona", "dúvida", "duvida", "pode", "explica", "o que é"],
    "complaint":    ["problema", "erro", "não funciona", "ruim", "péssimo", "cancelar", "reembolso"],
    "abandon":      ["não quero", "desistir", "parar", "cancelar", "tchau", "não preciso"],
}

PRIORITY_MAP = {
    "buy_interest": "high",
    "doubt":        "medium",
    "complaint":    "high",
    "abandon":      "high",
    "neutro":       "low",
}


def _detect_hint_intent(message: str) -> str:
    """Heurística leve para dar uma dica de intenção ao LLM."""
    msg_lower = message.lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(kw in msg_lower for kw in keywords):
            return intent
    return "neutro"


def _detect_hint_priority(intent: str) -> str:
    return PRIORITY_MAP.get(intent, "low")


def _summarize_history(history: List[Dict]) -> str:
    """Resume o histórico de forma compacta para o prompt."""
    if not history:
        return "Nenhuma interação anterior."

    lines = []
    for entry in history[-5:]:  # últimas 5 interações
        sender = "Lead" if entry.get("sender") == "lead" else "Agente"
        content = entry.get("content", "")
        if len(content) > 120:
            content = content[:117] + "..."
        lines.append(f"  [{sender}]: {content}")

    return "\n".join(lines)


# =====================================================
# FUNÇÃO PRINCIPAL
# =====================================================

def run_crm_planner(
    lead: Dict[str, Any],
    history: List[Dict],
    context: Dict[str, Any],
    constraints: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Recebe o input estruturado do lead e produz:
    - prompt enriquecido para o Executor
    - metadados do planejamento (para debug/log)

    Args:
        lead:        dados brutos do lead (id, name, message, status, source)
        history:     histórico de interações anteriores
        context:     contexto da empresa/produto/tom
        constraints: limites de resposta (max_tokens, response_style)

    Returns:
        {
          "executor_prompt": str,   ← vai direto para o Executor
          "planner_meta": dict      ← debug e observabilidade
        }
    """

    lead_message = lead.get("message", "")
    lead_name    = lead.get("name", "Lead")
    lead_status  = lead.get("status", "new")
    lead_source  = lead.get("source", "unknown")

    company  = context.get("company", "nossa empresa")
    product  = context.get("product", "nosso produto")
    tone     = context.get("tone", "comercial")

    response_style = constraints.get("response_style", "balanced")
    max_tokens     = constraints.get("max_tokens", 500)

    # Dicas heurísticas (o LLM pode divergir — tudo bem)
    hint_intent   = _detect_hint_intent(lead_message)
    hint_priority = _detect_hint_priority(hint_intent)

    history_summary = _summarize_history(history)

    is_first_contact = len(history) == 0

    # =====================================================
    # PROMPT ENRIQUECIDO PARA O EXECUTOR
    # =====================================================

    executor_prompt = f"""
Você está analisando uma interação de CRM. Gere o JSON de saída conforme especificado.

=== LEAD ===
Nome:    {lead_name}
Status:  {lead_status}
Origem:  {lead_source}
Mensagem recebida: "{lead_message}"
Primeiro contato: {"Sim" if is_first_contact else "Não"}

=== HISTÓRICO ===
{history_summary}

=== CONTEXTO DA EMPRESA ===
Empresa:  {company}
Produto:  {product}
Tom esperado: {tone}

=== DICAS DO PLANNER (use como referência, não como regra absoluta) ===
Intenção detectada: {hint_intent}
Prioridade sugerida: {hint_priority}

=== RESTRIÇÕES ===
Estilo de resposta: {response_style}
Máximo de tokens na resposta ao lead: {max_tokens}

=== AÇÕES DISPONÍVEIS ===
- send_message:   enviar mensagem ao lead (obrigatório sempre)
- update_status:  atualizar o status do lead no CRM
- notify_team:    notificar um membro da equipe

=== SUA TAREFA ===
1. Analise a intenção REAL do lead considerando mensagem + histórico
2. Defina prioridade e estágio corretos
3. Crie uma resposta adequada ao tom e contexto
4. Liste as ações necessárias com payloads preenchidos
5. Retorne APENAS o JSON estruturado, sem texto adicional

Lembre-se: "actions" NUNCA pode ser vazio.
""".strip()

    planner_meta = {
        "hint_intent":      hint_intent,
        "hint_priority":    hint_priority,
        "is_first_contact": is_first_contact,
        "history_count":    len(history),
        "lead_id":          lead.get("id"),
        "planned_at":       datetime.utcnow().isoformat(),
    }

    print(f"[CRM PLANNER] Lead: {lead_name} | Intent hint: {hint_intent} | Priority: {hint_priority}")

    return {
        "executor_prompt": executor_prompt,
        "planner_meta":    planner_meta,
    }