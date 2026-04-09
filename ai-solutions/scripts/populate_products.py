import asyncio
import asyncpg
import random
from datetime import datetime, timedelta
from typing import List, Dict

class ProductPopulator:
    def __init__(self):
        # Configurações do banco de dados da Loja Virtual
        self.db_config = {
            "host": "localhost",
            "port": 5433,
            "database": "user_JJ9t5xjMIAdbsmM86U2oLHGDGu62",
            "schema": "loja",
            "user": "postgres",
            "password": "root"
        }
        
        # Dados de exemplo para produtos
        self.categories = [
            "Eletronicos", "Roupas", "Casa e Decoracao", "Esportes", 
            "Livros", "Beleza", "Brinquedos", "Automotivo", "Saude", "Alimentacao"
        ]
        
        self.brands = [
            "Sony", "Samsung", "Apple", "Nike", "Adidas", "LG", "Philips",
            "Dell", "HP", "Lenovo", "Canon", "Nikon", "Bosch", "Electrolux"
        ]
        
        self.product_names = [
            "Smartphone", "Notebook", "TV LED", "Fone de Ouvido", "Tablet",
            "Camera Digital", "Smartwatch", "Console de Videogame", "Impressora",
            "Monitor", "Teclado", "Mouse", "Caixa de Som", "Carregador Portatil",
            "HD Externo", "SSD", "Memoria RAM", "Placa de Video", "Processador",
            "Placa-mae", "Fonte de Alimentacao", "Gabinete", "Cooler", "Webcam"
        ]

    async def create_connection(self):
        """Cria conexao com o banco de dados"""
        try:
            conn = await asyncpg.connect(
                host=self.db_config["host"],
                port=self.db_config["port"],
                user=self.db_config["user"],
                password=self.db_config["password"],
                database=self.db_config["database"]
            )
            print("Conexao com o banco de dados estabelecida com sucesso!")
            return conn
        except Exception as e:
            print(f"Erro ao conectar ao banco de dados: {e}")
            return None

    async def create_products_table(self, conn):
        """Cria a tabela products se nao existir"""
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.db_config["schema"]}.products (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            category VARCHAR(100) NOT NULL,
            brand VARCHAR(100),
            price DECIMAL(10,2) NOT NULL,
            stock_quantity INTEGER DEFAULT 0,
            sku VARCHAR(100) UNIQUE,
            weight_kg DECIMAL(8,3),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_products_category ON {self.db_config["schema"]}.products(category);
        CREATE INDEX IF NOT EXISTS idx_products_brand ON {self.db_config["schema"]}.products(brand);
        CREATE INDEX IF NOT EXISTS idx_products_price ON {self.db_config["schema"]}.products(price);
        CREATE INDEX IF NOT EXISTS idx_products_active ON {self.db_config["schema"]}.products(is_active);
        """
        
        try:
            await conn.execute(create_table_sql)
            print("Tabela 'products' criada/verificada com sucesso!")
            return True
        except Exception as e:
            print(f"Erro ao criar tabela: {e}")
            return False

    def generate_product_data(self, count: int = 100) -> List[Dict]:
        """Gera dados de produtos de exemplo"""
        products = []
        
        for i in range(1, count + 1):
            category = random.choice(self.categories)
            brand = random.choice(self.brands)
            product_name = random.choice(self.product_names)
            
            product = {
                "name": f"{brand} {product_name} {i}",
                "description": f"Descricao do produto {brand} {product_name} {i}. Produto de alta qualidade com garantia.",
                "category": category,
                "brand": brand,
                "price": round(random.uniform(50.0, 2000.0), 2),
                "stock_quantity": random.randint(0, 500),
                "sku": f"SKU-{brand.upper()}-{i:04d}",
                "weight_kg": round(random.uniform(0.1, 10.0), 3),
                "is_active": random.choice([True, True, True, False])  # 75% ativos
            }
            products.append(product)
        
        return products

    async def insert_products(self, conn, products: List[Dict]):
        """Insere produtos na tabela"""
        insert_sql = f"""
        INSERT INTO {self.db_config["schema"]}.products 
        (name, description, category, brand, price, stock_quantity, sku, weight_kg, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ON CONFLICT (sku) DO NOTHING
        """
        
        inserted_count = 0
        for product in products:
            try:
                await conn.execute(
                    insert_sql,
                    product["name"],
                    product["description"],
                    product["category"],
                    product["brand"],
                    product["price"],
                    product["stock_quantity"],
                    product["sku"],
                    product["weight_kg"],
                    product["is_active"]
                )
                inserted_count += 1
            except Exception as e:
                print(f"Erro ao inserir produto {product['sku']}: {e}")
        
        return inserted_count

    async def count_products(self, conn) -> int:
        """Conta o numero de produtos na tabela"""
        try:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {self.db_config["schema"]}.products")
            return count
        except Exception as e:
            print(f"Erro ao contar produtos: {e}")
            return 0

    async def run(self):
        """Executa o processo completo de populacao de produtos"""
        print("Iniciando processo de populacao de produtos...")
        
        # Conectar ao banco de dados
        conn = await self.create_connection()
        if not conn:
            return
        
        try:
            # Criar tabela
            if not await self.create_products_table(conn):
                return
            
            # Verificar se ja existem produtos
            current_count = await self.count_products(conn)
            print(f"Produtos existentes na tabela: {current_count}")
            
            if current_count >= 100:
                print("Tabela ja possui produtos suficientes. Nenhuma acao necessaria.")
                return
            
            # Gerar dados de produtos
            print("Gerando dados de 100 produtos...")
            products = self.generate_product_data(100)
            
            # Inserir produtos
            print("Inserindo produtos na tabela...")
            inserted_count = await self.insert_products(conn, products)
            
            # Verificar resultado final
            final_count = await self.count_products(conn)
            
            print(f"Processo concluido!")
            print(f"Produtos inseridos: {inserted_count}")
            print(f"Total de produtos na tabela: {final_count}")
            
            if inserted_count < 100:
                print(f"Apenas {inserted_count} produtos foram inseridos (alguns SKUs podem ter conflitos)")
            
        except Exception as e:
            print(f"Erro durante o processo: {e}")
        finally:
            await conn.close()
            print("Conexao com o banco de dados fechada.")

async def main():
    """Funcao principal"""
    populator = ProductPopulator()
    await populator.run()

if __name__ == "__main__":
    # Executar o script
    asyncio.run(main())