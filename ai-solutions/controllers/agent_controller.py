from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from schemas.agent_schema import (
    AgentCreateSchema,
    AgentUpdateSchema,
    AgentOutSchema
)

from services.agent_service import AgentService
from core.auth.supabase_auth import get_current_user
from bson.errors import InvalidId

router = APIRouter(
    prefix="/agents",
    tags=["Agents"]
)


# ------------------- CREATE -------------------
@router.post(
    "/",
    response_model=AgentOutSchema,
    status_code=status.HTTP_201_CREATED
)
def create_agent(
    agent_data: AgentCreateSchema,
    current_user: dict = Depends(get_current_user),
):
    try:
        return AgentService.create_agent(
            agent_data=agent_data,
            uid=current_user["uid"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------- LIST USER AGENTS -------------------
@router.get(
    "/",
    response_model=List[AgentOutSchema]
)
def list_agents(
    current_user: dict = Depends(get_current_user),
):
    return AgentService.list_agents_for_user(current_user["uid"])


# ------------------- LIST PUBLIC -------------------
@router.get(
    "/public",
    response_model=List[AgentOutSchema]
)
def list_public_agents():
    return AgentService.list_public_agents()


# ------------------- GET BY ID -------------------
@router.get(
    "/{agent_id}",
    response_model=AgentOutSchema
)
def get_agent(
    agent_id: str,
    current_user: dict = Depends(get_current_user),
):
    try:
        agent = AgentService.get_agent_by_id(agent_id, current_user["uid"])

        if not agent:
            raise HTTPException(status_code=404, detail="Agente não encontrado")

        return agent

    except InvalidId:
        raise HTTPException(status_code=400, detail="ID inválido")


# ------------------- UPDATE (FULL) -------------------
@router.put(
    "/{agent_id}",
    response_model=AgentOutSchema
)
def update_agent(
    agent_id: str,
    agent_data: AgentCreateSchema,
    current_user: dict = Depends(get_current_user),
):
    try:
        updated = AgentService.update_agent(
            agent_id,
            agent_data,
            current_user["uid"]
        )

        if not updated:
            raise HTTPException(
                status_code=404,
                detail="Agente não encontrado ou sem permissão"
            )

        return updated

    except InvalidId:
        raise HTTPException(status_code=400, detail="ID inválido")


# ------------------- UPDATE (PARTIAL) -------------------
@router.patch(
    "/{agent_id}",
    response_model=AgentOutSchema
)
def partial_update_agent(
    agent_id: str,
    agent_data: AgentUpdateSchema,
    current_user: dict = Depends(get_current_user),
):
    try:
        update_dict = agent_data.dict(exclude_unset=True)

        if not update_dict:
            raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

        current = AgentService.get_agent_by_id(agent_id, current_user["uid"])
        if not current:
            raise HTTPException(status_code=404, detail="Agente não encontrado")

        merged = {**current, **update_dict}
        full_data = AgentCreateSchema(**merged)

        return AgentService.update_agent(
            agent_id,
            full_data,
            current_user["uid"]
        )

    except InvalidId:
        raise HTTPException(status_code=400, detail="ID inválido")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ------------------- DELETE (SOFT DELETE) -------------------
@router.delete(
    "/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_agent(
    agent_id: str,
    current_user: dict = Depends(get_current_user),
):
    try:
        deleted = AgentService.delete_agent(agent_id, current_user["uid"])

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail="Agente não encontrado ou sem permissão"
            )

    except InvalidId:
        raise HTTPException(status_code=400, detail="ID inválido")


# ------------------- REACTIVATE -------------------
@router.post(
    "/{agent_id}/reactivate",
    response_model=AgentOutSchema
)
def reactivate_agent(
    agent_id: str,
    current_user: dict = Depends(get_current_user),
):
    try:
        agent = AgentService.reactivate_agent(
            agent_id,
            current_user["uid"]
        )

        if not agent:
            raise HTTPException(status_code=404, detail="Agente não encontrado")

        return agent

    except InvalidId:
        raise HTTPException(status_code=400, detail="ID inválido")