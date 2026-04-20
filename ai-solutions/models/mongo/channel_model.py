# models/v1/channel_model.py
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from models.mongo.base import MongoModel
from datetime import datetime
from enum import Enum


class ChannelType(str, Enum):
    EVOLUTION = "evolution"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    WEBHOOK = "webhook"
    WEBHOOK_SAPHIEN = "webhook_saphien"  # 🔥 ADICIONADO
    EMAIL = "email"


class ChannelStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    ERROR = "error"
    DISABLED = "disabled"


class ConnectionState(str, Enum):
    AWAITING_QR = "awaiting_qr"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    NEVER_CONNECTED = "never_connected"


class ChannelMetadata(BaseModel):
    """Metadados do canal"""
    instance_name: str
    title: str
    description: Optional[str] = ""
    icon: str = "message-square"
    category: str = "communication"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ChannelRequired(BaseModel):
    """Campos obrigatórios - variam por canal"""
    # Evolution
    phone_number: Optional[str] = None
    instance_name: Optional[str] = None
    # Telegram
    bot_token: Optional[str] = None
    bot_username: Optional[str] = None
    # Discord
    bot_token_discord: Optional[str] = None
    guild_id: Optional[str] = None
    # Webhook API
    webhook_endpoint: Optional[str] = None
    api_key_header: Optional[str] = None
    # 🔥 Saphien Webhook (NOVO)
    widget_token: Optional[str] = None
    allowed_origins: Optional[List[str]] = None
    # 🔥 Telegram específico
    chat_id: Optional[str] = None  # chat_id do usuário que fez /start


class ChannelPreferences(BaseModel):
    """Preferências do canal"""
    # Evolution
    reject_calls: bool = False
    call_message: str = "Desculpe, não aceito chamadas."
    always_online: bool = True
    read_messages: bool = True
    read_status: bool = False
    sync_full_history: bool = False
    groups_ignore: bool = False
    # Telegram
    parse_mode: str = "HTML"  # HTML, Markdown, None
    allow_groups: bool = True
    allow_private: bool = True
    # Genérico
    rate_limit_per_minute: int = 30
    auto_response_enabled: bool = False
    auto_response_message: Optional[str] = None
    # Opções extras (🔥 usado pelo Saphien para configurações do widget)
    extra: Dict[str, Any] = Field(default_factory=dict)


class ChannelStatusInfo(BaseModel):
    """Status do canal"""
    state: ChannelStatus = ChannelStatus.PENDING
    connection: ConnectionState = ConnectionState.NEVER_CONNECTED
    last_checked: Optional[datetime] = None
    error_message: Optional[str] = None
    # Evolution específico
    qr_code_pending: bool = False
    qr_code_base64: Optional[str] = None
    # Telegram específico
    webhook_set: bool = False
    webhook_url_confirmed: Optional[str] = None
    # Discord específico
    bot_invite_url: Optional[str] = None


class ChannelProfile(BaseModel):
    """Perfil público do canal"""
    name: Optional[str] = None
    username: Optional[str] = None
    profile_pic_url: Optional[str] = None
    about: Optional[str] = None


class ChannelWebhook(BaseModel):
    """Configuração de webhook (para quem vai receber)"""
    url: str
    enabled: bool = True
    webhook_by_events: bool = False
    webhook_base64: bool = True
    events: List[str] = Field(default_factory=list)
    secret_token: Optional[str] = None  # Telegram usa isso


class TriggerConfig(BaseModel):
    """Configuração de trigger para roteamento de agentes"""
    enabled: bool = False
    type: str = "keyword"  # keyword, regex, contains
    operator: str = "contains"  # contains, equals, startswith, endswith
    trigger: str = ""
    case_sensitive: bool = False


class ChannelAgent(BaseModel):
    """Agente associado ao canal"""
    id: str
    name: str
    status: str = "active"
    trigger_config: TriggerConfig = Field(default_factory=TriggerConfig)
    priority: int = 0  # 0 = menor prioridade, maior número = maior prioridade
    created_at: Optional[str] = None  # 🔥 ADICIONADO
    last_used: Optional[str] = None  # 🔥 ADICIONADO


class Channel(BaseModel, MongoModel):
    """Modelo COMPLETO do canal - igual ao seu Evolution"""
    __collection__ = "channels"

    id: str = Field(alias="_id")
    
    # Campos principais
    user_id: str  # Firebase UID ou ID do usuário dono
    channel_type: str  # evolution, telegram, webhook_saphien, etc
    
    # Dados do canal
    instance_name: Optional[str] = None  # 🔥 ADICIONADO no root level
    metadata: ChannelMetadata
    enabled: bool = True
    required: ChannelRequired = Field(default_factory=ChannelRequired)
    preferences: ChannelPreferences = Field(default_factory=ChannelPreferences)
    status: ChannelStatusInfo = Field(default_factory=ChannelStatusInfo)
    profile: ChannelProfile = Field(default_factory=ChannelProfile)
    agents: List[ChannelAgent] = Field(default_factory=list)
    webhook: Optional[ChannelWebhook] = None
    
    # 🔥 Campos específicos do Telegram (opcionais)
    bot_info: Optional[Dict[str, Any]] = None
    
    # Campos de sistema
    org: Optional[str] = None
    type: Optional[str] = "channel"
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }