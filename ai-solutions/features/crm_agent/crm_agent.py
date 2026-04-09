# features/crm/crm_agent.py
"""
CRM Agent — orquestrador principal.

Fluxo:
    Input estruturado
        ↓
    Planner  (lógica pura, sem LLM)
        ↓
    Executor (chama o agente Agno)
        ↓
    Output estruturado (analysis + response + actions)

Uso:
    result = await run_crm_agent(crm_input)
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional

from features.crm_agent.crm_planner import run_crm_planner
from features.crm_agent.crm_executor import run_crm_executor


# =====================================================
# TIPAGEM DO INPUT (documentação viva)
# =====================================================

"""
CRMInput esperado:
{
  "lead": {
    "id":      str,
    "name":    str,
    "message": str,
    "status":  "new" | "engaged" | "qualified" | "lost",
    "source":  str
  },
  "history": [
    {
      "sender":  "lead" | "agent",
      "content": str,
      "timestamp": str   (opcional)
    }
  ],
  "context": {
    "company": str,
    "product": str,
    "tone":    "comercial" | "tecnico" | "suporte"
  },
  "constraints": {
    "max_tokens":     int,
    "response_style": "short" | "balanced" | "detailed"
  }
}
"""


# =====================================================
# VALIDAÇÃO DO INPUT
# =====================================================

def _validate_input(crm_input: Dict[str, Any]) -> None:
    """Valida campos obrigatórios e lança erro descritivo."""
    if "lead" not in crm_input:
        raise ValueError("Campo 'lead' obrigatório no input CRM")

    lead = crm_input["lead"]
    if not lead.get("message"):
        raise ValueError("Campo 'lead.message' obrigatório")
    if not lead.get("id"):
        raise ValueError("Campo 'lead.id' obrigatório")


def _apply_defaults(crm_input: Dict[str, Any]) -> Dict[str, Any]:
    """Preenche campos opcionais com valores padrão."""
    crm_input.setdefault("history", [])
    crm_input.setdefault("context", {})
    crm_input.setdefault("constraints", {})

    ctx = crm_input["context"]
    ctx.setdefault("company", "Nossa Empresa")
    ctx.setdefault("product", "Nosso Produto")
    ctx.setdefault("tone", "comercial")

    cst = crm_input["constraints"]
    cst.setdefault("max_tokens", 500)
    cst.setdefault("response_style", "balanced")

    lead = crm_input["lead"]
    lead.setdefault("name", "Lead")
    lead.setdefault("status", "new")
    lead.setdefault("source", "unknown")

    return crm_input


# =====================================================
# ORQUESTRADOR PRINCIPAL
# =====================================================

async def run_crm_agent(crm_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ponto de entrada principal do agente CRM.

    Args:
        crm_input: dicionário estruturado com lead, history, context, constraints

    Returns:
        CRMOutput estruturado com analysis, response, actions, metadata
    """

    started_at = datetime.utcnow()

    print(f"\n{'='*60}")
    print(f"[CRM AGENT] Iniciando processamento")
    print(f"[CRM AGENT] Lead ID: {crm_input.get('lead', {}).get('id')}")
    print(f"[CRM AGENT] Timestamp: {started_at.isoformat()}")
    print(f"{'='*60}")

    # 1. Validação
    _validate_input(crm_input)

    # 2. Defaults
    crm_input = _apply_defaults(crm_input)

    lead        = crm_input["lead"]
    history     = crm_input["history"]
    context     = crm_input["context"]
    constraints = crm_input["constraints"]

    # 3. PLANNER — lógica pura, sem LLM
    print(f"\n[CRM AGENT] ▶ Etapa 1/2: Planner")
    planner_result = run_crm_planner(
        lead=lead,
        history=history,
        context=context,
        constraints=constraints,
    )

    executor_prompt = planner_result["executor_prompt"]
    planner_meta    = planner_result["planner_meta"]

    # 4. EXECUTOR — chama o LLM via Agno
    print(f"\n[CRM AGENT] ▶ Etapa 2/2: Executor")
    crm_output = await run_crm_executor(
        executor_prompt=executor_prompt,
        planner_meta=planner_meta,
    )

    # 5. Enriquece metadata final
    finished_at = datetime.utcnow()
    total_ms = int((finished_at - started_at).total_seconds() * 1000)

    crm_output["metadata"]["total_time_ms"] = total_ms
    crm_output["metadata"]["lead_id"] = lead["id"]

    print(f"\n{'='*60}")
    print(f"[CRM AGENT] ✅ Processamento completo em {total_ms}ms")
    print(f"  Intent:   {crm_output['analysis']['intent']}")
    print(f"  Priority: {crm_output['analysis']['priority']}")
    print(f"  Stage:    {crm_output['analysis']['stage']}")
    print(f"  Actions:  {[a['type'] for a in crm_output['actions']]}")
    print(f"{'='*60}\n")

    return crm_output