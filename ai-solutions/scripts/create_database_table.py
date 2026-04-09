import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv(".env")

async def create_database_table():
    """Cria a sequence e a tabela databases no PostgreSQL"""
    
    # Obtém a URL do PostgreSQL do .env
    postgres_url = os.getenv("POSTGRES_URL")
    if not postgres_url:
        print("POSTGRES_URL não encontrada no .env")
        return
    
    # Extrai informações da URL
    # postgresql+asyncpg://postgres:root@localhost:5433/saphien
    url_parts = postgres_url.replace("postgresql+asyncpg://", "").split("@")
    credentials = url_parts[0].split(":")
    host_port_db = url_parts[1].split("/")
    host_port = host_port_db[0].split(":")
    
    username = credentials[0]
    password = credentials[1]
    host = host_port[0]
    port = host_port[1] if len(host_port) > 1 else "5433"
    database = host_port_db[1]
    
    print(f"Conectando ao PostgreSQL: {host}:{port}/{database}")
    
    try:
        # Conecta ao PostgreSQL
        conn = await asyncpg.connect(
            host=host,
            port=int(port),
            user=username,
            password=password,
            database=database
        )
        
        print("Conectado ao PostgreSQL com sucesso")
        
        # Cria a sequence para a chave primária
        print("Criando sequence...")
        await conn.execute("""
            CREATE SEQUENCE IF NOT EXISTS databases_id_seq
            START WITH 1
            INCREMENT BY 1
            NO MINVALUE
            NO MAXVALUE
            CACHE 1;
        """)
        
        # Cria a tabela databases
        print("Criando tabela databases...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS databases (
                id INTEGER PRIMARY KEY DEFAULT nextval('databases_id_seq'),
                name VARCHAR NOT NULL,
                description TEXT,
                type VARCHAR NOT NULL DEFAULT 'PostgreSQL',
                host VARCHAR NOT NULL,
                port INTEGER NOT NULL DEFAULT 5433,
                database_name VARCHAR NOT NULL,
                username VARCHAR NOT NULL,
                password VARCHAR NOT NULL,
                status VARCHAR NOT NULL DEFAULT 'disconnected',
                created_by VARCHAR NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Cria índice no campo name
        print("Criando índices...")
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_databases_name ON databases(name);
        """)
        
        print("Tabela 'databases' criada com sucesso!")
        
        # Verifica se a tabela foi criada
        result = await conn.fetchrow("""
            SELECT COUNT(*) as count FROM information_schema.tables 
            WHERE table_name = 'databases';
        """)
        
        if result['count'] > 0:
            print("Verificação: Tabela 'databases' existe no banco de dados")
        else:
            print("Erro: Tabela 'databases' não foi criada")
        
        await conn.close()
        
    except Exception as e:
        print(f"Erro ao criar tabela: {e}")

if __name__ == "__main__":
    asyncio.run(create_database_table())