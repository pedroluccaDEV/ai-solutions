#!/usr/bin/env python3
"""
Script para adicionar colunas AIQ nas tabelas users, organizations e projects
e popular dados de teste.
"""

import os
import sys
import psycopg2
import random
from datetime import datetime

# Configuração do banco de dados
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'saphien',
    'user': 'postgres',
    'password': 'qwe321'
}

def get_db_connection():
    """Estabelece conexão com o banco de dados"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        sys.exit(1)

def add_aiq_columns():
    """Adiciona colunas AIQ nas tabelas necessárias"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Adicionar coluna AIQ na tabela users
        cursor.execute("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS aiq INTEGER DEFAULT floor(random() * 131 + 70)
        """)
        
        # Adicionar coluna AIQ na tabela organizations
        cursor.execute("""
            ALTER TABLE organizations 
            ADD COLUMN IF NOT EXISTS aiq INTEGER DEFAULT floor(random() * 131 + 70)
        """)
        
        # Adicionar coluna AIQ na tabela projects
        cursor.execute("""
            ALTER TABLE projects 
            ADD COLUMN IF NOT EXISTS aiq INTEGER DEFAULT floor(random() * 131 + 70)
        """)
        
        conn.commit()
        print("Colunas AIQ adicionadas com sucesso!")
        
    except Exception as e:
        conn.rollback()
        print(f"Erro ao adicionar colunas AIQ: {e}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

def populate_test_data():
    """Popula dados de teste para organizações e projetos"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Verificar se o usuário de teste existe
        cursor.execute("SELECT id, nome, sobrenome FROM users WHERE firebase_uid = 'JJ9t5xjMIAdbsmM86U2oLHGDGu62'")
        user = cursor.fetchone()
        
        if not user:
            print("Usuário de teste não encontrado. Criando usuário...")
            cursor.execute("""
                INSERT INTO users (firebase_uid, email, nome, sobrenome, role, is_active, created_at, updated_at)
                VALUES ('JJ9t5xjMIAdbsmM86U2oLHGDGu62', 'test@example.com', 'João', 'Silva', 'user', true, NOW(), NOW())
                RETURNING id
            """)
            user_id = cursor.fetchone()[0]
            print(f"Usuário de teste criado com ID: {user_id}")
        else:
            user_id = user[0]
            print(f"Usuário de teste encontrado: {user[1]} {user[2]} (ID: {user_id})")
        
        # Criar organização de teste se não existir
        cursor.execute("SELECT id, name FROM organizations WHERE name = 'Organização Teste'")
        org = cursor.fetchone()
        
        if not org:
            cursor.execute("""
                INSERT INTO organizations (name, description, user_id, created_by, created_at)
                VALUES ('Organização Teste', 'Organização de teste para desenvolvimento', %s, %s, NOW())
                RETURNING id
            """, (user_id, user_id))
            org_id = cursor.fetchone()[0]
            print(f"Organização de teste criada com ID: {org_id}")
        else:
            org_id = org[0]
            print(f"Organização de teste encontrada: {org[1]} (ID: {org_id})")
        
        # Adicionar usuário à organização
        cursor.execute("""
            -- organization_members table removed
            ON CONFLICT (organization_id, user_id) DO NOTHING
        """, (org_id, user_id))
        
        # Criar projeto de teste se não existir
        cursor.execute("SELECT id, name FROM projects WHERE name = 'Projeto Teste'")
        project = cursor.fetchone()
        
        if not project:
            cursor.execute("""
                INSERT INTO projects (name, description, organization_id, created_by, is_active, created_at, updated_at)
                VALUES ('Projeto Teste', 'Projeto de teste para desenvolvimento', %s, %s, true, NOW(), NOW())
                RETURNING id
            """, (org_id, user_id))
            project_id = cursor.fetchone()[0]
            print(f"Projeto de teste criado com ID: {project_id}")
        else:
            project_id = project[0]
            print(f"Projeto de teste encontrado: {project[1]} (ID: {project_id})")
        
        # Adicionar usuário ao projeto
        cursor.execute("""
            INSERT INTO project_members (user_id, project_id, status, created_at, updated_at)
            VALUES (%s, %s, 'active', NOW(), NOW())
            ON CONFLICT (user_id, project_id) DO NOTHING
        """, (user_id, project_id))
        
        # Atualizar valores AIQ com valores aleatórios entre 70 e 200
        cursor.execute("""
            UPDATE users SET aiq = floor(random() * 131 + 70) WHERE id = %s
        """, (user_id,))
        
        cursor.execute("""
            UPDATE organizations SET aiq = floor(random() * 131 + 70) WHERE id = %s
        """, (org_id,))
        
        cursor.execute("""
            UPDATE projects SET aiq = floor(random() * 131 + 70) WHERE id = %s
        """, (project_id,))
        
        conn.commit()
        print("Dados de teste populados com sucesso!")
        
        # Mostrar os valores AIQ gerados
        cursor.execute("""
            SELECT
                u.aiq as user_aiq,
                o.aiq as org_aiq,
                p.aiq as project_aiq
            FROM users u
            LEFT JOIN organizations o ON u.id = o.created_by
            LEFT JOIN project_members pm ON u.id = pm.user_id
            LEFT JOIN projects p ON pm.project_id = p.id
            WHERE u.id = %s
        """, (user_id,))
        
        result = cursor.fetchone()
        if result:
            print(f"Valores AIQ gerados:")
            print(f"   Usuário: {result[0]}")
            print(f"   Organização: {result[1]}")
            print(f"   Projeto: {result[2]}")
        
    except Exception as e:
        conn.rollback()
        print(f"Erro ao popular dados de teste: {e}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

def main():
    """Função principal"""
    print("Iniciando configuração das colunas AIQ...")
    
    # Adicionar colunas AIQ
    add_aiq_columns()
    
    # Popular dados de teste
    populate_test_data()
    
    print("Configuração concluída com sucesso!")

if __name__ == "__main__":
    main()