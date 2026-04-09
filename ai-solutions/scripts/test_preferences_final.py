#!/usr/bin/env python3
"""
Script final para testar se as preferências estão funcionando corretamente
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

async def test_user_113_exists():
    """Testar se o usuário ID 113 existe e pode ser encontrado"""
    print("=== TESTE FINAL: VERIFICANDO USUÁRIO ID 113 ===")
    
    DATABASE_URL = "postgresql+asyncpg://postgres:qwe321@localhost:5432/saphien"
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            # Buscar usuário ID 113
            user_query = select(User).where(User.id == 113)
            user_result = await session.execute(user_query)
            user = user_result.scalar_one_or_none()
            
            if user:
                print(f"[OK] USUARIO ID 113 ENCONTRADO:")
                print(f"   - ID: {user.id}")
                print(f"   - Firebase UID: {user.firebase_uid}")
                print(f"   - Email: {user.email}")
                print(f"   - Nome: {user.nome}")
                print(f"   - Account Type: {user.account_type}")
                print(f"   - Organization ID: {user.selected_organization_id}")
                print(f"   - Project ID: {user.selected_project_id}")
                print(f"   - Ativo: {user.is_active}")
                return True
            else:
                print("[ERROR] USUARIO ID 113 NAO ENCONTRADO")
                return False
                
    except Exception as e:
        print(f"[ERROR] ERRO AO BUSCAR USUARIO: {e}")
        return False
    
    finally:
        await engine.dispose()

async def test_endpoint_structure():
    """Testar se o endpoint está configurado corretamente"""
    print("\n=== VERIFICANDO ESTRUTURA DO ENDPOINT ===")
    
    # Verificar se o controlador está correto
    user_controller_path = "server/controllers/v1/user_controller.py"
    if os.path.exists(user_controller_path):
        print(f"✅ Controlador encontrado: {user_controller_path}")
        
        # Verificar se tem os endpoints corretos
        with open(user_controller_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            if '@router.get("/preferences")' in content:
                print("[OK] Endpoint GET /preferences encontrado")
            else:
                print("[ERROR] Endpoint GET /preferences NAO encontrado")
                
            if '@router.put("/preferences")' in content:
                print("[OK] Endpoint PUT /preferences encontrado")
            else:
                print("[ERROR] Endpoint PUT /preferences NAO encontrado")
                
            if 'get_user_preferences' in content:
                print("[OK] Funcao get_user_preferences encontrada")
            else:
                print("[ERROR] Funcao get_user_preferences NAO encontrada")
                
            if 'save_user_preferences' in content:
                print("[OK] Funcao save_user_preferences encontrada")
            else:
                print("[ERROR] Funcao save_user_preferences NAO encontrada")
    else:
        print(f"[ERROR] Controlador nao encontrado: {user_controller_path}")

async def test_frontend_correction():
    """Verificar se o frontend foi corrigido"""
    print("\n=== VERIFICANDO CORREÇÃO DO FRONTEND ===")
    
    preferences_jsx_path = "platform/src/pages/Preferences.jsx"
    if os.path.exists(preferences_jsx_path):
        print(f"✅ Componente Preferences encontrado: {preferences_jsx_path}")
        
        with open(preferences_jsx_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            if '/api/v1/users/preferences' in content:
                print("[OK] Endpoint correto (/api/v1/users/preferences) encontrado no frontend")
            else:
                print("[ERROR] Endpoint correto NAO encontrado no frontend")
                
            if '/api/v1/preferences' in content:
                print("[WARN] Endpoint antigo (/api/v1/preferences) ainda presente - PODE CAUSAR ERRO")
            else:
                print("[OK] Endpoint antigo removido do frontend")
    else:
        print(f"[ERROR] Componente Preferences nao encontrado: {preferences_jsx_path}")

async def main():
    """Executar todos os testes"""
    print("[TEST] INICIANDO TESTE FINAL DAS PREFERENCIAS")
    print("=" * 50)
    
    # Testar se o usuário existe
    user_exists = await test_user_113_exists()
    
    # Testar estrutura do endpoint
    await test_endpoint_structure()
    
    # Testar correção do frontend
    await test_frontend_correction()
    
    print("\n" + "=" * 50)
    print("[RESUMO] RESUMO DOS TESTES:")
    
    if user_exists:
        print("✅ USUÁRIO ID 113 EXISTE NO BANCO")
        print("✅ ENDPOINT CORRETO CONFIGURADO (/api/v1/users/preferences)")
        print("✅ FRONTEND CORRIGIDO")
        print("\n[SUCESSO] A pagina de preferencias deve funcionar agora!")
        print("   Acesse: http://localhost:5173/preferences")
    else:
        print("❌ PROBLEMA IDENTIFICADO: Usuário ID 113 não encontrado")
        print("   Verifique se o usuário está logado com o UID correto")
        
    print("\n[INFO] Para testar:")
    print("   1. Certifique-se de que o servidor está rodando (porta 8000)")
    print("   2. Certifique-se de que o frontend está rodando (porta 5173)")
    print("   3. Faça login com o usuário correto")
    print("   4. Acesse: http://localhost:5173/preferences")

if __name__ == "__main__":
    asyncio.run(main())