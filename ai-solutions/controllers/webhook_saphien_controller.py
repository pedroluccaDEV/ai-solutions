# controllers/v1/webhook_saphien_controller.py
"""
Controller para webhook do Saphien Widget.
Token de autenticação no HEADER (não na URL) para segurança.
"""
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Header, Depends, Query
from fastapi.responses import Response
from loguru import logger

from services.webhook_saphien_service import WebhookSaphienService
from services.channel_service import ChannelService
from core.config.database import get_mongo_db
from schemas.webhook_saphien_schema import (
    SaphienWebhookPayload,
    SaphienSessionPayload,
    SaphienMessageResponseSchema,
    SaphienSessionResponseSchema,
    SaphienMessagesResponseSchema,
    SaphienWidgetScriptResponseSchema
)

router = APIRouter(tags=["Saphien Webhook"])


# ======================================================
# WEBHOOK PRINCIPAL - RECEBE MENSAGENS (SEGURO)
# ======================================================

@router.post("/webhook_saphien", response_model=SaphienMessageResponseSchema)
async def saphien_webhook(
    payload: SaphienWebhookPayload,
    request: Request,
    db=Depends(get_mongo_db),
    widget_token: str = Header(..., alias="X-Widget-Token"),
    session_id: str = Header(..., alias="X-Session-Id"),
    origin: Optional[str] = Header(None, alias="Origin"),
):
    """
    Recebe mensagens do widget Saphien - TOKEN NO HEADER (seguro).

    Headers obrigatórios:
    - X-Widget-Token: Token do widget (gerado na criação do canal)
    - X-Session-Id: ID da sessão do visitante (gerado pelo frontend)
    
    Headers opcionais:
    - Origin: Domínio de origem (para validação CORS)
    
    Payload:
    {
        "message": "texto da mensagem",
        "sender": "user",
        "timestamp": "2024-01-01T00:00:00Z",
        "metadata": {}
    }
    """
    try:
        logger.info(f"[SAPHIEN CONTROLLER] Mensagem recebida | token: {widget_token[:15]}... | session: {session_id}")
        
        # Converte payload para dict
        data = payload.dict()
        data["session_id"] = session_id  # Garante que session_id do header seja usado
        
        result = await WebhookSaphienService.handle_incoming_message(
            widget_token=widget_token,
            session_id=session_id,
            data=data,
            origin=origin,
            db=db
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Mensagem não processável.")
        
        return SaphienMessageResponseSchema(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[SAPHIEN CONTROLLER] Erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ======================================================
# REGISTRO DE SESSÃO (SEGURO)
# ======================================================

@router.post("/webhook_saphien/session", response_model=SaphienSessionResponseSchema)
async def saphien_register_session(
    payload: SaphienSessionPayload,
    request: Request,
    db=Depends(get_mongo_db),
    widget_token: str = Header(..., alias="X-Widget-Token"),
    session_id: str = Header(..., alias="X-Session-Id"),
    origin: Optional[str] = Header(None, alias="Origin"),
):
    try:
        logger.info(f"[SAPHIEN CONTROLLER] Registro de sessão | token: {widget_token[:15]}... | session: {session_id}")
        
        # Converte payload para dict (já tem session_id)
        data = payload.dict()
        # data["session_id"] = session_id  # ← REMOVA esta linha (opcional, pois o payload já tem)
        
        # Verifica consistência entre header e body
        if data.get("session_id") != session_id:
            logger.warning(f"[SAPHIEN CONTROLLER] session_id mismatch: header={session_id}, body={data.get('session_id')}")
            # Pode optar por usar o do header ou retornar erro
            data["session_id"] = session_id  # Força usar o do header
        
        result = await WebhookSaphienService.register_session(
            widget_token=widget_token,
            session_id=session_id,
            data=data,
            origin=origin,
            db=db
        )
        
        if not result:
            raise HTTPException(status_code=400, detail="Erro ao registrar sessão")
        
        return SaphienSessionResponseSchema(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[SAPHIEN CONTROLLER] Erro ao registrar sessão: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ======================================================
# BUSCAR MENSAGENS DA SESSÃO (SEGURO)
# ======================================================

@router.get("/webhook_saphien/messages", response_model=SaphienMessagesResponseSchema)
async def saphien_get_messages(
    request: Request,
    db=Depends(get_mongo_db),
    widget_token: str = Header(..., alias="X-Widget-Token"),
    session_id: str = Header(..., alias="X-Session-Id"),
    limit: int = Query(50, ge=1, le=100, description="Limite de mensagens"),
    origin: Optional[str] = Header(None, alias="Origin"),
):
    """
    Retorna as mensagens de uma sessão - TOKEN NO HEADER (seguro).

    Headers obrigatórios:
    - X-Widget-Token: Token do widget
    - X-Session-Id: ID da sessão do visitante
    
    Query params:
    - limit: Número máximo de mensagens (padrão 50, max 100)
    """
    try:
        logger.info(f"[SAPHIEN CONTROLLER] Buscando mensagens | token: {widget_token[:15]}... | session: {session_id}")
        
        result = await WebhookSaphienService.get_session_messages(
            widget_token=widget_token,
            session_id=session_id,
            origin=origin,
            limit=limit
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")
        
        return SaphienMessagesResponseSchema(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[SAPHIEN CONTROLLER] Erro ao buscar mensagens: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ======================================================
# GERAR SCRIPT DO WIDGET (JSON)
# ======================================================

@router.get("/channels/{channel_id}/widget-script", response_model=SaphienWidgetScriptResponseSchema)
async def get_widget_script(
    channel_id: str,
    request: Request,
    db=Depends(get_mongo_db),
):
    """
    Retorna o script JS do widget para embed (formato JSON).

    Endpoint: GET /api/v1/channels/{channel_id}/widget-script
    
    Retorna:
    {
        "success": true,
        "script": "código JS...",
        "widget_token": "sw_xxx...",
        "embed_code": "<script src='...'></script>"
    }
    """
    try:
        channel = ChannelService.get_channel(channel_id)
        
        if not channel:
            raise HTTPException(status_code=404, detail="Canal não encontrado")
        
        if channel.get("channel_type") != "webhook_saphien":
            raise HTTPException(status_code=400, detail="Canal não é do tipo webhook_saphien")
        
        widget_token = channel.get("required", {}).get("widget_token")
        if not widget_token:
            raise HTTPException(status_code=400, detail="Widget token não encontrado")
        
        if not channel.get("enabled", True):
            raise HTTPException(status_code=400, detail="Canal está desabilitado")
        
        preferences = channel.get("preferences", {}).get("extra", {})
        allowed_origins = channel.get("required", {}).get("allowed_origins", [])
        instance_name = channel.get("metadata", {}).get("title", "Saphien Assistant")
        
        base_url = str(request.base_url).rstrip('/')
        
        widget_config = {
            "widget_token": widget_token,
            "apiUrl": f"{base_url}/api/v1/saphien/webhook_saphien",
            "instanceName": instance_name,
            "allowedOrigins": allowed_origins,
            "position": preferences.get("position", "bottom-right"),
            "primaryColor": preferences.get("primary_color", "#5c6bc0"),
            "placeholderText": preferences.get("placeholder_text", "Como posso ajudar?"),
            "showBranding": preferences.get("show_branding", True),
            "windowTitle": preferences.get("window_title", "Assistente Virtual"),
            "windowSubtitle": preferences.get("window_subtitle", "Online agora"),
            "theme": preferences.get("theme", "light"),
            "chatHeight": preferences.get("chat_height", "500px"),
            "chatWidth": preferences.get("chat_width", "380px"),
            "buttonIcon": preferences.get("button_icon", "message-circle"),
        }
        
        from features.channels.webhook_saphien.connection.saphien_widget_generator import SaphienWidgetGenerator
        generator = SaphienWidgetGenerator()
        script = generator.generate_widget_script(widget_config)
        
        logger.info(f"[SAPHIEN CONTROLLER] Script gerado para canal {channel_id}")
        
        return SaphienWidgetScriptResponseSchema(
            success=True,
            script=script,
            widget_token=widget_token,
            embed_code=f'<script src="{base_url}/api/v1/saphien/channels/{channel_id}/widget-script.js"></script>'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[SAPHIEN CONTROLLER] Erro ao gerar script: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ======================================================
# GERAR SCRIPT DO WIDGET (JS DIRETO)
# ======================================================

@router.get("/channels/{channel_id}/widget-script.js")
async def get_widget_script_js(
    channel_id: str,
    request: Request,
    db=Depends(get_mongo_db),
):
    """
    Retorna o script JS como arquivo .js para embed direto.
    """
    try:
        channel = ChannelService.get_channel(channel_id)
        
        if not channel:
            raise HTTPException(status_code=404, detail="Canal não encontrado")
        
        if channel.get("channel_type") != "webhook_saphien":
            raise HTTPException(status_code=400, detail="Canal não é do tipo webhook_saphien")
        
        widget_token = channel.get("required", {}).get("widget_token")
        if not widget_token:
            raise HTTPException(status_code=400, detail="Widget token não encontrado")
        
        if not channel.get("enabled", True):
            raise HTTPException(status_code=400, detail="Canal está desabilitado")
        
        preferences = channel.get("preferences", {}).get("extra", {})
        allowed_origins = channel.get("required", {}).get("allowed_origins", [])
        instance_name = channel.get("metadata", {}).get("title", "Saphien Assistant")
        
        base_url = str(request.base_url).rstrip('/')
        
        widget_config = {
            "widget_token": widget_token,
            "apiUrl": f"{base_url}/api/v1/saphien/webhook_saphien",
            "instanceName": instance_name,
            "allowedOrigins": allowed_origins,
            "position": preferences.get("position", "bottom-right"),
            "primaryColor": preferences.get("primary_color", "#5c6bc0"),
            "placeholderText": preferences.get("placeholder_text", "Como posso ajudar?"),
            "showBranding": preferences.get("show_branding", True),
            "windowTitle": preferences.get("window_title", "Assistente Virtual"),
            "windowSubtitle": preferences.get("window_subtitle", "Online agora"),
            "theme": preferences.get("theme", "light"),
            "chatHeight": preferences.get("chat_height", "500px"),
            "chatWidth": preferences.get("chat_width", "380px"),
            "buttonIcon": preferences.get("button_icon", "message-circle"),
        }
        
        from features.channels.webhook_saphien.connection.saphien_widget_generator import SaphienWidgetGenerator
        generator = SaphienWidgetGenerator()
        script = generator.generate_widget_script(widget_config)
        
        return Response(
            content=script,
            media_type="application/javascript",
            headers={
                "Cache-Control": "public, max-age=3600",
                "X-Content-Type-Options": "nosniff",
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[SAPHIEN CONTROLLER] Erro ao gerar script JS: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ======================================================
# HEALTH CHECK (opcional, mantido para compatibilidade)
# ======================================================

@router.get("/webhook_saphien/health")
async def saphien_health_check(
    widget_token: str = Header(..., alias="X-Widget-Token"),
):
    """
    Health check para verificar se o webhook está ativo.
    """
    try:
        user_id, channel_data = ChannelService.get_channel_by_widget_token(widget_token)
        
        if not channel_data:
            return {"status": "error", "message": "Canal não encontrado"}
        
        return {
            "status": "ok",
            "channel_type": channel_data.get("channel_type"),
            "enabled": channel_data.get("enabled", True),
            "instance_name": channel_data.get("instance_name"),
        }
        
    except Exception as e:
        logger.exception(f"[SAPHIEN CONTROLLER] Health check error: {e}")
        return {"status": "error", "message": str(e)}