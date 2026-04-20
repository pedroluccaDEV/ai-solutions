# features/channels/webhook_saphien/connection/saphien_channel_handler.py
"""
Handler para o canal webhook_saphien.
Gerencia criação, atualização e deleção de canais do tipo widget JS.
"""
from typing import Dict, Any, Optional
from loguru import logger
import secrets
import json

from features.channels.webhook_saphien.connection.saphien_widget_generator import SaphienWidgetGenerator


class SaphienChannelHandler:
    """Handler para operações do canal webhook_saphien."""
    
    def __init__(self):
        self.widget_generator = SaphienWidgetGenerator()
    
    def on_channel_created(self, channel_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Callback quando um canal Saphien é criado.
        
        Gera widget_token único e prepara os dados iniciais.
        
        Args:
            channel_data: Dados do canal sendo criado
            
        Returns:
            Dict com widget_token e webhook_url
        """
        try:
            # Gera token único para o widget
            widget_token = self._generate_widget_token()
            
            # Obtém nome da instância
            instance_name = channel_data.get("metadata", {}).get("instance_name", "unknown")
            
            # Constrói URL do webhook
            webhook_url = f"/api/v1/saphien/webhook_saphien/{widget_token}"
            
            # Prepara configurações do widget
            widget_config = {
                "widget_token": widget_token,
                "webhook_url": webhook_url,
                "instance_name": instance_name,
                "allowed_origins": channel_data.get("required", {}).get("allowed_origins", []),
                "preferences": channel_data.get("preferences", {}).get("extra", {})
            }
            
            # Gera snippet JS (opcional, pode ser gerado sob demanda)
            js_snippet = self.widget_generator.generate_widget_script(widget_config)
            
            logger.info(f"[SAPHIEN_HANDLER] Widget criado | token={widget_token[:15]}... | instance={instance_name}")
            
            return {
                "widget_token": widget_token,
                "webhook_url": webhook_url,
                "js_snippet": js_snippet  # Pode ser usado na resposta da API
            }
            
        except Exception as e:
            logger.error(f"[SAPHIEN_HANDLER] Erro ao criar canal: {e}")
            raise RuntimeError(f"Falha ao criar widget Saphien: {str(e)}")
    
    def on_channel_updated(self, channel_data: Dict[str, Any], updated_fields: Dict[str, Any]) -> None:
        """
        Callback quando um canal Saphien é atualizado.
        
        Args:
            channel_data: Dados completos do canal
            updated_fields: Campos que foram atualizados
        """
        try:
            # Verifica se alguma configuração relevante mudou
            if "preferences" in updated_fields:
                logger.info(f"[SAPHIEN_HANDLER] Preferências do widget atualizadas")
            
            if "required" in updated_fields and "allowed_origins" in updated_fields["required"]:
                logger.info(f"[SAPHIEN_HANDLER] Allowed origins atualizado")
                
        except Exception as e:
            logger.warning(f"[SAPHIEN_HANDLER] Erro no update (não crítico): {e}")
    
    def on_channel_deleted(self, channel_data: Dict[str, Any]) -> None:
        """
        Callback quando um canal Saphien é deletado.
        
        Args:
            channel_data: Dados do canal sendo deletado
        """
        try:
            widget_token = channel_data.get("required", {}).get("widget_token")
            if widget_token:
                logger.info(f"[SAPHIEN_HANDLER] Widget deletado | token={widget_token[:15]}...")
        except Exception as e:
            logger.warning(f"[SAPHIEN_HANDLER] Erro no delete (não crítico): {e}")
    
    def _generate_widget_token(self) -> str:
        """
        Gera um token único para o widget.
        
        Formato: sw_<32 caracteres hex>
        sw = saphien_widget
        """
        return f"sw_{secrets.token_hex(32)}"