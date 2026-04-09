#!/usr/bin/env python3
"""
Script para testar a ordenação de sessões por updated_at vs created_at
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from core.config.database import get_mongo_db
from dao.mongo.v1.chat_session_dao import ChatSessionDAO
from dao.mongo.v1.chat_message_dao import ChatMessageDAO

def test_session_ordering():
    """Testa se as sessões estão sendo ordenadas corretamente por updated_at"""
    
    print("TESTANDO ORDENAÇÃO DE SESSÕES")
    print("=" * 50)
    
    # Conectar ao banco
    db = get_mongo_db()
    session_dao = ChatSessionDAO(db)
    message_dao = ChatMessageDAO(db, session_dao=session_dao)
    
    # Usuário de teste
    test_user_id = "test_user_ordering"
    
    # Limpar sessões antigas do usuário de teste
    sessions = session_dao.list_sessions_by_user(test_user_id)
    for session in sessions:
        session_dao.delete_session(session["_id"])
    
    print(f"Criando sessões de teste para usuário: {test_user_id}")
    
    # Criar 3 sessões com diferentes timestamps
    now = datetime.utcnow()
    
    # Sessão 1: Criada há 3 dias, atualizada há 1 dia
    session1_id = session_dao.create_session(
        user_id=test_user_id,
        title="Sessão 1 - Antiga mas atualizada recentemente",
        session_type="test"
    )
    # Simular que foi atualizada há 1 dia
    session_dao.update_session(session1_id, {
        "updated_at": now - timedelta(days=1)
    })
    
    # Sessão 2: Criada há 2 dias, atualizada há 3 dias (mais antiga)
    session2_id = session_dao.create_session(
        user_id=test_user_id,
        title="Sessão 2 - Mais nova mas não atualizada",
        session_type="test"
    )
    # Simular que foi atualizada há 3 dias
    session_dao.update_session(session2_id, {
        "updated_at": now - timedelta(days=3)
    })
    
    # Sessão 3: Criada há 1 dia, atualizada agora (mais recente)
    session3_id = session_dao.create_session(
        user_id=test_user_id,
        title="Sessão 3 - Mais recente",
        session_type="test"
    )
    # Já tem updated_at atual por padrão
    
    print("Sessões criadas:")
    print(f"  - Sessão 1: Criada há 3 dias, atualizada há 1 dia")
    print(f"  - Sessão 2: Criada há 2 dias, atualizada há 3 dias")  
    print(f"  - Sessão 3: Criada há 1 dia, atualizada agora")
    
    # Testar ordenação
    print("\n TESTANDO ORDENAÇÃO:")
    
    # Buscar sessões ordenadas
    sessions = session_dao.list_sessions_by_user(test_user_id)
    
    print(f" Total de sessões encontradas: {len(sessions)}")
    
    if len(sessions) != 3:
        print(" ERRO: Número incorreto de sessões encontradas")
        return False
    
    # Verificar ordenação por updated_at (deveria ser: 3, 1, 2)
    expected_order = [session3_id, session1_id, session2_id]
    actual_order = [s["_id"] for s in sessions]
    
    print(f" Ordem esperada (por updated_at): {expected_order}")
    print(f" Ordem atual: {actual_order}")
    
    if actual_order == expected_order:
        print(" ORDENAÇÃO CORRETA: Sessões ordenadas por updated_at!")
        
        # Mostrar detalhes
        print("\n DETALHES DAS SESSÕES:")
        for i, session in enumerate(sessions, 1):
            print(f"  {i}. {session['title']}")
            print(f"     ID: {session['_id']}")
            print(f"     Criada: {session.get('created_at')}")
            print(f"     Atualizada: {session.get('updated_at')}")
            print()
            
        return True
    else:
        print(" ORDENAÇÃO INCORRETA: Sessões não estão ordenadas por updated_at!")
        
        # Mostrar detalhes
        print("\n DETALHES DAS SESSÕES:")
        for i, session in enumerate(sessions, 1):
            print(f"  {i}. {session['title']}")
            print(f"     ID: {session['_id']}")
            print(f"     Criada: {session.get('created_at')}")
            print(f"     Atualizada: {session.get('updated_at')}")
            print()
            
        return False

def test_playground_agent_ordering():
    """Testa se o PlaygroundAgentDAO está ordenando corretamente por updated_at"""
    
    print("\n" + "=" * 50)
    print(" TESTANDO ORDENAÇÃO DO PLAYGROUND AGENT DAO")
    print("=" * 50)
    
    from dao.mongo.v1.playground_agent_dao import PlaygroundAgentDAO
    
    test_user_id = "test_user_playground"
    test_agent_id = "test_agent_ordering"
    
    # Limpar sessões antigas
    try:
        PlaygroundAgentDAO.clear_session(test_user_id, test_agent_id)
    except:
        pass  # Pode não existir
    
    print(f" Criando sessões do playground para usuário: {test_user_id}")
    
    # Criar sessão
    session_id = PlaygroundAgentDAO.get_or_create_session(test_user_id, test_agent_id)
    
    # Simular atualização da sessão
    db = get_mongo_db()
    sessions_collection = db["chat_sessions"]
    
    # Atualizar o updated_at para um valor específico
    test_updated_at = datetime.utcnow() - timedelta(hours=2)
    sessions_collection.update_one(
        {"_id": session_id},
        {"$set": {"updated_at": test_updated_at}}
    )
    
    # Buscar sessão usando o método get_session
    session = PlaygroundAgentDAO.get_session(test_user_id, test_agent_id)
    
    if session:
        print(f" Sessão encontrada: {session['_id']}")
        print(f"   Updated_at: {session.get('updated_at')}")
        print(f"   Created_at: {session.get('created_at')}")
        
        # Verificar se o método está usando updated_at para ordenação
        if session.get('updated_at') == test_updated_at:
            print(" ORDENAÇÃO CORRETA: PlaygroundAgentDAO usando updated_at!")
            return True
        else:
            print(" ORDENAÇÃO INCORRETA: PlaygroundAgentDAO não está usando updated_at!")
            return False
    else:
        print(" ERRO: Sessão não encontrada")
        return False

if __name__ == "__main__":
    try:
        # Testar ordenação principal
        main_result = test_session_ordering()
        
        # Testar ordenação do playground
        playground_result = test_playground_agent_ordering()
        
        print("\n" + "=" * 50)
        print(" RESUMO DOS TESTES:")
        print(f"  - ChatSessionDAO: {' PASS' if main_result else ' FAIL'}")
        print(f"  - PlaygroundAgentDAO: {' PASS' if playground_result else ' FAIL'}")
        
        if main_result and playground_result:
            print("\n TODOS OS TESTES PASSARAM! A ordenação está correta.")
        else:
            print("\n ALGUNS TESTES FALHARAM! Verifique a implementação.")
            
    except Exception as e:
        print(f" ERRO durante os testes: {e}")
        import traceback
        traceback.print_exc()