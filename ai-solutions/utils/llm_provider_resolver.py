"""
Resolvedor dinâmico de provedores LLM
Permite que o sistema use diferentes provedores e modelos baseado na seleção do usuário
"""

import os
import logging
from typing import Dict, Optional, Any
import psycopg2
from core.config.settings import settings

logger = logging.getLogger(__name__)

class LLMProviderResolver:
    """Classe para resolver configurações de provedores LLM dinamicamente"""
    
    @staticmethod
    def get_provider_config_by_model_id(model_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém a configuração do provedor baseado no ID do modelo
        
        Args:
            model_id: ID do modelo selecionado
            
        Returns:
            Dicionário com configuração do provedor ou None se não encontrado
        """
        try:
            # Conectar ao PostgreSQL
            # Converter URL do SQLAlchemy para formato psycopg2
            postgres_url = settings.POSTGRES_URL.replace('postgresql+asyncpg://', 'postgresql://')
            conn = psycopg2.connect(postgres_url)
            
            cursor = conn.cursor()
            
            # Buscar configuração do provedor pelo model_id
            query = """
            SELECT
                p.id as provider_id,
                p.name as provider_name,
                p.package_name,
                p.provider_class,
                p.config_key,
                p.api_base_url,
                m.id as model_id,
                m.model_name
            FROM models m
            JOIN providers p ON m.provider_id = p.id
            WHERE m.id = %s AND p.is_active = true AND m.is_active = true
            """
            
            # Tentar converter para inteiro primeiro (ID numérico)
            try:
                model_id_int = int(model_id)
                cursor.execute(query, (model_id_int,))
            except (ValueError, TypeError):
                # Se não for numérico, buscar pelo ID como string
                logger.info(f"Buscando modelo por ID string: {model_id}")
                cursor.execute(query, (model_id,))
            result = cursor.fetchone()
            
            if not result:
                logger.warning(f"Modelo {model_id} não encontrado ou não ativo")
                return None
            
            # Extrair dados do resultado
            (provider_id, provider_name, package_name, provider_class, 
             config_key, api_base_url, model_id_db, model_name) = result
            
            # Obter API key do ambiente
            api_key = os.environ.get(config_key)
            if not api_key:
                logger.error(f"API key não encontrada para config_key: {config_key}")
                return None
            
            config = {
                "provider_id": provider_id,
                "provider_name": provider_name,
                "package_name": package_name,
                "provider_class": provider_class,
                "config_key": config_key,
                "api_key": api_key,
                "api_base_url": api_base_url,
                "model_id": model_id_db,
                "model_name": model_name
            }
            
            logger.info(f"Configuração do provedor carregada: {provider_name} - {model_name}")
            
            cursor.close()
            conn.close()
            
            return config
            
        except Exception as e:
            logger.error(f"Erro ao obter configuração do provedor para model_id {model_id}: {e}")
            return None
    
    @staticmethod
    def get_provider_config_by_agent_id(agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém a configuração do provedor baseado no ID do agente
        
        Args:
            agent_id: ID do agente selecionado
            
        Returns:
            Dicionário com configuração do provedor ou None se não encontrado
        """
        try:
            # Conectar ao PostgreSQL
            # Converter URL do SQLAlchemy para formato psycopg2
            postgres_url = settings.POSTGRES_URL.replace('postgresql+asyncpg://', 'postgresql://')
            conn = psycopg2.connect(postgres_url)
            
            cursor = conn.cursor()
            
            # Buscar configuração do provedor pelo agent_id (via MongoDB)
            # Primeiro precisamos obter o model_id do agente do MongoDB
            from pymongo import MongoClient
            mongo_client = MongoClient(settings.MONGO_URI)
            db = mongo_client[settings.MONGO_DB_NAME]
            
            # Buscar agente no MongoDB
            agent = db.agents.find_one({"_id": agent_id})
            if not agent:
                logger.warning(f"Agente {agent_id} não encontrado no MongoDB")
                return None
            
            model_id = agent.get("model")
            if not model_id:
                logger.warning(f"Agente {agent_id} não tem model configurado")
                return None
            
            # Agora buscar configuração do provedor usando o model_id
            # Garantir que model_id seja string para evitar problemas de tipo
            provider_config = LLMProviderResolver.get_provider_config_by_model_id(str(model_id))
            
            mongo_client.close()
            cursor.close()
            conn.close()
            
            return provider_config
            
        except Exception as e:
            logger.error(f"Erro ao obter configuração do provedor para agent_id {agent_id}: {e}")
            return None
    
    @staticmethod
    def resolve_provider_config(selected_model_id: str = None, selected_agent_id: str = None) -> Optional[Dict[str, Any]]:
        """
        Resolve a configuração do provedor baseado na prioridade:
        - Agente selecionado tem prioridade sobre modelo selecionado
        - Se nenhum for selecionado, usa configuração padrão
        
        Args:
            selected_model_id: ID do modelo selecionado na modal de provedor
            selected_agent_id: ID do agente selecionado na modal de agentes
            
        Returns:
            Dicionário com configuração do provedor ou None se não encontrado
        """
        # Prioridade: Agente selecionado > Modelo selecionado > Configuração padrão
        if selected_agent_id and selected_agent_id != "111111111111111111111111":
            logger.info(f"Usando configuração do agente selecionado: {selected_agent_id}")
            provider_config = LLMProviderResolver.get_provider_config_by_agent_id(selected_agent_id)
            if provider_config:
                return provider_config
        
        if selected_model_id:
            logger.info(f"Usando configuração do modelo selecionado: {selected_model_id}")
            provider_config = LLMProviderResolver.get_provider_config_by_model_id(selected_model_id)
            if provider_config:
                return provider_config
        
        # Fallback para configuração padrão (DeepSeek)
        logger.info("Usando configuração padrão (DeepSeek)")
        return {
            "provider_name": "DeepSeek",
            "package_name": "openai",
            "provider_class": "OpenAI",
            "config_key": "DEEPSEEK_API_KEY",
            "api_key": os.environ.get("DEEPSEEK_API_KEY"),
            "api_base_url": "https://api.deepseek.com/v1",
            "model_name": "deepseek-chat"
        }