#!/usr/bin/env python3
"""
Script para exportar todas as coleções do MongoDB Saphien para arquivos JSON.
Exporta cada coleção em um arquivo JSON separado.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from bson import json_util
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

def export_mongodb_database():
    """Exporta todas as coleções do MongoDB para arquivos JSON"""
    
    # Configurações do MongoDB a partir do .env
    mongo_uri = "mongodb://localhost:27017"
    #mongo_uri = "mongodb://mongo:hUICpcfCOoHGpCHgFGJiAOBNVOCIKPZT@tramway.proxy.rlwy.net:34458"
    db_name = "saphien"
    
    # Caminhos de exportação
    export_base_dir = Path(__file__).parent.parent / "exports"
    mongodb_dir = export_base_dir / "database" / "mongodb"
    
    # Criar diretórios se não existirem
    mongodb_dir.mkdir(parents=True, exist_ok=True)
    
    # Timestamp para nome dos arquivos
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_dir = mongodb_dir / f"backup_{timestamp}"
    export_dir.mkdir(exist_ok=True)
    
    print(f"Iniciando exportação do banco MongoDB...")
    print(f"Diretório de destino: {export_dir}")
    print(f"Conectando em: {mongo_uri}/{db_name}")
    
    try:
        # Conectar ao MongoDB
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')  # Testar conexão
        db = client[db_name]
        
        print("Conexão com MongoDB estabelecida com sucesso!")
        
        # Listar todas as coleções
        collections = db.list_collection_names()
        print(f"Coleções encontradas: {len(collections)}")
        
        if not collections:
            print("Nenhuma coleção encontrada no banco de dados")
            return True, "Nenhuma coleção para exportar"
        
        total_documents = 0
        exported_collections = []
        
        for collection_name in collections:
            collection = db[collection_name]
            document_count = collection.count_documents({})
            
            if document_count == 0:
                print(f"Pulando {collection_name} (vazia)")
                continue
                
            print(f"Exportando {collection_name} ({document_count} documentos)...")
            
            # Nome do arquivo
            output_file = export_dir / f"{collection_name}.json"
            
            # Exportar documentos
            documents = list(collection.find({}))
            
            # Converter para JSON com tratamento de objetos BSON
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(documents, f, default=json_util.default, indent=2, ensure_ascii=False)
            
            # Verificar se o arquivo foi criado corretamente
            file_size = output_file.stat().st_size
            print(f"   {output_file.name} ({file_size / 1024:.1f} KB)")
            
            exported_collections.append(collection_name)
            total_documents += document_count
        
        print("=" * 50)
        print(f"Exportação concluída!")
        print(f"Coleções exportadas: {len(exported_collections)}")
        print(f"Documentos totais: {total_documents}")
        print(f"Local: {export_dir}")
        
        # Criar arquivo de metadados
        metadata = {
            "export_date": datetime.now().isoformat(),
            "database": db_name,
            "collections_exported": exported_collections,
            "total_documents": total_documents,
            "mongo_uri": mongo_uri
        }
        
        metadata_file = export_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        return True, str(export_dir)
        
    except (ConnectionFailure, ServerSelectionTimeoutError):
        print("Não foi possível conectar ao MongoDB")
        print("   Verifique se o MongoDB está rodando: mongod --dbpath /seu/caminho/dados")
        return False, "Falha de conexão com MongoDB"
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return False, str(e)

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="Exportar banco MongoDB Saphien")
    parser.add_argument("--verbose", "-v", action="store_true", help="Modo verboso")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("EXPORTADOR DE BANCO MONGODB - SAPHIEN")
    print("=" * 60)
    
    success, message = export_mongodb_database()
    
    if success:
        print(f"Exportação concluída: {message}")
        sys.exit(0)
    else:
        print(f"Falha na exportação: {message}")
        sys.exit(1)

if __name__ == "__main__":
    main()