#!/usr/bin/env python3
"""
Script para testar os endpoints de preferências do usuário
"""

import asyncio
import sys
import os

# Adicionar o diretório raiz ao path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from models.postgres.user_model import User
import asyncpg

async def test_preferences_endpoints():
    """Testar os endpoints de preferências"""
    
    # Configuração do banco de dados
    DATABASE_URL = "postgresql+asyncpg://postgres:qwe321@localhost:5432/saphien"
    
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            print("=== Testando conexão com banco de dados ===")
            
            # Testar se podemos buscar usuários
            result = await session.execute(select(User))
            users = result.scalars().all()
            print(f"Total de usuários no banco: {len(users)}")
            
            # Listar alguns usuários para referência
            for user in users[:5]:
                print(f"  - ID: {user.id}, Email: {user.email}, Firebase UID: {user.firebase_uid}")
            
            # Testar busca por firebase_uid específico
            test_uid = "JJ9t5xjMIAdbsmM86U2oLHGDGu62"  # Substituir por um UID real se necessário
            user_query = select(User).where(User.firebase_uid == test_uid)
            user_result = await session.execute(user_query)
            user = user_result.scalar_one_or_none()
            
            if user:
                print(f"[OK] Usuário encontrado: {user.email} (ID: {user.id})")
            else:
                print(f"[WARN] Usuário com UID {test_uid} não encontrado")
                print("  Isso é esperado se o usuário não existir no banco ainda")
            
            print("\n=== Teste concluído ===")
            
    except Exception as e:
        print(f"[ERROR] Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await engine.dispose()

async def test_user_creation():
    """Testar a lógica de criação automática de usuário"""
    print("\n=== Testando logica de criacao automatica de usuario ===")
    
    # Simular dados de usuário Firebase
    firebase_user_data = {
        "uid": "test_firebase_uid_123",
        "email": "test_user@example.com",
        "nome": "Test",
        "sobrenome": "User"
    }
    
    DATABASE_URL = "postgresql+asyncpg://postgres:qwe321@localhost:5432/saphien"
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            # Verificar se o usuário já existe
            user_query = select(User).where(User.firebase_uid == firebase_user_data["uid"])
            user_result = await session.execute(user_query)
            existing_user = user_result.scalar_one_or_none()
            
            if existing_user:
                print(f"[OK] Usuario ja existe: {existing_user.email}")
                return existing_user
            
            # Criar novo usuário (simulando a lógica do controller)
            print("[INFO] Criando novo usuario automaticamente...")
            new_user = User(
                firebase_uid=firebase_user_data["uid"],
                email=firebase_user_data["email"],
                nome=firebase_user_data["nome"],
                sobrenome=firebase_user_data["sobrenome"],
                is_active=True
            )
            
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            
            print(f"[OK] Novo usuario criado: {new_user.email} (ID: {new_user.id})")
            return new_user
            
    except Exception as e:
        print(f"[ERROR] Erro ao criar usuario: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        await engine.dispose()

if __name__ == "__main__":
    print("Iniciando testes dos endpoints...")
    
    # Executar testes
    asyncio.run(test_preferences_endpoints())
    asyncio.run(test_user_creation())
    
    print("\n[INFO] Para testar os endpoints HTTP, acesse:")
    print("   - GET: http://localhost:8000/api/v1/users/preferences")
    print("   - PUT: http://localhost:8000/api/v1/users/preferences")
    print("\n[INFO] Certifique-se de que o servidor esta rodando e use um token Firebase valido")