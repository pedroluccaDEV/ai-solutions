import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv(".env")

async def get_databases_from_main_db():
    """
    Obtém a lista de bancos de dados cadastrados na tabela databases
    """
    try:
        # Obtém a URL do PostgreSQL do .env
        postgres_url = os.getenv("POSTGRES_URL")
        if not postgres_url:
            print("POSTGRES_URL não encontrada no .env")
            return []
        
        # Extrai informações da URL
        url_parts = postgres_url.replace("postgresql+asyncpg://", "").split("@")
        credentials = url_parts[0].split(":")
        host_port_db = url_parts[1].split("/")
        host_port = host_port_db[0].split(":")
        
        username = credentials[0]
        password = credentials[1]
        host = host_port[0]
        port = host_port[1] if len(host_port) > 1 else "5433"
        database = host_port_db[1]
        
        print(f"Conectando ao banco principal: {host}:{port}/{database}")
        
        # Conecta ao banco principal
        conn = await asyncpg.connect(
            host=host,
            port=int(port),
            user=username,
            password=password,
            database=database
        )
        
        # Busca todos os bancos cadastrados
        rows = await conn.fetch("""
            SELECT id, name, description, type, host, port, database_name, username, password, status
            FROM databases
        """)
        
        databases = []
        for row in rows:
            databases.append({
                'id': row['id'],
                'name': row['name'],
                'description': row['description'],
                'type': row['type'],
                'host': row['host'],
                'port': row['port'],
                'database_name': row['database_name'],
                'username': row['username'],
                'password': row['password'],
                'status': row['status']
            })
        
        await conn.close()
        return databases
        
    except Exception as e:
        print(f"Erro ao obter bancos do banco principal: {str(e)}")
        return []

async def create_product_table_for_database(db_config):
    """
    Cria a tabela de produtos com sequence para um banco de dados específico
    """
    try:
        # Conectar ao banco de dados alvo
        conn = await asyncpg.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database_name'],
            user=db_config['username'],
            password=db_config['password']
        )
        
        print(f"Conectado ao banco {db_config['database_name']} em {db_config['host']}:{db_config['port']}")
        
        # Criar sequence para o ID do produto
        await conn.execute("""
            CREATE SEQUENCE IF NOT EXISTS product_id_seq
            START WITH 1
            INCREMENT BY 1
            NO MINVALUE
            NO MAXVALUE
            CACHE 1;
        """)
        
        # Criar tabela de produtos
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY DEFAULT nextval('product_id_seq'),
                name VARCHAR(255) NOT NULL,
                description TEXT,
                price DECIMAL(10,2) NOT NULL,
                category VARCHAR(100),
                stock_quantity INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Inserir dados de exemplo
        sample_products = [
            ("Notebook Dell Inspiron 15", "Notebook Dell Inspiron 15 com Intel Core i5, 8GB RAM, 256GB SSD", 2499.99, "Eletrônicos", 15),
            ("Smartphone Samsung Galaxy S23", "Smartphone Samsung Galaxy S23 128GB, 8GB RAM, Câmera Tripla", 1899.99, "Eletrônicos", 25),
            ("Mouse Logitech MX Master 3", "Mouse sem fio Logitech MX Master 3 com sensor Darkfield", 299.99, "Periféricos", 50),
            ("Teclado Mecânico Redragon", "Teclado mecânico Redragon Kumara com switches Outemu Blue", 199.99, "Periféricos", 30),
            ("Monitor LG 24\" Full HD", "Monitor LG 24 polegadas Full HD IPS, 75Hz", 699.99, "Monitores", 20),
            ("Cadeira Gamer DXRacer", "Cadeira gamer DXRacer com ajuste de altura e reclinação", 1299.99, "Móveis", 10),
            ("Headset HyperX Cloud II", "Headset HyperX Cloud II com som surround 7.1", 399.99, "Áudio", 40),
            ("Webcam Logitech C920", "Webcam Logitech C920 HD Pro com 1080p", 299.99, "Vídeo", 35),
            ("SSD Kingston 500GB", "SSD Kingston NV1 500GB NVMe PCIe", 249.99, "Armazenamento", 60),
            ("Placa de Vídeo RTX 3060", "Placa de vídeo NVIDIA GeForce RTX 3060 12GB", 2199.99, "Hardware", 8)
        ]
        
        for product in sample_products:
            await conn.execute("""
                INSERT INTO products (name, description, price, category, stock_quantity)
                VALUES ($1, $2, $3, $4, $5)
            """, product[0], product[1], product[2], product[3], product[4])
        
        print(f"Tabela 'products' criada e populada com {len(sample_products)} produtos no banco {db_config['database_name']}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"Erro ao criar tabela no banco {db_config['database_name']}: {str(e)}")
        return False

async def main():
    """
    Função principal que executa o script
    """
    try:
        # Obter lista de bancos cadastrados
        databases = await get_databases_from_main_db()
        
        if not databases:
            print("Nenhum banco de dados encontrado na tabela 'databases'")
            return
        
        print(f"Encontrados {len(databases)} bancos de dados cadastrados")
        
        # Para cada banco cadastrado, criar a tabela de produtos
        for db in databases:
            print(f"\nProcessando banco: {db['name']} ({db['database_name']})")
            success = await create_product_table_for_database(db)
            
            if success:
                print(f"[SUCESSO] Tabela de produtos criada com sucesso em {db['database_name']}")
            else:
                print(f"[ERRO] Falha ao criar tabela em {db['database_name']}")
        
        print("\nScript concluído!")
        
    except Exception as e:
        print(f"Erro durante execução do script: {str(e)}")

if __name__ == "__main__":
    # Executar o script assíncrono
    asyncio.run(main())