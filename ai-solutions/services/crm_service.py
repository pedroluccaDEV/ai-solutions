"""
CRM Service — lógica de negócio sem banco de dados.
Usa um store in-memory (dict) como substituto temporário do DAO.
"""

import uuid
import time
from datetime import datetime, timedelta
from typing import Optional

from schemas.crm_schema import (
    LeadCreateSchema,
    LeadUpdateSchema,
    LeadOutSchema,
    AgentRunSchema,
    AgentRunOutSchema,
    AnalysisOut,
    ResponseOut,
    ActionOut,
)
from features.crm_agent.crm_agent import run_crm_agent


# ─────────────────────────────────────────────
# IN-MEMORY STORE
# Substituir por DAO + banco quando estiver pronto
# ─────────────────────────────────────────────

_leads_store: dict[str, dict] = {}


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _serialize_lead(lead: dict) -> LeadOutSchema:
    return LeadOutSchema(
        id=lead["id"],
        name=lead["name"],
        message=lead["message"],
        status=lead["status"],
        source=lead["source"],
        created_at=lead["created_at"],
        updated_at=lead["updated_at"],
    )


# ─────────────────────────────────────────────
# LEAD SERVICE
# ─────────────────────────────────────────────

class LeadService:

    @staticmethod
    def create_lead(data: LeadCreateSchema) -> LeadOutSchema:
        now = datetime.utcnow()
        lead = {
            "id": str(uuid.uuid4()),
            "name": data.name,
            "message": data.message,
            "status": data.status,
            "source": data.source,
            "created_at": now,
            "updated_at": now,
        }
        _leads_store[lead["id"]] = lead
        return _serialize_lead(lead)

    @staticmethod
    def list_leads() -> list[LeadOutSchema]:
        return [_serialize_lead(l) for l in _leads_store.values()]

    @staticmethod
    def get_lead(lead_id: str) -> Optional[LeadOutSchema]:
        lead = _leads_store.get(lead_id)
        if not lead:
            return None
        return _serialize_lead(lead)

    @staticmethod
    def update_lead(lead_id: str, data: LeadUpdateSchema) -> Optional[LeadOutSchema]:
        lead = _leads_store.get(lead_id)
        if not lead:
            return None

        updates = data.model_dump(exclude_unset=True)
        lead.update(updates)
        lead["updated_at"] = datetime.utcnow()
        _leads_store[lead_id] = lead
        return _serialize_lead(lead)

    @staticmethod
    def delete_lead(lead_id: str) -> bool:
        if lead_id not in _leads_store:
            return False
        del _leads_store[lead_id]
        return True


# ─────────────────────────────────────────────
# AGENT SERVICE
# ─────────────────────────────────────────────

class AgentService:

    @staticmethod
    async def run(payload: AgentRunSchema) -> AgentRunOutSchema:
        """
        Monta o payload no formato esperado pelo crm_agent e retorna
        o resultado tipado via AgentRunOutSchema.
        """
        agent_payload = {
            "lead": {
                "id":      payload.lead.source + "_" + str(uuid.uuid4())[:8],
                "name":    payload.lead.name,
                "message": payload.lead.message,
                "status":  payload.lead.status,
                "source":  payload.lead.source,
            },
            "history":     [m.model_dump() for m in (payload.history or [])],
            "context":     payload.context.model_dump() if payload.context else {},
            "constraints": payload.constraints.model_dump() if payload.constraints else {},
        }

        start = time.time()
        raw = await run_crm_agent(agent_payload)
        elapsed_ms = round((time.time() - start) * 1000)

        analysis_raw  = raw.get("analysis", {})
        response_raw  = raw.get("response", {})
        actions_raw   = raw.get("actions", [])
        metadata_raw  = raw.get("metadata", {})

        return AgentRunOutSchema(
            analysis=AnalysisOut(
                intent=analysis_raw.get("intent", "unknown"),
                confidence=float(analysis_raw.get("confidence", 0.0)),
                priority=analysis_raw.get("priority", "medium"),
                stage=analysis_raw.get("stage", ""),
                reasoning=analysis_raw.get("reasoning", ""),
            ),
            response=ResponseOut(
                tone=response_raw.get("tone", ""),
                message=response_raw.get("message", ""),
            ),
            actions=[
                ActionOut(type=a["type"], payload=a.get("payload", {}))
                for a in actions_raw
            ],
            metadata={
                **metadata_raw,
                "total_time_ms": elapsed_ms,
            },
        )