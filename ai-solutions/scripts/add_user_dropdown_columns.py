"""
Script para adicionar colunas de configuração do dropdown na tabela users
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, text
from sqlalchemy import create_engine
from core.config.settings import settings

# Criar engine síncrono para operações de schema
engine = create_engine(settings.POSTGRES_URL.replace("postgresql+asyncpg", "postgresql"))

def add_dropdown_columns():
    """Adiciona colunas para armazenar configurações do dropdown do usuário"""
    try:
        with Session(engine) as session:
            # Verificar se as colunas já existem
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name IN ('account_type', 'selected_organization_id', 'selected_project_id')
            """)
            existing_columns = session.execute(check_query).fetchall()
            existing_column_names = [col[0] for col in existing_columns]
            
            print(f"Colunas existentes: {existing_column_names}")
            
            # Adicionar colunas que não existem
            if 'account_type' not in existing_column_names:
                session.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN account_type VARCHAR(20) DEFAULT 'personal'
                """))
                print("Coluna 'account_type' adicionada")
            
            if 'selected_organization_id' not in existing_column_names:
                session.execute(text("""
                    ALTER TABLE users
                    ADD COLUMN selected_organization_id INTEGER,
                    ADD CONSTRAINT fk_user_organization
                    FOREIGN KEY (selected_organization_id) REFERENCES organizations(id)
                """))
                print("Coluna 'selected_organization_id' adicionada")
            
            if 'selected_project_id' not in existing_column_names:
                session.execute(text("""
                    ALTER TABLE users
                    ADD COLUMN selected_project_id INTEGER,
                    ADD CONSTRAINT fk_user_project
                    FOREIGN KEY (selected_project_id) REFERENCES projects(id)
                """))
                print("Coluna 'selected_project_id' adicionada")
            
            session.commit()
            print("Todas as colunas foram adicionadas com sucesso!")
            
    except Exception as e:
        print(f"Erro ao adicionar colunas: {e}")
        raise

if __name__ == "__main__":
    add_dropdown_columns()