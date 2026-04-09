"""
Script para testar a persistência de sessões e mensagens no chat de aplicativos
"""
import sys
import os
import asyncio
from pathlib import Path

# Adicionar o diretório server ao path
server_root = Path(__file__).parent.parent
sys.path.insert(0, str(server_root))

from core.config.database import get_mongo_db, get_postgres_db
from dao.mongo.v1.chat_session_dao import ChatSessionDAO
from dao.mongo.v1.chat_message_dao import ChatMessageDAO

async def test_chat_persistence():
    """Testa a persistência de sessões e mensagens"""
    
    print("=== TESTE DE PERSISTÊNCIA DE CHAT ===")
    
    try:
        # Obter conexões com os bancos
        mongo_db = get_mongo_db()
        postgres_db = get_postgres_db()
        
        # Testar DAOs
        session_dao = ChatSessionDAO(mongo_db)
        message_dao = ChatMessageDAO(mongo_db, session_dao=session_dao)
        
        # Dados de teste
        test_user_id = "test-user-123"
        test_app_id = "a13f33b5-055c-4d3f-a81c-0ef123cd65f7"
        test_schema_name = "cac"  # Schema esperado para o app_id
        
        print(f"Usuário de teste: {test_user_id}")
        print(f"App ID de teste: {test_app_id}")
        print(f"Schema esperado: {test_schema_name}")
        
        # 1. Testar criação de sessão
        print("\n1. Testando criação de sessão...")
        session_id = session_dao.create_session(
            user_id=test_user_id,
            agent_id=test_app_id,
            title=f"Chat - {test_schema_name}",
            session_type=test_schema_name
        )
        print(f"Sessão criada: {session_id}")
        
        # 2. Testar busca de sessão
        print("\n2. Testando busca de sessão...")
        session = session_dao.get_session_by_id(session_id)
        if session:
            print(f"Sessão encontrada: {session['_id']}")
            print(f"Tipo da sessão: {session.get('session_type', 'N/A')}")
            print(f"Título: {session.get('title', 'N/A')}")
        else:
            print("ERRO: Sessão não encontrada")
            return False
        
        # 3. Testar salvamento de mensagem
        print("\n3. Testando salvamento de mensagem...")
        test_message = "Olá, esta é uma mensagem de teste"
        message_id = message_dao.save_message(
            session_id=session_id,
            sender="user",
            content=test_message,
            app_id=test_app_id
        )
        print(f"Mensagem salva: {message_id}")
        
        # 4. Testar salvamento de resposta
        print("\n4. Testando salvamento de resposta...")
        test_response = "Olá! Esta é uma resposta de teste do assistente"
        response_id = message_dao.save_message(
            session_id=session_id,
            sender="assistant",
            content=test_response,
            app_id=test_app_id
        )
        print(f"Resposta salva: {response_id}")
        
        # 5. Testar listagem de mensagens
        print("\n5. Testando listagem de mensagens...")
        messages = message_dao.list_messages_by_session(session_id)
        print(f"Total de mensagens na sessão: {len(messages)}")
        for i, msg in enumerate(messages):
            print(f"  {i+1}. [{msg['sender']}] {msg['content'][:50]}...")
        
        # 6. Testar busca de sessão por agente e usuário
        print("\n6. Testando busca de sessão por agente e usuário...")
        existing_session = session_dao.get_session_by_agent_and_user(test_app_id, test_user_id)
        if existing_session:
            print(f"Sessão encontrada: {existing_session['_id']}")
            print(f"Tipo: {existing_session.get('session_type', 'N/A')}")
        else:
            print("ERRO: Sessão não encontrada por agente e usuário")
            return False
        
        # 7. Testar listagem de sessões por tipo
        print("\n7. Testando listagem de sessões por tipo...")
        sessions_by_type = session_dao.list_sessions_by_user_and_type(
            test_user_id, 
            session_type=test_schema_name
        )
        print(f"Sessões encontradas com tipo '{test_schema_name}': {len(sessions_by_type)}")
        for i, sess in enumerate(sessions_by_type):
            print(f"  {i+1}. {sess['_id']} - {sess.get('title', 'N/A')}")
        
        # 8. Testar contagem de sessões
        print("\n8. Testando contagem de sessões...")
        session_count = session_dao.count_sessions_by_user(test_user_id, test_schema_name)
        print(f"Total de sessões do usuário com tipo '{test_schema_name}': {session_count}")
        
        print("\n=== TESTE CONCLUÍDO COM SUCESSO ===")
        return True
        
    except Exception as e:
        print(f"ERRO durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_existing_app_sessions():
    """Testa sessões existentes para o app específico"""
    
    print("\n=== TESTE DE SESSÕES EXISTENTES DO APP ===")
    
    try:
        mongo_db = get_mongo_db()
        session_dao = ChatSessionDAO(mongo_db)
        
        # Buscar todas as sessões do app específico
        app_id = "a13f33b5-055c-4d3f-a81c-0ef123cd65f7"
        
        # Buscar sessões por agent_id (que é o app_id)
        sessions = session_dao.collection.find({"agent_id": app_id})
        sessions_list = list(sessions)
        
        print(f"Sessões encontradas para o app {app_id}: {len(sessions_list)}")
        
        for i, session in enumerate(sessions_list):
            print(f"\nSessão {i+1}:")
            print(f"  ID: {session['_id']}")
            print(f"  Usuário: {session.get('user_id', 'N/A')}")
            print(f"  Tipo: {session.get('session_type', 'N/A')}")
            print(f"  Título: {session.get('title', 'N/A')}")
            print(f"  Criada em: {session.get('created_at', 'N/A')}")
            
            # Buscar mensagens desta sessão
            message_dao = ChatMessageDAO(mongo_db, session_dao=ChatSessionDAO(mongo_db))
            messages = message_dao.list_messages_by_session(str(session['_id']))
            print(f"  Mensagens: {len(messages)}")
            
            for j, msg in enumerate(messages[:3]):  # Mostrar apenas as 3 primeiras
                print(f"    {j+1}. [{msg['sender']}] {msg['content'][:50]}...")
        
        return True
        
    except Exception as e:
        print(f"ERRO ao buscar sessões existentes: {e}")
        return False

if __name__ == "__main__":
    # Executar testes
    success1 = asyncio.run(test_chat_persistence())
    success2 = asyncio.run(test_existing_app_sessions())
    
    if success1 and success2:
        print("\nSUCESSO: TODOS OS TESTES PASSARAM!")
    else:
        print("\nERRO: ALGUNS TESTES FALHARAM!")
        sys.exit(1)