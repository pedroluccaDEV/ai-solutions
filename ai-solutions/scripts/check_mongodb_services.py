"""
Script para verificar se há serviços na coleção services do MongoDB
"""
import sys
import os
from pymongo import MongoClient
from loguru import logger

# Configurar logger
logger.remove()
logger.add(sys.stdout, level="INFO")

def check_mongodb_services():
    """Verificar serviços na coleção services do MongoDB"""
    print("\n=== VERIFICANDO SERVIÇOS NO MONGODB ===")
    
    try:
        # Conectar ao MongoDB
        client = MongoClient("mongodb://localhost:27017/")
        db = client["saphien"]
        services_collection = db["services"]
        
        print(f"Conectado ao MongoDB: {client.address}")
        print(f"Database: saphien")
        print(f"Coleção: services")
        
        # Contar total de documentos
        total_count = services_collection.count_documents({})
        print(f"Total de documentos na coleção services: {total_count}")
        
        # Buscar todos os serviços
        all_services = list(services_collection.find({}))
        
        if all_services:
            print(f"\n=== SERVIÇOS ENCONTRADOS ({len(all_services)}) ===")
            for service in all_services:
                print(f"Serviço: {service.get('name', 'N/A')}")
                print(f"  - App ID: {service.get('app_id', 'N/A')}")
                print(f"  - User ID: {service.get('user_id', 'N/A')}")
                print(f"  - Status: {service.get('status', 'N/A')}")
                print(f"  - Schema: {service.get('schema_name', 'N/A')}")
                print(f"  - Criado em: {service.get('created_at', 'N/A')}")
                print()
        else:
            print("Nenhum serviço encontrado na coleção services")
            
        # Verificar índices da coleção
        indexes = list(services_collection.list_indexes())
        print(f"\n=== ÍNDICES DA COLEÇÃO SERVICES ===")
        for index in indexes:
            print(f"Índice: {index['name']}")
            print(f"  - Campos: {index.get('key', {})}")
            print(f"  - Único: {index.get('unique', False)}")
            print()
            
        return all_services
        
    except Exception as e:
        print(f"❌ Erro ao verificar MongoDB: {e}")
        return None

def check_specific_user_services():
    """Verificar serviços específicos do usuário JJ9t5xjMIAdbsmM86U2oLHGDGu62"""
    print("\n=== VERIFICANDO SERVIÇOS DO USUÁRIO ESPECÍFICO ===")
    
    try:
        # Conectar ao MongoDB
        client = MongoClient("mongodb://localhost:27017/")
        db = client["saphien"]
        services_collection = db["services"]
        
        user_id = "JJ9t5xjMIAdbsmM86U2oLHGDGu62"
        app_id = "central_de_atendimento"
        
        # Buscar serviços específicos do usuário
        query = {
            "user_id": user_id,
            "app_id": app_id
        }
        
        user_services = list(services_collection.find(query))
        
        print(f"Buscando serviços para:")
        print(f"  - User ID: {user_id}")
        print(f"  - App ID: {app_id}")
        print(f"  - Query: {query}")
        
        if user_services:
            print(f"\n=== SERVIÇOS DO USUÁRIO ENCONTRADOS ({len(user_services)}) ===")
            for service in user_services:
                print(f"Serviço: {service.get('name', 'N/A')}")
                print(f"  - ID: {service.get('_id')}")
                print(f"  - Status: {service.get('status', 'N/A')}")
                print(f"  - Schema: {service.get('schema_name', 'N/A')}")
                print(f"  - Criado em: {service.get('created_at', 'N/A')}")
                print()
        else:
            print("Nenhum serviço encontrado para este usuário e aplicativo")
            
        return user_services
        
    except Exception as e:
        print(f"❌ Erro ao verificar serviços do usuário: {e}")
        return None

if __name__ == "__main__":
    print("=== VERIFICAÇÃO DA COLEÇÃO SERVICES NO MONGODB ===")
    
    # Verificar todos os serviços
    all_services = check_mongodb_services()
    
    # Verificar serviços específicos do usuário
    user_services = check_specific_user_services()
    
    print("\n=== RESUMO ===")
    print(f"Total de serviços no MongoDB: {len(all_services) if all_services else 0}")
    print(f"Serviços do usuário específico: {len(user_services) if user_services else 0}")