from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from models.mongo.base import MongoModel


class Agent(BaseModel, MongoModel):
    __collection__ = "agents"

    __indexes__ = [
        [("uid", 1)],
        [("org", 1)],
        [("category", 1)],
        [("status", 1)],
    ]

    # 🔧 Config Pydantic (v2)
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={datetime: lambda v: v.isoformat()},
    )

    # ---------------------------------------
    # 🆔 ID Mongo
    # ---------------------------------------
    id: Optional[str] = Field(default=None, alias="_id")

    # ---------------------------------------
    # 📌 Informações Básicas
    # ---------------------------------------
    category: str
    isClone: bool = False
    name: Optional[str] = None
    description: Optional[str] = None

    # ---------------------------------------
    # 🧠 Comportamento
    # ---------------------------------------
    roleDefinition: str
    goal: str
    agentRules: str
    whenToUse: str

    # ---------------------------------------
    # 🤖 LLM
    # ---------------------------------------
    model: int

    # ---------------------------------------
    # 📚 Relacionamentos
    # ---------------------------------------
    knowledgeBase: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    mcps: List[str] = Field(default_factory=list)

    # ---------------------------------------
    # ⚙️ Config
    # ---------------------------------------
    visibility: str
    status: str = "active"

    # ---------------------------------------
    # 🎨 UI
    # ---------------------------------------
    color: str

    # ---------------------------------------
    # 👤 Sistema
    # ---------------------------------------
    uid: str
    uid_export: Optional[str] = None
    org: Optional[str] = None
    type: str = "playground"
    memoryConfig: Optional[Dict] = None

    # ---------------------------------------
    # ⏱️ Timestamps
    # ---------------------------------------
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)