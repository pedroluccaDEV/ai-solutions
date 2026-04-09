"""
Script para adicionar persistência de sessões e mensagens ao chat de aplicativos
"""
import sys
import os
from pathlib import Path

# Adicionar o diretório server ao path
server_root = Path(__file__).parent.parent
sys.path.insert(0, str(server_root))

def add_persistence_to_app_chat():
    """Adiciona persistência de sessões e mensagens ao app_chat_controller.py"""
    
    controller_path = server_root / "controllers" / "v1" / "app_chat_controller.py"
    
    if not controller_path.exists():
        print(f"ERRO: Arquivo não encontrado: {controller_path}")
        return False
    
    # Ler o conteúdo atual
    with open(controller_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar se já tem as importações necessárias
    if "from core.config.database import get_mongo_db" not in content:
        # Adicionar importações após as existentes
        import_section = """from core.config.database import get_mongo_db
from dao.mongo.v1.chat_session_dao import ChatSessionDAO
from dao.mongo.v1.chat_message_dao import ChatMessageDAO
from uuid import uuid4
"""
        
        # Encontrar a posição após as importações existentes
        import_end = content.find('router = APIRouter()')
        if import_end == -1:
            print("ERRO: Não foi possível encontrar a seção de importações")
            return False
        
        # Inserir as novas importações
        content = content[:import_end] + import_section + content[import_end:]
    
    # Adicionar função para obter ou criar sessão
    if "async def get_or_create_app_session" not in content:
        session_function = """
async def get_or_create_app_session(app_id: str, user_id: str, db_session, mongo_db):
    \"\"\"
    Obtém ou cria uma sessão de chat para a aplicação com o schema_name como session_type
    \"\"\"
    try:
        # Obter informações da aplicação para saber o schema_name
        app_info = app_loader.get_app_config_from_database(app_id)
        if not app_info:
            print(f"Aplicação {app_id} não encontrada no MongoDB")
            return None
        
        schema_name = app_info['schema_name']
        print(f"Buscando sessão para app {app_id} com schema: {schema_name}, usuário: {user_id}")
        
        # Buscar sessão existente
        session_dao = ChatSessionDAO(mongo_db)
        existing_session = session_dao.get_session_by_agent_and_user(app_id, user_id)
        
        if existing_session:
            print(f"Sessão existente encontrada: {existing_session['_id']}")
            return existing_session['_id']
        
        # Criar nova sessão
        session_id = session_dao.create_session(
            user_id=user_id,
            agent_id=app_id,
            title=f"Chat - {schema_name}",
            session_type=schema_name  # Usar schema_name como session_type
        )
        
        print(f"Nova sessão criada: {session_id}")
        return session_id
        
    except Exception as e:
        print(f"Erro ao obter/criar sessão: {e}")
        return None

async def save_chat_message(session_id: str, sender: str, content: str, mongo_db, **kwargs):
    \"\"\"
    Salva uma mensagem no banco de dados
    \"\"\"
    try:
        message_dao = ChatMessageDAO(mongo_db, session_dao=ChatSessionDAO(mongo_db))
        message_id = message_dao.save_message(
            session_id=session_id,
            sender=sender,
            content=content,
            **kwargs
        )
        print(f"Mensagem salva: {message_id} para sessão {session_id}")
        return message_id
    except Exception as e:
        print(f"Erro ao salvar mensagem: {e}")
        return None
"""
        
        # Encontrar posição para inserir as funções (após as funções auxiliares existentes)
        helper_end = content.find('class ChatMessageRequest(BaseModel):')
        if helper_end == -1:
            print("ERRO: Não foi possível encontrar a seção de modelos")
            return False
        
        content = content[:helper_end] + session_function + content[helper_end:]
    
    # Modificar o endpoint de chat para incluir persistência
    if "async def process_chat_message(" in content:
        # Encontrar o endpoint e adicionar persistência
        endpoint_start = content.find('async def process_chat_message(')
        if endpoint_start != -1:
            # Encontrar o início do bloco try
            try_start = content.find('try:', endpoint_start)
            if try_start != -1:
                # Encontrar o final da declaração de parâmetros
                params_end = content.find('):', endpoint_start) + 2
                
                # Adicionar dependência do MongoDB
                new_params = content[params_end:try_start].replace(
                    'db_session = Depends(get_postgres_db)',
                    'db_session = Depends(get_postgres_db),\n    mongo_db = Depends(get_mongo_db)'
                )
                
                content = content[:params_end] + new_params + content[try_start:]
                
                # Encontrar a posição após a validação da mensagem
                validation_end = content.find('print(f"Processando mensagem para app', try_start)
                if validation_end != -1:
                    # Adicionar código de persistência
                    persistence_code = """
        # Obter ou criar sessão e salvar mensagem do usuário
        session_id = await get_or_create_app_session(app_id, firebase_uid, db_session, mongo_db)
        if session_id:
            await save_chat_message(
                session_id=session_id,
                sender="user",
                content=request.message,
                app_id=app_id
            )
"""
                    content = content[:validation_end] + persistence_code + content[validation_end:]
        
        # Adicionar persistência da resposta do agente
        response_save_pos = content.find('return ChatMessageResponse(', endpoint_start)
        if response_save_pos != -1:
            # Encontrar o bloco de retorno
            return_block_start = content.rfind('        ', 0, response_save_pos)
            
            # Adicionar código para salvar a resposta
            response_save_code = """
        # Salvar resposta do agente
        if session_id:
            await save_chat_message(
                session_id=session_id,
                sender="assistant",
                content=response_text,
                app_id=app_id
            )
"""
            content = content[:return_block_start] + response_save_code + content[return_block_start:]
    
    # Modificar o endpoint de streaming para incluir persistência
    if "async def process_chat_message_streaming(" in content:
        endpoint_start = content.find('async def process_chat_message_streaming(')
        if endpoint_start != -1:
            # Encontrar o início do bloco try
            try_start = content.find('try:', endpoint_start)
            if try_start != -1:
                # Encontrar o final da declaração de parâmetros
                params_end = content.find('):', endpoint_start) + 2
                
                # Adicionar dependência do MongoDB
                new_params = content[params_end:try_start].replace(
                    'db_session = Depends(get_postgres_db)',
                    'db_session = Depends(get_postgres_db),\n    mongo_db = Depends(get_mongo_db)'
                )
                
                content = content[:params_end] + new_params + content[try_start:]
                
                # Encontrar a posição após a validação da mensagem
                validation_end = content.find('print(f"Processando mensagem com streaming para app', try_start)
                if validation_end != -1:
                    # Adicionar código de persistência
                    persistence_code = """
        # Obter ou criar sessão e salvar mensagem do usuário
        session_id = await get_or_create_app_session(app_id, firebase_uid, db_session, mongo_db)
        if session_id:
            await save_chat_message(
                session_id=session_id,
                sender="user",
                content=request.message,
                app_id=app_id
            )
"""
                    content = content[:validation_end] + persistence_code + content[validation_end:]
        
        # Modificar a função de streaming para salvar a resposta completa
        if "async def generate_stream():" in content:
            stream_func_start = content.find('async def generate_stream():')
            if stream_func_start != -1:
                # Encontrar o final da função generate_stream
                stream_func_end = content.find('return StreamingResponse(', stream_func_start)
                if stream_func_end != -1:
                    # Adicionar código para coletar e salvar a resposta completa
                    stream_collect_code = """
                # Coletar tokens para salvar resposta completa
                full_response = ""
                async for chunk in team.process_query_streaming(request.message):
                    if isinstance(chunk, dict) and 'token' in chunk:
                        token = chunk['token']
                        full_response += token
                        import json
                        chunk_json = json.dumps(chunk)
                        yield f"data: {chunk_json}\\n\\n"
                    else:
                        import json
                        chunk_json = json.dumps(chunk)
                        yield f"data: {chunk_json}\\n\\n"
                
                # Salvar resposta completa do agente
                if session_id and full_response:
                    await save_chat_message(
                        session_id=session_id,
                        sender="assistant",
                        content=full_response,
                        app_id=app_id
                    )
"""
                    # Substituir o loop de streaming existente
                    old_stream_loop_start = content.find('async for chunk in team.process_query_streaming(request.message):', stream_func_start)
                    if old_stream_loop_start != -1:
                        old_stream_loop_end = content.find('else:', old_stream_loop_start)
                        if old_stream_loop_end != -1:
                            content = content[:old_stream_loop_start] + stream_collect_code + content[old_stream_loop_end:]
    
    # Escrever o conteúdo modificado
    with open(controller_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("SUCESSO: Persistencia adicionada ao app_chat_controller.py")
    return True

if __name__ == "__main__":
    success = add_persistence_to_app_chat()
    if success:
        print("SUCESSO: Script executado com sucesso!")
    else:
        print("ERRO: Falha ao executar o script")
        sys.exit(1)