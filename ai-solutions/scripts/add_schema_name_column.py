"""
Script para adicionar a coluna schema_name na tabela databases
"""
import asyncio
import sys
import os

# Adicionar o diretório raiz ao path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import text
from core.config.database import get_postgres_engine

async def add_schema_name_column():
    """Adiciona a coluna schema_name na tabela databases se ela não existir"""
    
    engine = get_postgres_engine()
    
    async with engine.begin() as conn:
        # Verificar se a coluna schema_name já existe
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'databases' AND column_name = 'schema_name'
        """))
        
        column_exists = result.fetchone()
        
        if not column_exists:
            print("Adicionando coluna schema_name na tabela databases...")
            
            # Adicionar a coluna schema_name
            await conn.execute(text("""
                ALTER TABLE databases 
                ADD COLUMN schema_name VARCHAR(255)
            """))
            
            print("Coluna schema_name adicionada com sucesso!")
        else:
            print("Coluna schema_name já existe na tabela databases.")
        
        # Verificar a estrutura atual da tabela
        result = await conn.execute(text("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'databases' 
            ORDER BY ordinal_position
        """))
        
        columns = result.fetchall()
        print("\nEstrutura atual da tabela databases:")
        for column in columns:
            print(f"  {column[0]} ({column[1]}) - Nullable: {column[2]}")

if __name__ == "__main__":
    asyncio.run(add_schema_name_column())