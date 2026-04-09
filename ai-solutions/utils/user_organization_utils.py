from typing import Optional, Dict, Any
import logging
from core.config.database import get_postgres_db
from dao.postgres.v1.user_dao import UserDAO
from models.postgres.user_model import User

logger = logging.getLogger(__name__)


async def get_user_organization_info(firebase_uid: str) -> Optional[Dict[str, Any]]:
    """
    Busca informações de organização do usuário na tabela users.
    
    Args:
        firebase_uid: Firebase UID do usuário
        
    Returns:
        Dict com informações de organização ou None se não for organização
    """
    try:
        async for session in get_postgres_db():
            user = await UserDAO.get_by_firebase_uid(session, firebase_uid)
            
            if not user:
                logger.warning(f"Usuário com firebase_uid {firebase_uid} não encontrado")
                return None
            
            # Verificar se é conta de organização
            if user.account_type == 'organization':
                logger.info(f"Usuário {firebase_uid} é conta de organização. "
                           f"selected_organization_id: {user.selected_organization_id}, "
                           f"selected_project_id: {user.selected_project_id}")
                
                return {
                    "is_organization": True,
                    "selected_organization_id": user.selected_organization_id,
                    "selected_project_id": user.selected_project_id
                }
            else:
                logger.info(f"Usuário {firebase_uid} é conta pessoal (account_type: {user.account_type})")
                return {
                    "is_organization": False,
                    "selected_organization_id": None,
                    "selected_project_id": None
                }
                
    except Exception as e:
        logger.error(f"Erro ao buscar informações de organização do usuário {firebase_uid}: {e}")
        return None


async def get_organization_info_for_session(firebase_uid: str) -> Dict[str, Any]:
    """
    Obtém informações de organização para criação de sessão.
    
    Args:
        firebase_uid: Firebase UID do usuário
    
    Returns:
        Dict com org_id e project_id para a sessão
    """
    org_info = await get_user_organization_info(firebase_uid)
    
    if org_info and org_info["is_organization"]:
        # Garantir que os IDs sejam strings para compatibilidade com MongoDB
        org_id = str(org_info["selected_organization_id"]) if org_info["selected_organization_id"] else None
        project_id = str(org_info["selected_project_id"]) if org_info["selected_project_id"] else None
        
        logger.info(f"Organização detectada para sessão: org_id={org_id}, project_id={project_id}")
        
        return {
            "org_id": org_id,
            "project_id": project_id
        }
    else:
        logger.info(f"Conta pessoal detectada para sessão: firebase_uid={firebase_uid}")
        return {
            "org_id": None,
            "project_id": None
        }