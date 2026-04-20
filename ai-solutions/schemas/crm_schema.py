from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
import uuid


# ─────────────────────────────────────────────
# ENUMS / LITERALS
# ─────────────────────────────────────────────

LeadStatus = Literal["new", "engaged", "qualified", "closed", "lost"]
LeadSource = Literal["landing_page", "whatsapp", "email", "referral", "other"]
LeadIntent  = Literal["buy", "doubt", "complaint", "abandon", "unknown"]
LeadPriority = Literal["low", "medium", "high", "critical"]
ActionType  = Literal["update_status", "schedule_followup", "send_message", "escalate", "close"]


# ─────────────────────────────────────────────
# NESTED MODELS
# ─────────────────────────────────────────────

class HistoryMessage(BaseModel):
    sender: Literal["lead", "agent"]
    content: str
    timestamp: Optional[datetime] = None


class LeadContext(BaseModel):
    company: Optional[str] = None
    product: Optional[str] = None
    tone: Optional[Literal["comercial", "tecnico", "suporte"]] = "comercial"


class LeadConstraints(BaseModel):
    max_tokens: Optional[int] = 400
    response_style: Optional[Literal["short", "balanced", "detailed"]] = "balanced"


# ─────────────────────────────────────────────
# LEAD — CRUD
# ─────────────────────────────────────────────

class LeadCreateSchema(BaseModel):
    name: str
    message: str
    status: LeadStatus = "new"
    source: LeadSource = "other"


class LeadUpdateSchema(BaseModel):
    name: Optional[str] = None
    message: Optional[str] = None
    status: Optional[LeadStatus] = None
    source: Optional[LeadSource] = None


class LeadOutSchema(BaseModel):
    id: str
    name: str
    message: str
    status: LeadStatus
    source: LeadSource
    created_at: datetime
    updated_at: datetime


# ─────────────────────────────────────────────
# AGENT RUN — INPUT
# ─────────────────────────────────────────────

class AgentRunSchema(BaseModel):
    lead: LeadCreateSchema
    history: Optional[List[HistoryMessage]] = []
    context: Optional[LeadContext] = LeadContext()
    constraints: Optional[LeadConstraints] = LeadConstraints()


# ─────────────────────────────────────────────
# AGENT RUN — OUTPUT
# ─────────────────────────────────────────────

class AnalysisOut(BaseModel):
    intent: LeadIntent
    confidence: float
    priority: LeadPriority
    stage: str
    reasoning: str


class ResponseOut(BaseModel):
    tone: str
    message: str


class ActionOut(BaseModel):
    type: ActionType
    payload: dict


class AgentRunOutSchema(BaseModel):
    analysis: AnalysisOut
    response: ResponseOut
    actions: List[ActionOut]
    metadata: dict