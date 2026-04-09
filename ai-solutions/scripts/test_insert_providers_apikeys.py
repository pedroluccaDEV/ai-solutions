#!/usr/bin/env python3
"""
Script para inserir dados de teste na tabela providers_apikeys
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

def insert_test_data():
    """Insere dados de teste na tabela providers_apikeys"""
    
    try:
        # Configuração de conexão
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="saphien",
            user="postgres",
            password="qwe321"
        )
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("Inserindo dados de teste na tabela providers_apikeys...")
        
        # Inserir dados de exemplo
        test_data = [
            {
                'id_provider': 1,
                'url': 'https://api.openai.com/v1',
                'apikey': 'sk-example-openai-123456789',
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'status': True
            },
            {
                'id_provider': 2,
                'url': 'https://api.anthropic.com/v1',
                'apikey': 'claude-example-anthropic-987654321',
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'status': True
            },
            {
                'id_provider': 3,
                'url': 'https://api.groq.com/openai/v1',
                'apikey': 'gsk-example-groq-abcdef123456',
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'status': False
            }
        ]
        
        for data in test_data:
            cursor.execute("""
                INSERT INTO providers_apikeys 
                (id_provider, url, apikey, created_at, updated_at, status)
                VALUES (%(id_provider)s, %(url)s, %(apikey)s, %(created_at)s, %(updated_at)s, %(status)s)
            """, data)
        
        conn.commit()
        print(f"Inseridos {len(test_data)} registros de teste")
        
        # Verificar os dados inseridos
        cursor.execute("SELECT COUNT(*) as count FROM providers_apikeys")
        result = cursor.fetchone()
        print(f"Total de registros na tabela: {result['count']}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"Erro ao inserir dados de teste: {e}")
        return False

if __name__ == "__main__":
    success = insert_test_data()
    if success:
        print("Dados de teste inseridos com sucesso!")
    else:
        print("Falha ao inserir dados de teste!")