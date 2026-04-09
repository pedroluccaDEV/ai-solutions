"""
Carregador de configurações de agentes do MongoDB
Integra as informações dos agentes da coleção 'agents' no comportamento do agente de IA
"""

import logging
from typing import Dict, Optional
from bson import ObjectId
from core.config.database import get_mongo_db

logger = logging.getLogger(__name__)

class AgentConfigLoader:
    """Carrega e processa configurações de agentes do MongoDB"""
    
    @staticmethod
    def load_agent_config(agent_id: str) -> Optional[Dict]:
        """
        Carrega as configurações completas de um agente da coleção 'agents'
        
        Args:
            agent_id: ID do agente no MongoDB
            
        Returns:
            Dicionário com configurações do agente ou None se não encontrado
        """
        try:
            logger.info(f"=== [AGENT CONFIG LOADER] Iniciando carregamento do agente: {agent_id} ===")
            logger.info(f"[AGENT CONFIG LOADER] Tipo do agent_id: {type(agent_id)}")
            
            # Verificar se é um agente especial (como "maestro") que não está no MongoDB
            if agent_id == "maestro":
                logger.info(f"[AGENT CONFIG LOADER] Agente especial '{agent_id}' - não está no MongoDB")
                return None
            
            # Verificar se é um ObjectId válido
            try:
                ObjectId(agent_id)
            except Exception:
                logger.warning(f"[AGENT CONFIG LOADER] ID '{agent_id}' não é um ObjectId válido")
                return None
            
            db = get_mongo_db()
            logger.info(f"[AGENT CONFIG LOADER] Conexão com MongoDB estabelecida")
            
            # Buscar agente no MongoDB
            logger.info(f"[AGENT CONFIG LOADER] Buscando agente com ID: {agent_id}")
            agent = db["agents"].find_one({"_id": ObjectId(agent_id)})
            
            if not agent:
                logger.warning(f"[AGENT CONFIG LOADER] Agente {agent_id} não encontrado no MongoDB")
                return None
            
            logger.info(f"[AGENT CONFIG LOADER] Agente encontrado: {agent.get('name', 'Sem nome')}")
            
            # Converter ObjectId para string
            agent["_id"] = str(agent["_id"])
            
            # Extrair campos relevantes para personalização do comportamento
            config = {
                "id": agent["_id"],
                "name": agent.get("name", "Agente Desconhecido"),
                "category": agent.get("category", "general"),
                "description": agent.get("description", ""),
                "personalityInstructions": agent.get("personalityInstructions", ""),
                "agentRules": agent.get("agentRules", ""),
                "goal": agent.get("goal", ""),
                "roleDefinition": agent.get("roleDefinition", ""),
                "temperature": agent.get("temperature", 0.7),
                "maxTokens": agent.get("maxTokens", 2000),
                "tools": agent.get("tools", []),
                "knowledgeBase": agent.get("knowledgeBase", []),
                "mcps": agent.get("mcps", []),
                "visibility": agent.get("visibility", "private"),
                "status": agent.get("status", "active")
            }
            
            logger.info(f"[AGENT CONFIG LOADER] Configurações do agente {agent_id} carregadas com sucesso")
            logger.info(f"[AGENT CONFIG LOADER] Nome: {config['name']}")
            logger.info(f"[AGENT CONFIG LOADER] Categoria: {config['category']}")
            logger.info(f"[AGENT CONFIG LOADER] Descrição: {len(config['description'])} caracteres")
            logger.info(f"[AGENT CONFIG LOADER] Personalidade: {len(config['personalityInstructions'])} caracteres")
            logger.info(f"[AGENT CONFIG LOADER] Regras: {len(config['agentRules'])} caracteres")
            logger.info(f"[AGENT CONFIG LOADER] Objetivo: {len(config['goal'])} caracteres")
            logger.info(f"[AGENT CONFIG LOADER] Papel: {len(config['roleDefinition'])} caracteres")
            
            return config
            
        except Exception as e:
            logger.error(f"[AGENT CONFIG LOADER] Erro ao carregar configurações do agente {agent_id}: {e}")
            import traceback
            logger.error(f"[AGENT CONFIG LOADER] Traceback: {traceback.format_exc()}")
            return None
    
    @staticmethod
    def build_agent_system_prompt(agent_config: Dict) -> str:
        """
        Constrói o system prompt personalizado baseado nas configurações do agente
        
        Args:
            agent_config: Configurações do agente carregadas do MongoDB
            
        Returns:
            String com o system prompt personalizado
        """
        if not agent_config:
            return "Você é um assistente de IA útil e informativo."
        
        # Construir prompt baseado nas configurações do agente
        prompt_parts = []
        
        # Nome e categoria
        if agent_config.get("name"):
            prompt_parts.append(f"Você é {agent_config['name']}")
            if agent_config.get("category"):
                prompt_parts.append(f", um agente especializado em {agent_config['category']}")
            prompt_parts.append(".")
        else:
            prompt_parts.append("Você é um assistente de IA especializado.")
        
        # Definição de papel
        if agent_config.get("roleDefinition"):
            prompt_parts.append(f"\n\nSeu papel: {agent_config['roleDefinition']}")
        
        # Personalidade
        if agent_config.get("personalityInstructions"):
            prompt_parts.append(f"\n\nPersonalidade: {agent_config['personalityInstructions']}")
        
        # Objetivo
        if agent_config.get("goal"):
            prompt_parts.append(f"\n\nObjetivo: {agent_config['goal']}")
        
        # Regras
        if agent_config.get("agentRules"):
            prompt_parts.append(f"\n\nRegras a seguir: {agent_config['agentRules']}")
        
        # Descrição geral
        if agent_config.get("description"):
            prompt_parts.append(f"\n\nDescrição: {agent_config['description']}")
        
        # Instruções finais padrão
        prompt_parts.append("\n\nResponda de forma clara, útil e alinhada com sua especialização.")
        
        # Instruções de identificação do agente
        agent_name = agent_config.get("name", "Assistente IA")
        prompt_parts.append(f"\n\nREGRA CRÍTICA: SEMPRE inicie sua resposta identificando seu nome como um título markdown (## {agent_name}), seguido pela mensagem.")
        prompt_parts.append(f"\nExemplo de formato correto: ## {agent_name}")
        prompt_parts.append(f"\n[conteúdo da resposta]")
        prompt_parts.append(f"\n\nEXEMPLOS INCORRETOS (NÃO USE):")
        prompt_parts.append(f"\n{agent_name}")
        prompt_parts.append(f"\nResposta de {agent_name}")
        prompt_parts.append(f"\nComo {agent_name},")
        prompt_parts.append(f"\n\nNUNCA inicie sua resposta diretamente sem primeiro identificar seu nome como título markdown.")
        prompt_parts.append(f"\nNUNCA use prefixos como 'Resposta de [Nome]' - use APENAS o formato markdown ## Nome do Agente.")
        prompt_parts.append(f"\nNUNCA use apenas o nome sem o formato markdown ##.")
        prompt_parts.append(f"\nA primeira linha de cada resposta DEVE ser exatamente: ## {agent_name}")
        prompt_parts.append(f"\nNUNCA inclua no corpo da mensagem informações técnicas como transfer_task_to_member(member_id=...) ou tempos de execução.")
        
        return "".join(prompt_parts)
    
    @staticmethod
    def get_agent_temperature(agent_config: Dict) -> float:
        """Retorna a temperatura configurada para o agente"""
        return agent_config.get("temperature", 0.7)
    
    @staticmethod
    def get_agent_max_tokens(agent_config: Dict) -> int:
        """Retorna o máximo de tokens configurado para o agente"""
        return agent_config.get("maxTokens", 2000)
    
    @staticmethod
    def get_agent_knowledge_bases(agent_config: Dict) -> list:
        """Retorna as bases de conhecimento configuradas para o agente"""
        return agent_config.get("knowledgeBase", [])
    
    @staticmethod
    def get_agent_tools(agent_config: Dict) -> list:
        """Retorna as ferramentas configuradas para o agente"""
        return agent_config.get("tools", [])


# Função de conveniência para uso rápido
def load_and_build_agent_prompt(agent_id: str) -> tuple:
    """
    Carrega configurações do agente e constrói o prompt personalizado
    
    Args:
        agent_id: ID do agente
        
    Returns:
        Tuple (agent_config, system_prompt)
    """
    config = AgentConfigLoader.load_agent_config(agent_id)
    if config:
        prompt = AgentConfigLoader.build_agent_system_prompt(config)
        return config, prompt
    return None, "Você é um assistente de IA útil e informativo."