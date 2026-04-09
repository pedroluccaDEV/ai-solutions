import os
import asyncio
from loguru import logger
from utils.team.team_flow import execute_team_flow
from core.config.database import get_mongo_db

async def execute_playground_team(team_id: str, prompt: str, user_jwt: str, user_id: str):
    """
    Executa um time completo no playground
    """
    try:
        logger.info(f"[PLAYGROUND_TEAM] Iniciando execução do time {team_id}")
        
        # Obter conexão com o banco
        db = get_mongo_db()
        
        # Montar o time completo
        team = await execute_team_flow(team_id, user_jwt, user_id, db)
        
        if not team:
            raise ValueError(f"Time {team_id} não pôde ser montado")
        
        logger.info(f"[PLAYGROUND_TEAM] Time montado: {team.name} com {len(team.members)} membros")
        
        # Executar o time com o prompt do usuário
        logger.info(f"[PLAYGROUND_TEAM] Executando time com prompt: {prompt[:100]}...")
        
        # Executar o time (usando o modo apropriado)
        if team.mode == "collaborate":
            # Modo colaborativo - todos os agentes trabalham juntos
            result = await team.run(prompt)
        elif team.mode == "coordinate":
            # Modo coordenado - líder coordena os membros
            result = await team.run(prompt)
        elif team.mode == "route":
            # Modo roteamento - direciona para o agente apropriado
            result = await team.run(prompt)
        else:
            # Modo padrão
            result = await team.run(prompt)
        
        logger.info("[PLAYGROUND_TEAM] Time executado com sucesso")
        
        # Extrair a resposta - priorizar respostas dos membros
        team_response = ""
        
        # Primeiro verificar se há respostas dos membros
        if hasattr(result, 'member_responses') and result.member_responses:
            for member_response in result.member_responses:
                if hasattr(member_response, 'content') and member_response.content:
                    team_response = member_response.content
                    break
        
        # Se não houver respostas de membros, usar o conteúdo do team
        if not team_response:
            if hasattr(result, 'content'):
                team_response = result.content
            elif isinstance(result, dict) and 'content' in result:
                team_response = result['content']
            else:
                team_response = str(result)
        
        logger.debug(f"[PLAYGROUND_TEAM] Resposta do time: {team_response[:200]}...")
        
        return {
            "team_result": team_response,
            "team_name": team.name,
            "team_mode": team.mode,
            "member_count": len(team.members)
        }
        
    except Exception as e:
        logger.error(f"[PLAYGROUND_TEAM] Erro na execução do time: {e}")
        logger.debug(f"[PLAYGROUND_TEAM] Traceback: {e.__traceback__}")
        raise