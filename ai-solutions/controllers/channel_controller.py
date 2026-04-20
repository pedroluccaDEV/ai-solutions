# controllers/v1/channel_controller.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, Dict, Any, List
from bson import ObjectId
from loguru import logger

from services.channel_service import ChannelService
from schemas.channel_schema import ChannelCreateSchema, ChannelUpdateSchema
from core.auth.firebase_auth import get_current_user # vamos trocar o firebase por supabase

router = APIRouter(tags=["Channels"])


# ------------------- CRIAÇÃO DE CANAL -------------------
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=dict)
async def create_channel(
    channel_data: ChannelCreateSchema,
    current_user: dict = Depends(get_current_user),
):
    try:
        # Verifica limite de canais por usuário
        user_channels_count = ChannelService.count_user_channels(
            user_id=current_user["uid"], 
            channel_type=channel_data.channel_type
        )
        
        if user_channels_count >= 10:
            raise HTTPException(
                status_code=400,
                detail=f"Limite de 10 canais do tipo {channel_data.channel_type} atingido"
            )
        
        # 🔥 FIX: Converte para dict preservando agents
        # Tenta diferentes métodos baseado na versão do Pydantic
        if hasattr(channel_data, 'model_dump'):
            # Pydantic v2
            channel_dict = channel_data.model_dump()
        else:
            # Pydantic v1
            channel_dict = channel_data.dict()
        
        # 🔥 WORKAROUND: Se agents não está no dict mas existe no objeto, adiciona manualmente
        if 'agents' not in channel_dict and channel_data.agents:
            logger.info(f"[CONTROLLER] Agents não estava no dict. Adicionando manualmente...")
            channel_dict['agents'] = []
            for agent in channel_data.agents:
                if hasattr(agent, 'model_dump'):
                    channel_dict['agents'].append(agent.model_dump())
                elif hasattr(agent, 'dict'):
                    channel_dict['agents'].append(agent.dict())
                else:
                    channel_dict['agents'].append(agent)
            logger.info(f"[CONTROLLER] Adicionados {len(channel_dict['agents'])} agents manualmente")
        
        # 🔥 LOG para debug
        logger.info(f"[CONTROLLER] Agents no dict final: {len(channel_dict.get('agents', []))}")
        
        channel_type = channel_dict.pop("channel_type")
        
        # 🔥 GARANTE que instance_name está no root level do dict
        instance_name = channel_dict.get("instance_name")
        
        # Se não veio no root level, tenta pegar do metadata
        if not instance_name:
            instance_name = channel_dict.get("metadata", {}).get("instance_name")
            if instance_name:
                channel_dict["instance_name"] = instance_name
        
        # Se ainda não tiver, gera um padrão (fallback)
        if not instance_name:
            instance_name = f"{channel_type}_{current_user['uid'][:8]}"
            channel_dict["instance_name"] = instance_name
            if "metadata" in channel_dict:
                channel_dict["metadata"]["instance_name"] = instance_name
        
        logger.info(f"[CONTROLLER] Criando canal - instance_name: {instance_name}")
        
        # Cria o canal
        created_channel = await ChannelService.create_channel(
            user_id=current_user["uid"],
            channel_type=channel_type,
            channel_data=channel_dict
        )
        
        if not created_channel:
            raise HTTPException(status_code=400, detail="Erro ao criar canal")
        
        return {
            "success": True,
            "channel": created_channel
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[CONTROLLER] Erro ao criar canal: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


# ------------------- LISTA DE CANAIS DO USUÁRIO -------------------
@router.get("/", response_model=List[dict])
def list_channels(
    channel_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """
    Lista todos os canais do usuário.
    Opcionalmente filtra por tipo (evolution, telegram, discord, etc).
    """
    channels = ChannelService.list_user_channels(
        user_id=current_user["uid"],
        channel_type=channel_type
    )
    
    return channels


# ------------------- LISTA TODOS OS CANAIS (ADMIN) -------------------
@router.get("/admin/all", response_model=List[dict])
def list_all_channels_admin(
    channel_type: Optional[str] = None,
    enabled_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
):
    """
    [ADMIN] Lista todos os canais do sistema.
    Requer que o usuário seja admin.
    """
    # Verifica se é admin (ajuste conforme sua lógica)
    if current_user.get("email") not in ["admin@seudominio.com"]:
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    
    channels = ChannelService.list_all_channels(
        channel_type=channel_type,
        enabled_only=enabled_only,
        skip=skip,
        limit=limit
    )
    return channels


# ------------------- DETALHE DE UM CANAL -------------------
@router.get("/{channel_id}", response_model=dict)
def get_channel(
    channel_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Busca um canal específico pelo ID.
    """
    try:
        # Valida se o ID é um ObjectId válido
        if not ObjectId.is_valid(channel_id):
            raise HTTPException(status_code=400, detail="ID de canal inválido")
        
        channel = ChannelService.get_channel(channel_id)
        
        if not channel:
            raise HTTPException(status_code=404, detail="Canal não encontrado")
        
        # Verifica se o canal pertence ao usuário
        if channel.get("user_id") != current_user["uid"]:
            raise HTTPException(status_code=403, detail="Acesso negado")
        
        return channel
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


# ------------------- BUSCA POR INSTANCE_NAME -------------------
@router.get("/by-instance/{channel_type}/{instance_name}", response_model=dict)
def get_channel_by_instance_name(
    channel_type: str,
    instance_name: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Busca um canal pelo nome da instância (ex: instance_5511999999999).
    """
    user_id, channel = ChannelService.get_channel_by_instance_name(
        channel_type=channel_type,
        instance_name=instance_name
    )
    
    if not channel:
        raise HTTPException(status_code=404, detail="Canal não encontrado")
    
    # Verifica se o canal pertence ao usuário
    if user_id != current_user["uid"]:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    return channel


# ------------------- BUSCA POR BOT_TOKEN (TELEGRAM) -------------------
@router.get("/telegram/by-token/{bot_token}", response_model=dict)
def get_channel_by_bot_token(
    bot_token: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Busca um canal do Telegram pelo bot_token.
    """
    user_id, channel = ChannelService.get_channel_by_bot_token(bot_token)
    
    if not channel:
        raise HTTPException(status_code=404, detail="Canal do Telegram não encontrado")
    
    # Verifica se o canal pertence ao usuário
    if user_id != current_user["uid"]:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    return channel


# ------------------- ATUALIZAÇÃO DE CANAL -------------------
@router.put("/{channel_id}", response_model=dict)
async def update_channel(
    channel_id: str,
    channel_data: ChannelUpdateSchema,
    current_user: dict = Depends(get_current_user),
):
    """
    Atualiza um canal existente.
    """
    try:
        if not ObjectId.is_valid(channel_id):
            raise HTTPException(status_code=400, detail="ID de canal inválido")
        
        # Verifica se o canal existe e pertence ao usuário
        existing = ChannelService.get_channel(channel_id)
        
        if not existing:
            raise HTTPException(status_code=404, detail="Canal não encontrado")
        
        if existing.get("user_id") != current_user["uid"]:
            raise HTTPException(status_code=403, detail="Acesso negado")
        
        # Converte para dict
        if hasattr(channel_data, 'model_dump'):
            update_dict = channel_data.model_dump(exclude_unset=True)
        else:
            update_dict = channel_data.dict(exclude_unset=True)
        
        # Atualiza
        updated = await ChannelService.update_channel(
            channel_id=channel_id,
            user_id=current_user["uid"],
            updates=update_dict
        )
        
        if not updated:
            raise HTTPException(status_code=400, detail="Erro ao atualizar canal")
        
        # Busca o canal atualizado
        channel = ChannelService.get_channel(channel_id)
        
        return {
            "success": True,
            "channel": channel
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


# ------------------- ATUALIZAÇÃO PARCIAL DE CANAL -------------------
@router.patch("/{channel_id}", response_model=dict)
async def partial_update_channel(
    channel_id: str,
    channel_data: ChannelUpdateSchema,
    current_user: dict = Depends(get_current_user),
):
    """
    Atualização parcial de um canal.
    """
    try:
        if not ObjectId.is_valid(channel_id):
            raise HTTPException(status_code=400, detail="ID de canal inválido")
        
        # Verifica se o canal existe e pertence ao usuário
        existing = ChannelService.get_channel(channel_id)
        
        if not existing:
            raise HTTPException(status_code=404, detail="Canal não encontrado")
        
        if existing.get("user_id") != current_user["uid"]:
            raise HTTPException(status_code=403, detail="Acesso negado")
        
        # Converte para dict (apenas campos enviados)
        if hasattr(channel_data, 'model_dump'):
            update_dict = channel_data.model_dump(exclude_unset=True)
        else:
            update_dict = channel_data.dict(exclude_unset=True)
        
        if not update_dict:
            raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")
        
        # Atualiza
        updated = await ChannelService.update_channel(
            channel_id=channel_id,
            user_id=current_user["uid"],
            updates=update_dict
        )
        
        if not updated:
            raise HTTPException(status_code=400, detail="Erro ao atualizar canal")
        
        # Busca o canal atualizado
        channel = ChannelService.get_channel(channel_id)
        
        return {
            "success": True,
            "channel": channel
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


# ------------------- ATUALIZAR STATUS DO CANAL -------------------
@router.patch("/{channel_id}/status", response_model=dict)
def update_channel_status(
    channel_id: str,
    status_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
):
    """
    Atualiza o status de conexão do canal.
    
    Body example:
    {
        "state": "active",
        "connection": "connected",
        "error_message": null
    }
    """
    try:
        if not ObjectId.is_valid(channel_id):
            raise HTTPException(status_code=400, detail="ID de canal inválido")
        
        # Verifica se o canal existe e pertence ao usuário
        existing = ChannelService.get_channel(channel_id)
        
        if not existing:
            raise HTTPException(status_code=404, detail="Canal não encontrado")
        
        if existing.get("user_id") != current_user["uid"]:
            raise HTTPException(status_code=403, detail="Acesso negado")
        
        # Atualiza status
        updated = ChannelService.update_channel_status(
            channel_id=channel_id,
            user_id=current_user["uid"],
            state=status_data.get("state"),
            connection=status_data.get("connection"),
            error_message=status_data.get("error_message")
        )
        
        if not updated:
            raise HTTPException(status_code=400, detail="Erro ao atualizar status")
        
        return {
            "success": True,
            "message": "Status atualizado com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


# ------------------- HABILITAR/DESABILITAR CANAL -------------------
@router.post("/{channel_id}/enable", response_model=dict)
def enable_channel(
    channel_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Habilita um canal.
    """
    try:
        if not ObjectId.is_valid(channel_id):
            raise HTTPException(status_code=400, detail="ID de canal inválido")
        
        # Verifica se o canal existe e pertence ao usuário
        existing = ChannelService.get_channel(channel_id)
        
        if not existing:
            raise HTTPException(status_code=404, detail="Canal não encontrado")
        
        if existing.get("user_id") != current_user["uid"]:
            raise HTTPException(status_code=403, detail="Acesso negado")
        
        updated = ChannelService.enable_channel(
            channel_id=channel_id,
            user_id=current_user["uid"]
        )
        
        if not updated:
            raise HTTPException(status_code=400, detail="Erro ao habilitar canal")
        
        return {"success": True, "message": "Canal habilitado com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.post("/{channel_id}/disable", response_model=dict)
def disable_channel(
    channel_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Desabilita um canal.
    """
    try:
        if not ObjectId.is_valid(channel_id):
            raise HTTPException(status_code=400, detail="ID de canal inválido")
        
        # Verifica se o canal existe e pertence ao usuário
        existing = ChannelService.get_channel(channel_id)
        
        if not existing:
            raise HTTPException(status_code=404, detail="Canal não encontrado")
        
        if existing.get("user_id") != current_user["uid"]:
            raise HTTPException(status_code=403, detail="Acesso negado")
        
        updated = ChannelService.disable_channel(
            channel_id=channel_id,
            user_id=current_user["uid"]
        )
        
        if not updated:
            raise HTTPException(status_code=400, detail="Erro ao desabilitar canal")
        
        return {"success": True, "message": "Canal desabilitado com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


# ------------------- DELETA CANAL -------------------
@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel(
    channel_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Remove um canal.
    """
    try:
        if not ObjectId.is_valid(channel_id):
            raise HTTPException(status_code=400, detail="ID de canal inválido")
        
        # Verifica se o canal existe e pertence ao usuário
        existing = ChannelService.get_channel(channel_id)
        
        if not existing:
            raise HTTPException(status_code=404, detail="Canal não encontrado")
        
        if existing.get("user_id") != current_user["uid"]:
            raise HTTPException(status_code=403, detail="Acesso negado")
        
        # TODO: Antes de deletar, chamar cleanup específico do canal
        # Ex: Telegram: deleteWebhook, Evolution: delete instance
        
        # Delete
        deleted = await ChannelService.delete_channel(
            channel_id=channel_id,
            user_id=current_user["uid"]
        )
        
        if not deleted:
            raise HTTPException(status_code=400, detail="Erro ao deletar canal")
        
        return None  # 204 No Content
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


# ------------------- ADICIONAR AGENTE AO CANAL -------------------
@router.post("/{channel_id}/agents/{agent_id}", response_model=dict)
def add_agent_to_channel(
    channel_id: str,
    agent_id: str,
    trigger_config: Optional[Dict[str, Any]] = None,
    current_user: dict = Depends(get_current_user),
):
    """
    Adiciona um agente existente ao canal.
    """
    try:
        if not ObjectId.is_valid(channel_id):
            raise HTTPException(status_code=400, detail="ID de canal inválido")
        
        # Verifica se o canal existe e pertence ao usuário
        channel = ChannelService.get_channel(channel_id)
        
        if not channel:
            raise HTTPException(status_code=404, detail="Canal não encontrado")
        
        if channel.get("user_id") != current_user["uid"]:
            raise HTTPException(status_code=403, detail="Acesso negado")
        
        # Busca o agente para obter o nome
        from dao.mongo.v1.agent_dao import AgentDAO
        agent = AgentDAO.get_agent_by_id(agent_id)
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agente não encontrado")
        
        # Verifica se o agente pertence ao usuário
        if agent.get("uid") != current_user["uid"]:
            raise HTTPException(status_code=403, detail="Acesso negado ao agente")
        
        # Adiciona ao canal
        result = ChannelService.add_agent_to_channel(
            channel_id=channel_id,
            user_id=current_user["uid"],
            agent_id=agent_id,
            agent_name=agent.get("name", agent_id),
            trigger_config=trigger_config
        )
        
        if not result:
            raise HTTPException(status_code=400, detail="Erro ao adicionar agente ao canal")
        
        return {"success": True, "message": f"Agente {agent_id} adicionado ao canal"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


# ------------------- REMOVER AGENTE DO CANAL -------------------
@router.delete("/{channel_id}/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_agent_from_channel(
    channel_id: str,
    agent_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Remove um agente do canal.
    """
    try:
        if not ObjectId.is_valid(channel_id):
            raise HTTPException(status_code=400, detail="ID de canal inválido")
        
        # Verifica se o canal existe e pertence ao usuário
        channel = ChannelService.get_channel(channel_id)
        
        if not channel:
            raise HTTPException(status_code=404, detail="Canal não encontrado")
        
        if channel.get("user_id") != current_user["uid"]:
            raise HTTPException(status_code=403, detail="Acesso negado")
        
        result = ChannelService.remove_agent_from_channel(
            channel_id=channel_id,
            user_id=current_user["uid"],
            agent_id=agent_id
        )
        
        if not result:
            raise HTTPException(status_code=400, detail="Erro ao remover agente do canal")
        
        return None  # 204 No Content
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")