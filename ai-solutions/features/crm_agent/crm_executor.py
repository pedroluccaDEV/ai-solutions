# features/crm/crm_executor.py
"""
CRM Executor — chama o agente Agno com o prompt do Planner
e parseia o output estruturado em JSON válido.

Responsabilidade: executar + validar + garantir estrutura correta.
"""

import json
import re
import traceback
from datetime import datetime
from typing import Dict, Any, Optional

from features.crm_agent.crm_builder import build_crm_agent, get_model_info


# =====================================================
# SCHEMA DE VALIDAÇÃO DO OUTPUT
# =====================================================

VALID_INTENTS   = {"buy_interest", "duvida", "reclamacao", "abandono", "neutro"}
VALID_PRIORITIES = {"high", "medium", "low"}
VALID_STAGES    = {"novo", "engajado", "qualificado", "perdido"}
VALID_TONES     = {"friendly", "professional", "urgent", "empathetic"}
VALID_ACTIONS   = {"send_message", "update_status", "notify_team"}


def _extract_json_from_text(text: str) -> Optional[str]:
    """
    Tenta extrair JSON válido mesmo que o LLM tenha incluído
    texto ou markdown ao redor.
    """
    # Tenta extrair bloco de código ```json ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
    if match:
        return match.group(1).strip()

    # Tenta encontrar o primeiro { ... } de nível raiz
    match = re.search(r"\{[\s\S]+\}", text)
    if match:
        return match.group(0).strip()

    return None


def _validate_and_fix_output(parsed: Dict) -> Dict:
    """
    Valida o JSON retornado pelo LLM e corrige campos faltantes
    com valores seguros. Nunca lança exceção — sempre retorna algo útil.
    """

    # --- analysis ---
    analysis = parsed.get("analysis", {})
    if not isinstance(analysis, dict):
        analysis = {}

    analysis.setdefault("intent", "neutro")
    analysis.setdefault("confidence", 0.5)
    analysis.setdefault("priority", "medium")
    analysis.setdefault("stage", "novo")
    analysis.setdefault("reasoning", "Sem raciocínio fornecido.")

    # Garante valores válidos
    if analysis["intent"] not in VALID_INTENTS:
        analysis["intent"] = "neutro"
    if analysis["priority"] not in VALID_PRIORITIES:
        analysis["priority"] = "medium"
    if analysis["stage"] not in VALID_STAGES:
        analysis["stage"] = "novo"

    parsed["analysis"] = analysis

    # --- response ---
    response = parsed.get("response", {})
    if not isinstance(response, dict):
        response = {}

    response.setdefault("message", "Olá! Como posso te ajudar?")
    response.setdefault("tone", "friendly")

    if response["tone"] not in VALID_TONES:
        response["tone"] = "friendly"

    parsed["response"] = response

    # --- actions ---
    actions = parsed.get("actions", [])
    if not isinstance(actions, list) or len(actions) == 0:
        # Garante ao menos send_message
        actions = [
            {
                "type": "send_message",
                "payload": {"message": response["message"]}
            }
        ]

    # Valida cada ação
    clean_actions = []
    for action in actions:
        if not isinstance(action, dict):
            continue
        action_type = action.get("type", "")
        if action_type not in VALID_ACTIONS:
            continue
        action.setdefault("payload", {})
        clean_actions.append(action)

    if not clean_actions:
        clean_actions = [
            {
                "type": "send_message",
                "payload": {"message": response["message"]}
            }
        ]

    parsed["actions"] = clean_actions

    # --- metadata ---
    model_info = get_model_info()
    metadata = parsed.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}

    metadata.setdefault("model", model_info["model_id"])
    metadata.setdefault("processing_note", "")
    parsed["metadata"] = metadata

    return parsed


# =====================================================
# EXECUTOR PRINCIPAL
# =====================================================

async def run_crm_executor(
    executor_prompt: str,
    planner_meta: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Recebe o prompt enriquecido do Planner, chama o agente Agno
    e retorna o output CRM estruturado.

    Args:
        executor_prompt: prompt construído pelo Planner
        planner_meta:    metadados do planejamento (para logging)

    Returns:
        CRMOutput estruturado:
        {
          "analysis": {...},
          "response": {...},
          "actions": [...],
          "metadata": {...},
          "_meta": {...}   ← interno, não enviar ao cliente
        }
    """

    start_time = datetime.utcnow()
    raw_output = ""
    parse_success = False

    try:
        print(f"\n[CRM EXECUTOR] Iniciando execução...")
        print(f"[CRM EXECUTOR] Lead ID: {planner_meta.get('lead_id')}")
        print(f"[CRM EXECUTOR] Intent hint: {planner_meta.get('hint_intent')}")

        # Instancia o agente (fixo por enquanto)
        agent = build_crm_agent()

        # Chama o LLM — sem streaming pois precisamos do JSON completo
        response = await agent.arun(executor_prompt)

        # Extrai o conteúdo de texto
        if hasattr(response, "content"):
            raw_output = response.content or ""
        else:
            raw_output = str(response)

        print(f"[CRM EXECUTOR] Output bruto recebido: {len(raw_output)} chars")

        # =================== PARSE JSON ===================
        json_str = _extract_json_from_text(raw_output)

        if not json_str:
            raise ValueError("Nenhum JSON encontrado no output do LLM")

        parsed = json.loads(json_str)
        parse_success = True

        print(f"[CRM EXECUTOR] JSON parseado com sucesso")

    except json.JSONDecodeError as e:
        print(f"[CRM EXECUTOR] Erro ao parsear JSON: {e}")
        print(f"[CRM EXECUTOR] Output bruto: {raw_output[:300]}")
        # Cria estrutura mínima para não quebrar o fluxo
        parsed = {}

    except Exception as e:
        print(f"[CRM EXECUTOR] Erro na execução: {e}")
        traceback.print_exc()
        parsed = {}

    # =================== VALIDAÇÃO E CORREÇÃO ===================
    output = _validate_and_fix_output(parsed)

    # =================== METADADOS INTERNOS ===================
    end_time = datetime.utcnow()
    processing_ms = int((end_time - start_time).total_seconds() * 1000)

    output["metadata"]["processing_time_ms"] = processing_ms
    output["metadata"]["executed_at"] = end_time.isoformat()

    # Campo interno para debug (remover antes de enviar ao cliente se necessário)
    output["_meta"] = {
        "parse_success":    parse_success,
        "raw_output_len":   len(raw_output),
        "planner_meta":     planner_meta,
        "lead_id":          planner_meta.get("lead_id"),
    }

    print(f"[CRM EXECUTOR] Concluído em {processing_ms}ms")
    print(f"[CRM EXECUTOR] Intent: {output['analysis']['intent']} | Priority: {output['analysis']['priority']}")
    print(f"[CRM EXECUTOR] Ações: {[a['type'] for a in output['actions']]}")

    return output