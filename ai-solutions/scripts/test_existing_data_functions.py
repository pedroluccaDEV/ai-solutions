"""
Script para testar as funções get_existing_tables e get_existing_services
"""
import sys
import os
import asyncio
from datetime import datetime

# Adicionar o diretório server ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controllers.v1.builder_controller import get_existing_tables, get_existing_services
from core.auth.firebase_auth import get_current_user
from loguru import logger

# Configurar logger
logger.remove()
logger.add(sys.stdout, level="INFO")

async def test_get_existing_tables():
    """Testar função get_existing_tables"""
    print("\n=== TESTANDO get_existing_tables ===")
    
    try:
        # Simular usuário para teste
        test_user = {"uid": "JJ9t5xjMIAdbsmM86U2oLHGDGu62"}
        
        # Testar com schema conhecido
        schema_name = "cac"  # Schema conhecido do central_de_atendimento
        
        print(f"Buscando tabelas no schema: {schema_name}")
        print(f"Usuário: {test_user['uid']}")
        
        # Chamar função
        result = await get_existing_tables(schema_name, test_user)
        
        print(f"Resultado: {result}")
        print(f"Número de tabelas encontradas: {len(result.get('tables', []))}")
        
        if result.get('tables'):
            for table in result['tables']:
                print(f"  - Tabela: {table.get('name')} com {len(table.get('columns', []))} colunas")
        
        return result
        
    except Exception as e:
        print(f"❌ Erro ao testar get_existing_tables: {e}")
        return None

async def test_get_existing_services():
    """Testar função get_existing_services"""
    print("\n=== TESTANDO get_existing_services ===")
    
    try:
        # Simular usuário para teste
        test_user = {"uid": "JJ9t5xjMIAdbsmM86U2oLHGDGu62"}
        
        # Testar com app_id conhecido
        app_id = "central_de_atendimento"
        
        print(f"Buscando serviços para app: {app_id}")
        print(f"Usuário: {test_user['uid']}")
        
        # Chamar função
        result = await get_existing_services(app_id, test_user)
        
        print(f"Resultado: {result}")
        print(f"Número de serviços encontrados: {len(result.get('services', []))}")
        
        if result.get('services'):
            for service in result['services']:
                print(f"  - Serviço: {service.get('name')} (Status: {service.get('status')})")
        
        return result
        
    except Exception as e:
        print(f"❌ Erro ao testar get_existing_services: {e}")
        return None

async def main():
    """Função principal de teste"""
    print("=== INICIANDO TESTE DAS FUNÇÕES EXISTING DATA ===")
    print(f"Timestamp: {datetime.now()}")
    
    # Testar get_existing_tables
    tables_result = await test_get_existing_tables()
    
    # Testar get_existing_services
    services_result = await test_get_existing_services()
    
    print("\n=== RESUMO DOS TESTES ===")
    print(f"get_existing_tables: {'SUCESSO' if tables_result else 'FALHA'}")
    print(f"get_existing_services: {'SUCESSO' if services_result else 'FALHA'}")
    
    if tables_result:
        print(f"Tabelas encontradas: {len(tables_result.get('tables', []))}")
    
    if services_result:
        print(f"Serviços encontrados: {len(services_result.get('services', []))}")

if __name__ == "__main__":
    asyncio.run(main())