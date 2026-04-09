from typing import Optional, List
from pydantic import BaseModel, Field
from models.mongo.base import MongoModel

class Agent(BaseModel, MongoModel):
    __collection__ = "agents"

    id: str = Field(alias="_id")

    # Informações Básicas
    category: str
    isClone: bool = False
    name: Optional[str] = None  # antigo cloneName
    description: Optional[str] = None

    # Configuração de Comportamento
    roleDefinition: str
    goal: str
    agentRules: str
    whenToUse: str

    # Modelo de Linguagem
    model: int

    # Listas
    knowledgeBase: List[str] = []
    tools: List[str] = []
    mcps: List[str] = []

    # Configurações Avançadas
    visibility: str
    status: str = "active"

    # Personalização
    color: str

    # Campos de sistema
    uid: str
    uid_export: Optional[str] = None  # Usuário que exportou o agente (para galeria)
    org: Optional[str] = None
    type: Optional[str] = "playground"
    memoryConfig: Optional[dict] = None

    # Timestamps
    createdAt: Optional[str] = None
updatedAt: Optional[str] = None