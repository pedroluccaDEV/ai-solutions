from typing import Optional, List

from dao.mongo.agent_dao import AgentDAO
from schemas.agent_schema import (
    AgentCreateSchema,
    AgentUpdateSchema
)


class AgentService:
    def __init__(self):
        self.dao = AgentDAO()

    # ---------------------------
    # Create
    # ---------------------------

    def create(self, data: AgentCreateSchema, uid: str) -> dict:
        return self.dao.create(data, uid)

    # ---------------------------
    # Read
    # ---------------------------

    def get_by_id(self, agent_id: str, uid: str) -> Optional[dict]:
        return self.dao.get_by_id(agent_id, uid)

    def list_by_user(self, uid: str) -> List[dict]:
        return self.dao.list_by_user(uid)

    def list_public(self) -> List[dict]:
        return self.dao.list_public()

    # ---------------------------
    # Update
    # ---------------------------

    def update(self, agent_id: str, data: AgentUpdateSchema, uid: str) -> Optional[dict]:
        return self.dao.update(agent_id, data, uid)

    # ---------------------------
    # Delete (soft delete)
    # ---------------------------

    def delete(self, agent_id: str, uid: str) -> bool:
        return self.dao.delete(agent_id, uid)