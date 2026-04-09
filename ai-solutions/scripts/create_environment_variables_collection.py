#!/usr/bin/env python3
"""
Script para criar a coleção environment_variables no MongoDB
e inserir alguns dados de exemplo.
"""

import sys
import os
from datetime import datetime

# Adicionar o diretório server ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config.database import get_mongo_db
from bson import ObjectId

def create_environment_variables_collection():
    """Criar a coleção environment_variables e inserir dados de exemplo"""
    
    try:
        db = get_mongo_db()
        
        # Verificar se a coleção já existe
        collections = db.list_collection_names()
        
        if "environment_variables" in collections:
            print("Coleção environment_variables já existe")
            # Contar documentos existentes
            count = db.environment_variables.count_documents({})
            print(f"Total de variáveis existentes: {count}")
        else:
            print("Criando coleção environment_variables...")
            # Criar a coleção inserindo um documento
            db.environment_variables.insert_one({
                "_id": ObjectId(),
                "key": "INITIAL_SETUP",
                "value": "setup_completed",
                "environment": "Development",
                "description": "Documento inicial para criar a coleção",
                "created_by": "system",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "updated_by": "system"
            })
            print("Coleção environment_variables criada com sucesso")
        
        # Inserir alguns dados de exemplo (apenas se não existirem)
        example_variables = [
            {
                "key": "API_KEY",
                "value": "sk-example-123456789",
                "environment": "Production",
                "description": "Chave da API principal"
            },
            {
                "key": "DATABASE_URL",
                "value": "postgresql://user:pass@localhost:5433/saphien",
                "environment": "Development",
                "description": "URL de conexão com o banco de dados"
            },
            {
                "key": "AWS_ACCESS_KEY",
                "value": "AKIAIOSFODNN7EXAMPLE",
                "environment": "Staging",
                "description": "Chave de acesso AWS"
            }
        ]
        
        inserted_count = 0
        for var_data in example_variables:
            # Verificar se já existe uma variável com a mesma chave e ambiente
            existing = db.environment_variables.find_one({
                "key": var_data["key"],
                "environment": var_data["environment"]
            })
            
            if not existing:
                db.environment_variables.insert_one({
                    "_id": ObjectId(),
                    **var_data,
                    "created_by": "system",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "updated_by": "system"
                })
                inserted_count += 1
                print(f"Variável de exemplo inserida: {var_data['key']} ({var_data['environment']})")
            else:
                print(f"Variável já existe: {var_data['key']} ({var_data['environment']})")
        
        if inserted_count > 0:
            print(f"{inserted_count} variáveis de exemplo inseridas")
        else:
            print("Nenhuma nova variável de exemplo inserida (todas já existiam)")
        
        # Contar documentos finais
        total_count = db.environment_variables.count_documents({})
        print(f"Total de variáveis na coleção: {total_count}")
        
        # Criar índices para melhor performance
        print("Criando índices...")
        db.environment_variables.create_index([("created_by", 1)])
        db.environment_variables.create_index([("key", 1), ("environment", 1)])
        db.environment_variables.create_index([("environment", 1)])
        db.environment_variables.create_index([("created_at", -1)])
        print("Índices criados com sucesso")
        
        return True
        
    except Exception as e:
        print(f"Erro ao criar coleção: {e}")
        return False

def test_collection_access():
    """Testar acesso à coleção criada"""
    try:
        db = get_mongo_db()
        
        # Testar busca
        variables = list(db.environment_variables.find().limit(5))
        print(f"Primeiras {len(variables)} variáveis:")
        
        for var in variables:
            print(f"  - {var['key']} = {var['value']} ({var['environment']})")
        
        return True
        
    except Exception as e:
        print(f"Erro ao testar acesso: {e}")
        return False

if __name__ == "__main__":
    print("Iniciando setup da coleção environment_variables...")
    
    # Criar coleção
    success = create_environment_variables_collection()
    
    if success:
        print("\nTestando acesso à coleção...")
        test_collection_access()
        print("\nSetup concluído com sucesso!")
    else:
        print("\nSetup falhou!")