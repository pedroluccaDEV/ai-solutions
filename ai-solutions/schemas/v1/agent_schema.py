from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal, Union
from datetime import datetime
from bson import ObjectId
from pydantic_core import core_schema


class PyObjectId(str):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        return core_schema.str_schema()

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str) and ObjectId.is_valid(v):
            return v
        raise ValueError("Invalid objectid")


class MemoryConfig(BaseModel):
    type: Literal["short_term", "long_term"]
    limit: int


class AgentBase(BaseModel):
    # REMOVIDO: uid não deve estar no schema base pois é definido automaticamente

    # Informações Básicas
    category: str
    isClone: bool = False
    name: Optional[str] = None
    description: Optional[str] = None

    # Configuração de Comportamento
    roleDefinition: str
    goal: str
    agentRules: str
    whenToUse: str

    # Modelo de Linguagem
    model: int

    # Listas
    knowledgeBase: Optional[List[str]] = []
    tools: Optional[List[str]] = []
    mcps: Optional[List[str]] = []

    # Configurações Avançadas
    visibility: Literal["public", "private"]
    status: Literal["active", "inactive"] = "active"

    # Personalização
    color: str

    # Compatibilidade
    org: Optional[str] = None
    type: Literal["playground", "chat"] = "playground"
    memoryConfig: Optional[dict] = None


class AgentCreateSchema(AgentBase):
    pass


class AgentUpdateSchema(BaseModel):
    # REMOVIDO: uid não deve ser atualizável via API

    category: Optional[str] = None
    isClone: Optional[bool] = None
    name: Optional[str] = None
    description: Optional[str] = None

    roleDefinition: Optional[str] = None
    goal: Optional[str] = None
    agentRules: Optional[str] = None
    whenToUse: Optional[str] = None

    model: Optional[int] = None
    knowledgeBase: Optional[List[str]] = None
    tools: Optional[List[str]] = None
    mcps: Optional[List[str]] = None

    visibility: Optional[Literal["public", "private"]] = None
    status: Optional[Literal["active", "inactive"]] = None

    color: Optional[str] = None

    org: Optional[str] = None
    type: Optional[Literal["playground", "chat"]] = None
    rulesFile: Optional[Union[dict, None]] = None
    memoryConfig: Optional[MemoryConfig] = None
    embeddingModel: Optional[dict] = None


class AgentOutSchema(AgentBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    uid: str  # <-- ADICIONADO AQUI para retorno, mas não para criação
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        },
        arbitrary_types_allowed=True
    )