# schemas/webhook_saphien_schema.py
"""
Schemas para webhook do Saphien Widget.
Padrão similar ao Telegram, mas adaptado para widget web.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


# ======================================================
# SCHEMAS PARA REQUISIÇÕES DO WIDGET
# ======================================================

class SaphienUserInfoSchema(BaseModel):
    """Informações do usuário/visitante do site."""
    url: Optional[str] = None
    user_agent: Optional[str] = Field(None, alias="userAgent")
    ip: Optional[str] = None
    timestamp: Optional[str] = None
    
    class Config:
        populate_by_name = True


class SaphienMessageRequestSchema(BaseModel):
    """Payload da mensagem enviada pelo widget."""
    message: str
    session_id: str
    sender: str = "user"
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SaphienSessionRequestSchema(BaseModel):
    """Payload para registro de sessão."""
    session_id: str
    url: Optional[str] = None
    userAgent: Optional[str] = None
    ip: Optional[str] = None
    timestamp: Optional[str] = None


# ======================================================
# SCHEMAS PARA RESPOSTAS DO SERVIDOR
# ======================================================

class SaphienMessageResponseSchema(BaseModel):
    """Resposta padrão para mensagens."""
    status: str = "success"  # success, error
    reply: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class SaphienErrorResponseSchema(BaseModel):
    """Resposta de erro."""
    status: str = "error"
    reply: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class SaphienSessionResponseSchema(BaseModel):
    """Resposta para registro de sessão."""
    status: str
    session_id: Optional[str] = None  # ← tornar opcional
    is_new: Optional[bool] = None      # ← tornar opcional
    created_at: Optional[str] = None
    instance_name: Optional[str] = None
    message: Optional[str] = None      # ← adicionar para mensagens de erro


class SaphienMessageHistorySchema(BaseModel):
    """Mensagem individual no histórico."""
    text: str
    sender: str  # user, bot
    timestamp: Optional[str] = None


class SaphienMessagesResponseSchema(BaseModel):
    """Resposta para histórico de mensagens."""
    status: str
    session_id: str
    messages: List[SaphienMessageHistorySchema] = Field(default_factory=list)
    count: int = 0


class SaphienWidgetScriptResponseSchema(BaseModel):
    """Resposta para geração do script do widget."""
    success: bool
    script: str
    widget_token: str
    embed_code: str


# ======================================================
# SCHEMAS PARA STORAGE (MongoDB)
# ======================================================

class SaphienSessionSchema(BaseModel):
    """Schema para sessão no MongoDB (formato chat_sessions)."""
    id: Optional[str] = Field(None, alias="_id")
    widget_token: str
    session_id: str  # ID gerado pelo frontend
    type: str = "saphien"
    user_info: Optional[SaphienUserInfoSchema] = None
    active_agent: Optional[Dict[str, Any]] = None
    agents: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")
    last_activity: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class SaphienMessageSchema(BaseModel):
    """Schema para mensagem no MongoDB (formato chat_messages)."""
    id: Optional[str] = Field(None, alias="_id")
    session_id: str
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    role: str  # user, assistant
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    type: str = "saphien"
    created_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


# ======================================================
# SCHEMAS PARA WEBHOOK (payloads externos)
# ======================================================

class SaphienWebhookPayload(BaseModel):
    """
    Payload esperado pelo webhook do widget.
    Similar ao TelegramWebhookPayload, mas adaptado.
    """
    message: str
    session_id: str
    sender: str = "user"
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SaphienSessionPayload(BaseModel):
    """Payload para registro de sessão."""
    session_id: str  # ← ADICIONAR ESTA LINHA
    url: Optional[str] = None
    userAgent: Optional[str] = None
    ip: Optional[str] = None
    timestamp: Optional[str] = None