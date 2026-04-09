#!/usr/bin/env python3
"""
Script simples para testar a ordenação de sessões
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from core.config.database import get_mongo_db
from dao.mongo.v1.chat_session_dao import ChatSessionDAO

def test_simple_ordering():
    """Testa se as sessões estão sendo ordenadas corretamente por updated_at"""
    
    print("TESTANDO ORDENAÇÃO SIMPLES DE SESSÕES")
    print("=" * 50)
    
    # Conectar ao banco
    db = get_mongo_db()
    session_dao = ChatSessionDAO(db)
    
    # Usuário de teste
    test_user_id = "test_user_simple"
    
    # Limpar sessões antigas do usuário de teste
    sessions = session_dao.list_sessions_by_user(test_user_id)
    for session in sessions:
        session_dao.delete_session(session["_id"])
    
    print(f"Criando sessões de teste para usuário: {test_user_id}")
    
    # Criar 3 sessões com diferentes timestamps
    now = datetime.utcnow()
    
    # Sessão 1: Atualizada há 1 hora
    session1_id = session_dao.create_session(
        user_id=test_user_id,
        title="Sessão 1 - Atualizada há 1 hora",
        session_type="test"
    )
    session_dao.update_session(session1_id, {
        "updated_at": now - timedelta(hours=1)
    })
    
    # Sessão 2: Atualizada há 2 horas
    session2_id = session_dao.create_session(
        user_id=test_user_id,
        title="Sessão 2 - Atualizada há 2 horas",
        session_type="test"
    )
    session_dao.update_session(session2_id, {
        "updated_at": now - timedelta(hours=2)
    })
    
    # Sessão 3: Atualizada agora
    session3_id = session_dao.create_session(
        user_id=test_user_id,
        title="Sessão 3 - Atualizada agora",
        session_type="test"
    )
    
    print("Sessões criadas com diferentes updated_at")
    
    # Testar ordenação
    print("\nTESTANDO ORDENAÇÃO:")
    
    # Buscar sessões ordenadas
    sessions = session_dao.list_sessions_by_user(test_user_id)
    
    print(f"Total de sessões encontradas: {len(sessions)}")
    
    if len(sessions) != 3:
        print("ERRO: Número incorreto de sessões encontradas")
        return False
    
    # Verificar ordenação por updated_at (deveria ser: 3, 1, 2)
    expected_order = [session3_id, session1_id, session2_id]
    actual_order = [s["_id"] for s in sessions]
    
    print(f"Ordem esperada (por updated_at): {expected_order}")
    print(f"Ordem atual: {actual_order}")
    
    if actual_order == expected_order:
        print("ORDENAÇÃO CORRETA: Sessões ordenadas por updated_at!")
        
        # Mostrar detalhes
        print("\nDETALHES DAS SESSÕES:")
        for i, session in enumerate(sessions, 1):
            print(f"  {i}. {session['title']}")
            print(f"     ID: {session['_id']}")
            print(f"     Criada: {session.get('created_at')}")
            print(f"     Atualizada: {session.get('updated_at')}")
            print()
            
        return True
    else:
        print("ORDENAÇÃO INCORRETA: Sessões não estão ordenadas por updated_at!")
        
        # Mostrar detalhes
        print("\nDETALHES DAS SESSÕES:")
        for i, session in enumerate(sessions, 1):
            print(f"  {i}. {session['title']}")
            print(f"     ID: {session['_id']}")
            print(f"     Criada: {session.get('created_at')}")
            print(f"     Atualizada: {session.get('updated_at')}")
            print()
            
        return False

if __name__ == "__main__":
    try:
        result = test_simple_ordering()
        
        print("\n" + "=" * 50)
        print("RESUMO DO TESTE:")
        print(f"  - ChatSessionDAO: {'PASS' if result else 'FAIL'}")
        
        if result:
            print("\nTODOS OS TESTES PASSARAM! A ordenação está correta.")
        else:
            print("\nTESTE FALHOU! Verifique a implementação.")
            
    except Exception as e:
        print(f"ERRO durante os testes: {e}")
        import traceback
        traceback.print_exc()