#!/usr/bin/env python3
"""
Script para criar o Agente Orquestrador no MongoDB
Este agente será exibido como segunda opção na modal de seleção de agentes
"""

import sys
import os
import asyncio

# Adicionar o diretório raiz ao path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo import MongoClient
from datetime import datetime

async def create_orchestrator_agent():
    """Cria o agente Orquestrador no MongoDB"""
    
    # Configuração da conexão MongoDB
    MONGODB_URI = "mongodb://localhost:27017"
    DATABASE_NAME = "saphien"
    COLLECTION_NAME = "agents"
    
    try:
        # Conectar ao MongoDB
        client = MongoClient(MONGODB_URI)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        # Verificar se o agente já existe
        existing_agent = collection.find_one({"_id": "222222222222222222222222"})
        if existing_agent:
            print("Agente Orquestrador já existe no banco de dados")
            print(f"   Nome: {existing_agent.get('name', 'N/A')}")
            print(f"   Categoria: {existing_agent.get('category', 'N/A')}")
            return existing_agent
        
        # Dados do agente Orquestrador
        orchestrator_agent = {
            "_id": "222222222222222222222222",
            "name": "Modo Orquestrador",
            "category": "Modo Orquestrador",
            "description": "Orquestra múltiplos agentes especialistas para resolver problemas complexos de forma colaborativa",
            "goal": "Coordenar e orquestrar múltiplos agentes especialistas para resolver problemas complexos que requerem expertise em diferentes áreas",
            "roleDefinition": "Orquestrador de Agentes Especialistas",
            "personalityInstructions": "Sou um orquestrador inteligente que analisa problemas complexos e distribui tarefas para os agentes especialistas mais adequados. Coordeno a colaboração entre diferentes especialistas para obter a melhor solução possível.",
            "agentRules": "1. Analisar a complexidade do problema\n2. Identificar quais agentes especialistas são necessários\n3. Coordenar a colaboração entre os agentes\n4. Sintetizar as respostas dos especialistas\n5. Garantir uma solução coesa e completa",
            "whenToUse": "Para problemas complexos que envolvem múltiplas áreas de conhecimento ou quando você não sabe qual agente especialista é o mais adequado",
            "status": "active",
            "is_public": True,
            "is_owner": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "model_id": None,  # Não usa modelo específico, é um agente especial
            "provider_id": None,  # Não usa provedor específico
            "user_uid": None,  # Agente do sistema
            "metadata": {
                "type": "system_orchestrator",
                "special_agent": True,
                "display_order": 2,  # Segunda opção na lista
                "color": "blue",  # Cor para identificação visual
                "icon": "orchestrator"
            }
        }
        
        # Inserir o agente
        result = collection.insert_one(orchestrator_agent)
        
        print("Agente Orquestrador criado com sucesso!")
        print(f"   ID: {orchestrator_agent['_id']}")
        print(f"   Nome: {orchestrator_agent['name']}")
        print(f"   Categoria: {orchestrator_agent['category']}")
        print(f"   Descrição: {orchestrator_agent['description']}")
        
        return orchestrator_agent
        
    except Exception as e:
        print(f"Erro ao criar agente Orquestrador: {e}")
        return None
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    print("Iniciando criação do Agente Orquestrador...")
    asyncio.run(create_orchestrator_agent())