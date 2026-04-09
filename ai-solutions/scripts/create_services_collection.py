"""
Script para criar a coleção services no MongoDB com índices otimizados
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config.database import get_mongo_db
from loguru import logger

def create_services_collection():
    """Cria a coleção services com índices otimizados"""
    try:
        db = get_mongo_db()
        
        # A coleção será criada automaticamente no primeiro insert
        # Mas vamos criar índices para otimizar as consultas
        services_collection = db.services
        
        # Criar índices para consultas frequentes
        services_collection.create_index([("app_id", 1), ("user_id", 1)])
        services_collection.create_index([("user_id", 1)])
        services_collection.create_index([("app_id", 1)])
        services_collection.create_index([("status", 1)])
        services_collection.create_index([("created_at", -1)])
        
        logger.info("Coleção 'services' configurada com índices otimizados")
        print("Coleção 'services' configurada com índices otimizados")
        
        # Verificar se a coleção existe
        collections = db.list_collection_names()
        if "services" in collections:
            print(f"Coleção 'services' existe no MongoDB")
            print(f"Total de documentos: {services_collection.count_documents({})}")
        else:
            print("Coleção 'services' será criada automaticamente no primeiro insert")
            
    except Exception as e:
        logger.error(f"Erro ao configurar coleção services: {e}")
        print(f"Erro ao configurar coleção services: {e}")

if __name__ == "__main__":
    create_services_collection()