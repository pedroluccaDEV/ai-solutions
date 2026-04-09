#!/usr/bin/env python3
"""
Script para testar a navegação do sidebar de chat
Simula o frontend carregando o menu e verifica se o campo app_id está sendo retornado corretamente
"""

import sys
import os
import json
import logging
from typing import List, Dict, Any

# Adicionar o diretório pai ao path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config.init_db import get_mongo_client
from core.config.settings import settings
from dao.mongo.v1.chat_session_dao import ChatSessionDAO

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_user_sessions(user_id: str = "JJ9t5xjMIAdbsmM86U2oLHGDGu62"):
    """
    Testa as sessões do usuário específico e verifica o campo app_id
    """
    try:
        logger.info(f"=== INICIANDO TESTE DE SESSÕES DO USUÁRIO ===")
        logger.info(f"Usuário: {user_id}")
        
        # Inicializar conexão com MongoDB
        mongo_client = get_mongo_client()
        db = mongo_client.get_database(settings.MONGO_DB_NAME)
        session_dao = ChatSessionDAO(db)
        
        # Buscar todas as sessões do usuário
        logger.info(f"Buscando sessões do usuário {user_id}...")
        sessions = session_dao.list_sessions_by_user(user_id)
        
        logger.info(f"Total de sessões encontradas: {len(sessions)}")
        
        # Analisar cada sessão
        sessions_with_app_id = []
        sessions_without_app_id = []
        
        for i, session in enumerate(sessions):
            session_id = session.get("_id", "N/A")
            title = session.get("title", "Sem título")
            app_id = session.get("app_id")
            session_type = session.get("session_type")
            created_at = session.get("created_at")
            updated_at = session.get("updated_at")
            
            session_info = {
                "index": i + 1,
                "session_id": session_id,
                "title": title,
                "app_id": app_id,
                "session_type": session_type,
                "created_at": str(created_at) if created_at else "N/A",
                "updated_at": str(updated_at) if updated_at else "N/A",
                "should_open_playground": bool(app_id and app_id != "null" and app_id != "")
            }
            
            if session_info["should_open_playground"]:
                sessions_with_app_id.append(session_info)
            else:
                sessions_without_app_id.append(session_info)
            
            logger.info(f"Sessão {i+1}:")
            logger.info(f"  ID: {session_id}")
            logger.info(f"  Título: {title}")
            logger.info(f"  app_id: {app_id}")
            logger.info(f"  Tipo: {session_type}")
            logger.info(f"  Deve abrir Playground: {session_info['should_open_playground']}")
            logger.info(f"  URL esperada: {get_expected_url(session_info)}")
            logger.info("  ---")
        
        # Resumo
        logger.info(f"=== RESUMO DO TESTE ===")
        logger.info(f"Total de sessões: {len(sessions)}")
        logger.info(f"Sessões com app_id válido: {len(sessions_with_app_id)}")
        logger.info(f"Sessões sem app_id: {len(sessions_without_app_id)}")
        
        # Detalhes das sessões com app_id
        if sessions_with_app_id:
            logger.info("=== SESSÕES QUE DEVEM ABRIR PLAYGROUND ===")
            for session in sessions_with_app_id:
                logger.info(f"Sessão {session['index']}:")
                logger.info(f"  ID: {session['session_id']}")
                logger.info(f"  Título: {session['title']}")
                logger.info(f"  app_id: {session['app_id']}")
                logger.info(f"  URL esperada: {get_expected_url(session)}")
        
        # Detalhes das sessões sem app_id
        if sessions_without_app_id:
            logger.info("=== SESSÕES QUE DEVEM ABRIR CHAT NORMAL ===")
            for session in sessions_without_app_id:
                logger.info(f"Sessão {session['index']}:")
                logger.info(f"  ID: {session['session_id']}")
                logger.info(f"  Título: {session['title']}")
                logger.info(f"  URL esperada: {get_expected_url(session)}")
        
        # Verificar se há alguma sessão problemática
        problematic_sessions = []
        for session in sessions:
            app_id = session.get("app_id")
            if app_id and app_id != "null" and app_id != "":
                # Esta sessão deve abrir playground
                expected_url = f"http://localhost:5173/playground/app/chat/{app_id}"
                logger.info(f"✅ Sessão {session.get('_id')} deve abrir: {expected_url}")
            else:
                # Esta sessão deve abrir chat normal
                expected_url = f"http://localhost:5173/chat/c/{session.get('_id')}"
                logger.info(f"✅ Sessão {session.get('_id')} deve abrir: {expected_url}")
        
        logger.info("=== TESTE CONCLUÍDO ===")
        
        return {
            "total_sessions": len(sessions),
            "sessions_with_app_id": len(sessions_with_app_id),
            "sessions_without_app_id": len(sessions_without_app_id),
            "sessions_with_app_id_details": sessions_with_app_id,
            "sessions_without_app_id_details": sessions_without_app_id
        }
        
    except Exception as e:
        logger.error(f"Erro durante o teste: {e}", exc_info=True)
        return {"error": str(e)}

