# features/channels/webhook_saphien/connection/saphien_connection.py
"""
Gerenciador de conexão para o widget Saphien.
Responsável por enviar respostas de volta para o widget.
"""
from typing import Dict, Any, Optional
from loguru import logger
import httpx
from fastapi.responses import JSONResponse


class SaphienConnection:
    """Gerencia respostas do webhook Saphien."""
    
    def __init__(self, widget_token: str, base_url: str = ""):
        """
        Args:
            widget_token: Token do widget
            base_url: URL base da API (opcional, para respostas)
        """
        self.widget_token = widget_token
        self.base_url = base_url
    
    @staticmethod
    def create_response(reply: str, status: str = "success") -> Dict[str, Any]:
        """
        Cria resposta para o widget.
        
        Args:
            reply: Texto de resposta
            status: Status da resposta (success, error)
        
        Returns:
            Dict com a resposta formatada
        """
        return {
            "status": status,
            "reply": reply,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def create_error_response(error_message: str) -> Dict[str, Any]:
        """
        Cria resposta de erro.
        """
        return {
            "status": "error",
            "reply": f"⚠️ {error_message}",
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def create_streaming_response(chunk: str, is_last: bool = False) -> Dict[str, Any]:
        """
        Cria resposta para streaming (se implementado).
        """
        return {
            "type": "stream" if not is_last else "stream_end",
            "chunk": chunk,
            "timestamp": datetime.now().isoformat()
        }


# Import necessário para datetime
from datetime import datetime