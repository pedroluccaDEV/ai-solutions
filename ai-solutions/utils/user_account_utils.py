from typing import Dict, Any, Optional
from dao.postgres.v1.user_dao import UserDAO
from core.config.database import get_postgres_db


async def get_user_account_info(firebase_uid: str) -> Dict[str, Any]:
    """
    Obtém informações da conta do usuário da tabela users do PostgreSQL.
    
    Args:
        firebase_uid: UID do Firebase do usuário
        
    Returns:
        Dict com informações da conta do usuário:
        - account_type: 'personal' ou 'organization'
        - selected_organization_id: ID da organização selecionada (se account_type='organization')
        - selected_project_id: ID do projeto selecionado (se account_type='organization')
    """
    try:
        async for session in get_postgres_db():
            user = await UserDAO.get_by_firebase_uid(session, firebase_uid)
            if not user:
                return {
                    "account_type": "personal",
                    "selected_organization_id": None,
                    "selected_project_id": None
                }
            
            return {
                "account_type": user.account_type or "personal",
                "selected_organization_id": user.selected_organization_id,
                "selected_project_id": user.selected_project_id
            }
            
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao buscar informações da conta do usuário {firebase_uid}: {e}")
        
        # Fallback para conta personal em caso de erro
        return {
            "account_type": "personal",
            "selected_organization_id": None,
            "selected_project_id": None
        }


async def get_session_filter_criteria(firebase_uid: str) -> Dict[str, Any]:
    """
    Obtém critérios de filtro para sessões baseado no tipo de conta do usuário.
    
    Args:
        firebase_uid: UID do Firebase do usuário
    
    Returns:
        Dict com critérios de filtro para MongoDB:
        - Para conta personal: {"org_id": None, "project_id": None}
        - Para conta organização: {"org_id": selected_organization_id, "project_id": selected_project_id}
    """
    user_info = await get_user_account_info(firebase_uid)
    
    if user_info["account_type"] == "organization":
        # Para conta organização: filtrar por org_id e project_id específicos
        # Converter para string para compatibilidade com MongoDB (onde são salvos como strings)
        org_id = str(user_info["selected_organization_id"]) if user_info["selected_organization_id"] else None
        project_id = str(user_info["selected_project_id"]) if user_info["selected_project_id"] else None
        
        return {
            "org_id": org_id,
            "project_id": project_id
        }
    else:
        # Para conta personal: filtrar apenas sessões sem org_id e project_id
        return {
            "org_id": None,
            "project_id": None
        }