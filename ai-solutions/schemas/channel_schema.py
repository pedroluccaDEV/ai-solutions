# schemas/v1/channel_schema.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class ChannelMetadataSchema(BaseModel):
    instance_name: str
    title: str
    description: Optional[str] = ""
    icon: str = "message-square"
    category: str = "communication"


class ChannelRequiredSchema(BaseModel):
    phone_number: Optional[str] = None
    instance_name: Optional[str] = None
    bot_token: Optional[str] = None
    bot_username: Optional[str] = None
    bot_token_discord: Optional[str] = None
    guild_id: Optional[str] = None
    webhook_endpoint: Optional[str] = None
    api_key_header: Optional[str] = None
    chat_id: Optional[str] = None  # Telegram: chat_id do usuário que fez /start
    widget_token: Optional[str] = None  # Saphien: token único do widget
    allowed_origins: Optional[List[str]] = None  # Saphien: whitelist de domínios


class ChannelPreferencesSchema(BaseModel):
    reject_calls: bool = False
    call_message: str = "Desculpe, não aceito chamadas."
    always_online: bool = True
    read_messages: bool = True
    read_status: bool = False
    sync_full_history: bool = False
    groups_ignore: bool = False
    parse_mode: str = "HTML"
    allow_groups: bool = True
    allow_private: bool = True
    rate_limit_per_minute: int = 30
    auto_response_enabled: bool = False
    auto_response_message: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)


class ChannelStatusSchema(BaseModel):
    state: str = "pending"  # pending, active, error, disconnected
    connection: str = "never_connected"  # never_connected, connected, disconnected, error
    last_checked: Optional[datetime] = None
    error_message: Optional[str] = None
    qr_code_pending: bool = False
    qr_code_base64: Optional[str] = None
    webhook_set: bool = False
    webhook_url_confirmed: Optional[str] = None
    bot_invite_url: Optional[str] = None


class ChannelProfileSchema(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    profile_pic_url: Optional[str] = None
    about: Optional[str] = None


class ChannelWebhookSchema(BaseModel):
    url: str
    enabled: bool = True
    webhook_by_events: bool = False
    webhook_base64: bool = True
    events: List[str] = Field(default_factory=list)
    secret_token: Optional[str] = None


class ChannelAgentSchema(BaseModel):
    id: str
    name: str
    status: str = "active"
    trigger_config: Dict[str, Any] = Field(default_factory=dict)
    priority: int = 0
    created_at: Optional[str] = None
    last_used: Optional[str] = None


class ChannelCreateSchema(BaseModel):
    channel_type: str  # evolution, telegram, discord, webhook_saphien
    instance_name: Optional[str] = None
    metadata: ChannelMetadataSchema
    enabled: bool = True
    required: ChannelRequiredSchema = Field(default_factory=ChannelRequiredSchema)
    preferences: ChannelPreferencesSchema = Field(default_factory=ChannelPreferencesSchema)
    webhook: Optional[ChannelWebhookSchema] = None
    agents: Optional[List[ChannelAgentSchema]] = Field(default_factory=list) 
    
    class Config:
        # IMPORTANTE: Permite campos extras? Se não, pode estar dropando
        extra = "allow"  # ← Isso permite campos não definidos

class ChannelUpdateSchema(BaseModel):
    metadata: Optional[ChannelMetadataSchema] = None
    enabled: Optional[bool] = None
    required: Optional[ChannelRequiredSchema] = None
    preferences: Optional[ChannelPreferencesSchema] = None
    webhook: Optional[ChannelWebhookSchema] = None
    status: Optional[Dict[str, Any]] = None
    agents: Optional[List[ChannelAgentSchema]] = None


class ChannelOutSchema(BaseModel):
    """Schema para resposta da API (leitura)"""
    id: str = Field(alias="_id")
    user_id: str
    channel_type: str
    metadata: ChannelMetadataSchema
    enabled: bool
    required: ChannelRequiredSchema
    preferences: ChannelPreferencesSchema
    status: ChannelStatusSchema
    profile: Optional[ChannelProfileSchema] = None
    agents: List[ChannelAgentSchema] = Field(default_factory=list)
    webhook: Optional[ChannelWebhookSchema] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True