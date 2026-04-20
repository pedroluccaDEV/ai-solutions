from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal
from datetime import datetime
from bson import ObjectId
from pydantic_core import core_schema


# ---------------------------------------
# 🔧 ObjectId Adapter
# ---------------------------------------

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
        raise ValueError("Invalid ObjectId")


# ---------------------------------------
# 📦 Base (entidade pura)
# ---------------------------------------

class AgentBase(BaseModel):
    category: str
    isClone: bool = False

    name: Optional[str] = None
    description: Optional[str] = None

    roleDefinition: str
    goal: str
    agentRules: str
    whenToUse: str

    model: int

    knowledgeBase: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    mcps: List[str] = Field(default_factory=list)

    visibility: Literal["public", "private"]
    status: Literal["active", "inactive"] = "active"

    color: str

    org: Optional[str] = None


# ---------------------------------------
# ✍️ Create
# ---------------------------------------

class AgentCreateSchema(AgentBase):
    pass


# ---------------------------------------
# ✏️ Update (partial)
# ---------------------------------------

class AgentUpdateSchema(BaseModel):
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


# ---------------------------------------
# 📤 Output
# ---------------------------------------

class AgentOutSchema(AgentBase):
    id: PyObjectId = Field(alias="_id")

    uid: str

    createdAt: datetime
    updatedAt: datetime

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        },
        arbitrary_types_allowed=True
    )