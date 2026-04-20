from fastapi import APIRouter, HTTPException, status
from typing import List

from schemas.crm_schema import (
    LeadCreateSchema,
    LeadUpdateSchema,
    LeadOutSchema,
    AgentRunSchema,
    AgentRunOutSchema,
)
from services.crm_service import LeadService, AgentService

router = APIRouter(tags=["CRM"])


# ─────────────────────────────────────────────
# LEADS — CRUD
# ─────────────────────────────────────────────

@router.post("/leads", status_code=status.HTTP_201_CREATED, response_model=LeadOutSchema)
def create_lead(data: LeadCreateSchema):
    return LeadService.create_lead(data)


@router.get("/leads", response_model=List[LeadOutSchema])
def list_leads():
    return LeadService.list_leads()


@router.get("/leads/{lead_id}", response_model=LeadOutSchema)
def get_lead(lead_id: str):
    lead = LeadService.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    return lead


@router.patch("/leads/{lead_id}", response_model=LeadOutSchema)
def update_lead(lead_id: str, data: LeadUpdateSchema):
    lead = LeadService.update_lead(lead_id, data)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    return lead


@router.delete("/leads/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(lead_id: str):
    deleted = LeadService.delete_lead(lead_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Lead não encontrado")


# ─────────────────────────────────────────────
# AGENT
# ─────────────────────────────────────────────

@router.post("/agent/run", response_model=AgentRunOutSchema)
async def run_agent(payload: AgentRunSchema):
    """
    Recebe um lead + histórico + contexto,
    aciona o agente e retorna análise, resposta e ações.
    """
    try:
        return await AgentService.run(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no agente: {str(e)}")