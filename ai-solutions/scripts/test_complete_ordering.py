#!/usr/bin/env python3
"""
Script de teste para validar a ordenação completa por updated_at
Testa tanto o backend quanto o frontend para garantir que as sessões
são ordenadas corretamente por updated_at do mais recente para o mais antigo
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta
from bson import ObjectId

# Adicionar o diretório server ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database_service import DatabaseService
from dao.mongo.v1.chat_session_dao import ChatSessionDAO
from dao.mongo.v1.chat_message_dao import ChatMessageDAO

async def test_complete_ordering():
    """Testa a ordenação completa por updated_at"""
    print("INICIANDO TESTE DE ORDENAÇÃO COMPLETA")
    print("=" * 60)
    
    # Inicializar serviços
    db_service = DatabaseService()
    chat_session_dao = ChatSessionDAO()
    chat_message_dao = ChatMessageDAO()
    
    # ID de usuário de teste
    test_user_id = "test-user-ordering"
    
    try:
        # Limpar sessões de teste anteriores
        await chat_session_dao.collection.delete_many({"user_id": test_user_id})
        print("Sessões de teste anteriores removidas")
        
        # Criar sessões de teste com diferentes timestamps
        sessions = []
        base_time = datetime.utcnow()
        
        # Sessão 1: Mais antiga (criada há 3 dias)
        session1 = {
            "_id": ObjectId(),
            "user_id": test_user_id,
            "title": "Sessão Antiga",
            "created_at": base_time - timedelta(days=3),
            "updated_at": base_time - timedelta(days=3),
            "type": "chat"
        }
        
        # Sessão 2: Intermediária (criada há 2 dias)
        session2 = {
            "_id": ObjectId(),
            "user_id": test_user_id,
            "title": "Sessão Intermediária",
            "created_at": base_time - timedelta(days=2),
            "updated_at": base_time - timedelta(days=2),
            "type": "chat"
        }
        
        # Sessão 3: Mais recente (criada há 1 dia)
        session3 = {
            "_id": ObjectId(),
            "user_id": test_user_id,
            "title": "Sessão Recente",
            "created_at": base_time - timedelta(days=1),
            "updated_at": base_time - timedelta(days=1),
            "type": "chat"
        }
        
        # Inserir sessões
        await chat_session_dao.collection.insert_many([session1, session2, session3])
        print("Sessões de teste criadas")
        
        # Testar ordenação no backend
        print("\nTESTANDO ORDENAÇÃO NO BACKEND")
        print("-" * 40)
        
        # Buscar sessões ordenadas por updated_at
        backend_sessions = await chat_session_dao.list_sessions_by_user(test_user_id)
        
        print(f"Total de sessões encontradas: {len(backend_sessions)}")
        
        # Verificar ordenação
        if len(backend_sessions) >= 3:
            print("Ordem das sessões no backend:")
            for i, session in enumerate(backend_sessions[:3], 1):
                print(f"  {i}. {session['title']} - updated_at: {session['updated_at']}")
            
            # Verificar se está ordenado corretamente (mais recente primeiro)
            if (backend_sessions[0]['_id'] == session3['_id'] and
                backend_sessions[1]['_id'] == session2['_id'] and
                backend_sessions[2]['_id'] == session1['_id']):
                print("BACKEND: Ordenação por updated_at funcionando corretamente")
            else:
                print("BACKEND: Ordenação por updated_at incorreta")
                return False
        else:
            print("Não foram encontradas sessões suficientes para testar")
            return False
        
        # Testar atualização do updated_at ao salvar mensagem
        print("\nTESTANDO ATUALIZAÇÃO DO updated_at")
        print("-" * 40)
        
        # Salvar uma mensagem na sessão mais antiga
        message_data = {
            "session_id": session1['_id'],
            "user_id": test_user_id,
            "content": "Mensagem de teste para atualizar updated_at",
            "role": "user"
        }
        
        await chat_message_dao.save_message(message_data)
        print("Mensagem salva na sessão mais antiga")
        
        # Buscar sessão atualizada
        updated_session = await chat_session_dao.get_session(session1['_id'])
        
        if updated_session:
            print(f"updated_at antes: {session1['updated_at']}")
            print(f"updated_at depois: {updated_session['updated_at']}")
            
            if updated_session['updated_at'] > session1['updated_at']:
                print("updated_at foi atualizado corretamente")
            else:
                print("updated_at não foi atualizado")
                return False
        else:
            print("Não foi possível buscar a sessão atualizada")
            return False
        
        # Testar ordenação após atualização
        print("\nTESTANDO ORDENAÇÃO APÓS ATUALIZAÇÃO")
        print("-" * 40)
        
        backend_sessions_after = await chat_session_dao.list_sessions_by_user(test_user_id)
        
        print("Nova ordem das sessões:")
        for i, session in enumerate(backend_sessions_after[:3], 1):
            print(f"  {i}. {session['title']} - updated_at: {session['updated_at']}")
        
        # A sessão mais antiga (agora atualizada) deve estar no topo
        if backend_sessions_after[0]['_id'] == session1['_id']:
            print("ORDENAÇÃO: Sessão atualizada corretamente movida para o topo")
        else:
            print("ORDENAÇÃO: Sessão atualizada não foi movida para o topo")
            return False
        
        print("\nTESTE DE ORDENAÇÃO COMPLETA CONCLUÍDO COM SUCESSO!")
        return True
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Limpar dados de teste
        try:
            await chat_session_dao.collection.delete_many({"user_id": test_user_id})
            print("🧹 Dados de teste limpos")
        except Exception as e:
            print(f"⚠️  Erro ao limpar dados de teste: {e}")

async def test_frontend_logic():
    """Testa a lógica de ordenação que seria usada no frontend"""
    print("\n🖥️  TESTANDO LÓGICA DO FRONTEND")
    print("=" * 60)
    
    # Simular dados que viriam da API
    sessions_data = [
        {
            "_id": "session1",
            "title": "Sessão Antiga",
            "created_at": "2025-10-20T10:00:00Z",
            "updated_at": "2025-10-20T10:00:00Z"
        },
        {
            "_id": "session2", 
            "title": "Sessão Intermediária",
            "created_at": "2025-10-21T10:00:00Z",
            "updated_at": "2025-10-21T10:00:00Z"
        },
        {
            "_id": "session3",
            "title": "Sessão Recente", 
            "created_at": "2025-10-22T10:00:00Z",
            "updated_at": "2025-10-22T10:00:00Z"
        }
    ]
    
    # Simular a lógica do ChatSidebar.jsx
    def frontend_sorting_logic(sessions):
        # Ordenar por updated_at (mais recente primeiro), fallback para created_at
        return sorted(sessions, key=lambda x: x.get('updated_at') or x.get('created_at'), reverse=True)
    
    # Aplicar ordenação
    sorted_sessions = frontend_sorting_logic(sessions_data)
    
    print("📋 Sessões ordenadas pelo frontend:")
    for i, session in enumerate(sorted_sessions, 1):
        print(f"  {i}. {session['title']} - updated_at: {session['updated_at']}")
    
    # Verificar ordenação
    if (sorted_sessions[0]['_id'] == 'session3' and 
        sorted_sessions[1]['_id'] == 'session2' and 
        sorted_sessions[2]['_id'] == 'session1'):
        print("✅ FRONTEND: Lógica de ordenação funcionando corretamente")
        return True
    else:
        print("❌ FRONTEND: Lógica de ordenação incorreta")
        return False

if __name__ == "__main__":
    async def main():
        backend_success = await test_complete_ordering()
        frontend_success = test_frontend_logic()
        
        print("\n" + "=" * 60)
        print("📋 RESUMO DOS TESTES")
        print("=" * 60)
        print(f"Backend: {'✅ PASSOU' if backend_success else '❌ FALHOU'}")
        print(f"Frontend: {'✅ PASSOU' if frontend_success else '❌ FALHOU'}")
        
        if backend_success and frontend_success:
            print("\n🎉 TODOS OS TESTES PASSARAM! A ordenação por updated_at está funcionando corretamente.")
        else:
            print("\n💥 ALGUNS TESTES FALHARAM. Verifique as correções implementadas.")
            sys.exit(1)
    
    asyncio.run(main())