def get_expected_url(session_info: Dict[str, Any]) -> str:
    """
    Retorna a URL esperada baseada no app_id da sessão
    """
    if session_info["should_open_playground"]:
        return f"http://localhost:5173/playground/app/chat/{session_info['app_id']}"
    else:
        return f"http://localhost:5173/chat/c/{session_info['session_id']}"

def simulate_frontend_navigation_logic(sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Simula a lógica de navegação do frontend (ChatSidebar.jsx)
    """
    navigation_results = []
    
    for session in sessions:
        session_id = session.get("_id")
        app_id = session.get("app_id")
        
        # Lógica simplificada do frontend
        has_valid_app_id = app_id and isinstance(app_id, str) and app_id.strip() != ""
        
        if has_valid_app_id:
            target_url = f"http://localhost:5173/playground/app/chat/{app_id}"
            navigation_type = "PLAYGROUND_APP"
        else:
            target_url = f"http://localhost:5173/chat/c/{session_id}"
            navigation_type = "REGULAR_CHAT"
        
        navigation_results.append({
            "session_id": session_id,
            "session_title": session.get("title", "Sem título"),
            "app_id": app_id,
            "has_valid_app_id": has_valid_app_id,
            "target_url": target_url,
            "navigation_type": navigation_type
        })
    
    return {
        "navigation_results": navigation_results,
        "summary": {
            "total_sessions": len(sessions),
            "playground_sessions": len([r for r in navigation_results if r["navigation_type"] == "PLAYGROUND_APP"]),
            "regular_chat_sessions": len([r for r in navigation_results if r["navigation_type"] == "REGULAR_CHAT"])
        }
    }

if __name__ == "__main__":
    logger.info("=== INICIANDO SIMULAÇÃO DO FRONTEND CHAT SIDEBAR ===")
    
    # Testar com o usuário específico mencionado no problema
    user_id = "JJ9t5xjMIAdbsmM86U2oLHGDGu62"
    
    # Executar teste principal
    test_result = test_user_sessions(user_id)
    
    if "error" not in test_result:
        # Simular lógica do frontend
        mongo_client = get_mongo_client()
        db = mongo_client.get_database(settings.MONGO_DB_NAME)
        session_dao = ChatSessionDAO(db)
        sessions = session_dao.list_sessions_by_user(user_id)
        
        frontend_simulation = simulate_frontend_navigation_logic(sessions)
        
        logger.info("=== SIMULAÇÃO DO FRONTEND ===")
        logger.info(f"Resumo: {json.dumps(frontend_simulation['summary'], indent=2, ensure_ascii=False)}")
        
        for result in frontend_simulation["navigation_results"]:
            logger.info(f"Sessão: {result['session_title']}")
            logger.info(f"  ID: {result['session_id']}")
            logger.info(f"  app_id: {result['app_id']}")
            logger.info(f"  URL de destino: {result['target_url']}")
            logger.info(f"  Tipo: {result['navigation_type']}")
            logger.info("  ---")
        
        # Verificar se há alguma sessão problemática específica
        problematic_sessions = []
        for session in sessions:
            session_id = session.get("_id")
            app_id = session.get("app_id")
            
            # Verificar se há sessões com app_id que não estão sendo tratadas corretamente
            if app_id and app_id != "null" and app_id != "":
                # Verificar se esta é a sessão específica mencionada no problema
                if session_id == "7bd9e21d-5ed0-4fb5-9510-03f130556834":
                    problematic_sessions.append({
                        "session_id": session_id,
                        "app_id": app_id,
                        "expected_url": f"http://localhost:5173/playground/app/chat/{app_id}",
                        "current_behavior": "Abrindo chat normal em vez de playground",
                        "issue": "PROBLEMA IDENTIFICADO - Esta sessão deve abrir playground mas está abrindo chat normal"
                    })
        
        if problematic_sessions:
            logger.warning("=== PROBLEMAS IDENTIFICADOS ===")
            for problem in problematic_sessions:
                logger.warning(f"🚨 {problem['issue']}")
                logger.warning(f"   Sessão: {problem['session_id']}")
                logger.warning(f"   app_id: {problem['app_id']}")
                logger.warning(f"   URL esperada: {problem['expected_url']}")
                logger.warning(f"   Comportamento atual: {problem['current_behavior']}")
    
    logger.info("=== FIM DA SIMULAÇÃO ===")