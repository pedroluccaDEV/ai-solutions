"""
Script de teste para verificar se o campo updated_at da sessão é atualizado
quando uma mensagem é salva na coleção chat_messages.
"""
import sys
import os
from datetime import datetime, timedelta

# Adicionar path para importar módulos do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config.database import get_mongo_db
from dao.mongo.v1.chat_session_dao import ChatSessionDAO
from dao.mongo.v1.chat_message_dao import ChatMessageDAO

def test_updated_at_update():
    """Testa se o campo updated_at da sessão é atualizado ao salvar mensagem"""
    try:
        print("=== INICIANDO TESTE DE ATUALIZAÇÃO DO updated_at ===")
        
        # Obter conexão com MongoDB
        mongo_db = get_mongo_db()
        
        # Criar DAOs
        session_dao = ChatSessionDAO(mongo_db)
        message_dao = ChatMessageDAO(mongo_db, session_dao=session_dao)
        
        # Criar uma sessão de teste
        print("Criando sessão de teste...")
        session_id = session_dao.create_session(
            user_id="test_user_123",
            title="Sessão de Teste",
            session_type="test"
        )
        print(f"Sessão criada: {session_id}")
        
        # Obter a sessão criada para verificar o updated_at inicial
        session = session_dao.get_session_by_id(session_id)
        initial_updated_at = session.get("updated_at")
        print(f"updated_at inicial: {initial_updated_at}")
        
        # Aguardar 1 segundo para garantir diferença de tempo
        import time
        time.sleep(1)
        
        # Salvar uma mensagem na sessão
        print("Salvando mensagem de teste...")
        message_id = message_dao.save_message(
            session_id=session_id,
            sender="user",
            content="Esta é uma mensagem de teste para verificar a atualização do updated_at",
            user_id="test_user_123"
        )
        print(f"Mensagem salva: {message_id}")
        
        # Obter a sessão novamente para verificar se o updated_at foi atualizado
        updated_session = session_dao.get_session_by_id(session_id)
        final_updated_at = updated_session.get("updated_at")
        print(f"updated_at final: {final_updated_at}")
        
        # Verificar se o updated_at foi atualizado
        if initial_updated_at and final_updated_at:
            time_diff = final_updated_at - initial_updated_at
            print(f"Diferença de tempo: {time_diff.total_seconds():.2f} segundos")
            
            if time_diff.total_seconds() > 0:
                print("SUCESSO: O campo updated_at foi atualizado corretamente!")
                return True
            else:
                print("ERRO: O campo updated_at não foi atualizado")
                return False
        else:
            print("ERRO: Não foi possível obter os timestamps")
            return False
            
    except Exception as e:
        print(f"ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Limpeza: remover sessão e mensagens de teste
        try:
            if 'session_id' in locals():
                # Remover mensagens da sessão
                message_dao.delete_messages_by_session(session_id)
                # Remover sessão
                session_dao.delete_session(session_id)
                print("Dados de teste removidos")
        except Exception as cleanup_error:
            print(f"Aviso: Erro na limpeza: {cleanup_error}")

def test_multiple_messages():
    """Testa se o updated_at é atualizado para múltiplas mensagens"""
    try:
        print("\n=== TESTANDO MULTIPLAS MENSAGENS ===")
        
        # Obter conexão com MongoDB
        mongo_db = get_mongo_db()
        
        # Criar DAOs
        session_dao = ChatSessionDAO(mongo_db)
        message_dao = ChatMessageDAO(mongo_db, session_dao=session_dao)
        
        # Criar uma sessão de teste
        session_id = session_dao.create_session(
            user_id="test_user_456",
            title="Sessao de Teste Multiplas Mensagens",
            session_type="test"
        )
        print(f"Sessão criada: {session_id}")
        
        # Salvar 3 mensagens e verificar se o updated_at é atualizado a cada uma
        timestamps = []
        
        for i in range(3):
            # Obter updated_at atual
            session = session_dao.get_session_by_id(session_id)
            current_updated_at = session.get("updated_at")
            timestamps.append(current_updated_at)
            
            # Aguardar um pouco
            import time
            time.sleep(0.5)
            
            # Salvar mensagem
            message_id = message_dao.save_message(
                session_id=session_id,
                sender="user",
                content=f"Mensagem de teste {i+1}",
                user_id="test_user_456"
            )
            print(f"Mensagem {i+1} salva: {message_id}")
            
            # Obter updated_at após salvar mensagem
            updated_session = session_dao.get_session_by_id(session_id)
            new_updated_at = updated_session.get("updated_at")
            timestamps.append(new_updated_at)
            
            # Verificar se foi atualizado
            if current_updated_at and new_updated_at:
                time_diff = new_updated_at - current_updated_at
                if time_diff.total_seconds() > 0:
                    print(f"SUCESSO: Mensagem {i+1}: updated_at atualizado (+{time_diff.total_seconds():.2f}s)")
                else:
                    print(f"ERRO: Mensagem {i+1}: updated_at NAO atualizado")
            else:
                print(f"ERRO: Mensagem {i+1}: Nao foi possivel verificar timestamps")
        
        # Verificar se todos os timestamps são crescentes
        is_increasing = all(timestamps[i] < timestamps[i+1] for i in range(len(timestamps)-1))
        if is_increasing:
            print("SUCESSO: Todos os timestamps sao crescentes!")
        else:
            print("ERRO: Os timestamps nao sao consistentemente crescentes")
            
        return is_increasing
        
    except Exception as e:
        print(f"ERRO NO TESTE DE MULTIPLAS MENSAGENS: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Limpeza
        try:
            if 'session_id' in locals():
                message_dao.delete_messages_by_session(session_id)
                session_dao.delete_session(session_id)
                print("Dados de teste removidos")
        except Exception as cleanup_error:
            print(f"Aviso: Erro na limpeza: {cleanup_error}")

if __name__ == "__main__":
    print("Executando testes de atualização do campo updated_at...")
    
    # Executar teste simples
    test1_passed = test_updated_at_update()
    
    # Executar teste de múltiplas mensagens
    test2_passed = test_multiple_messages()
    
    # Resultado final
    print("\n=== RESULTADO FINAL ===")
    if test1_passed and test2_passed:
        print("SUCESSO: TODOS OS TESTES FORAM APROVADOS!")
        print("A implementação está funcionando corretamente.")
    else:
        print("AVISO: ALGUNS TESTES FALHARAM!")
        print("Verifique a implementação do método save_message no ChatMessageDAO.")