#!/usr/bin/env python3
"""
Script para limpar a coleção de canais no MongoDB
Remove todos os documentos da coleção 'channels'
"""

import sys
import os

# Adiciona o diretório server ao path para importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.config.database import get_mongo_db

def clear_channels_collection():
    """Limpa todos os documentos da coleção channels"""
    try:
        db = get_mongo_db()
        collection = db["channels"]
        
        # Conta documentos antes da limpeza
        count_before = collection.count_documents({})
        print(f"Documentos na coleção 'channels' antes: {count_before}")
        
        if count_before == 0:
            print("Coleção 'channels' já está vazia.")
            return
        
        # Remove todos os documentos
        result = collection.delete_many({})
        print(f"Documentos removidos: {result.deleted_count}")
        
        # Conta documentos depois da limpeza
        count_after = collection.count_documents({})
        print(f"Documentos na coleção 'channels' depois: {count_after}")
        
        print("Coleção 'channels' limpa com sucesso!")
        
    except Exception as e:
        print(f"Erro ao limpar coleção 'channels': {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("Iniciando limpeza da coleção 'channels'...")
    clear_channels_collection()