#!/usr/bin/env python3
"""
Script para verificar o status do ChromaDB
"""

import os
import sys
from pathlib import Path

# Adicionar o caminho do projeto ao sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config.chroma_client import is_chroma_available

def check_chroma_status():
    """Verifica o status do ChromaDB"""
    print("=== VERIFICAÇÃO DO STATUS DO CHROMADB ===\n")
    
    # Verificar variáveis de ambiente
    chroma_url = os.getenv("CHROMA_URL")
    chroma_auth = os.getenv("CHROMA_AUTH")
    
    print(f"CHROMA_URL: {chroma_url}")
    print(f"CHROMA_AUTH: {'***' if chroma_auth else 'Não configurada'}")
    
    # Verificar disponibilidade
    if is_chroma_available():
        print("\n✅ ChromaDB está CONECTADO e funcionando")
        return True
    else:
        print("\n❌ ChromaDB NÃO está disponível")
        print("\n--- SOLUÇÃO ---")
        print("1. Inicie o ChromaDB localmente:")
        print("   docker run -p 8000:8000 chromadb/chroma")
        print()
        print("2. Ou configure uma URL externa do ChromaDB:")
        print("   export CHROMA_URL=http://localhost:8000")
        print("   export CHROMA_AUTH=sua_chave_aqui (se necessário)")
        print()
        print("3. Para desenvolvimento, você pode usar:")
        print("   pip install chromadb")
        print("   python -m chromadb run --host localhost --port 8000")
        return False

def main():
    """Função principal"""
    success = check_chroma_status()
    
    if not success:
        print("\n⚠️  ATENÇÃO: Sem ChromaDB, as bases de conhecimento serão criadas")
        print("   mas os documentos NÃO serão processados/salvos.")
        print("   A base aparecerá com '0 documentos' na interface.")

if __name__ == "__main__":
    main()