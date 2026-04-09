#!/usr/bin/env python3
"""
Script para gerar script SQL de migração para:
1. Criação da tabela organizations_projects
2. Popular tabelas com informações existentes
3. Inclusão de novas colunas na tabela users
4. Inclusão da coluna aiq nas tabelas organizations e projects
"""

import os
from datetime import datetime

def generate_sql_migration():
    """Gera script SQL completo de migração"""
    
    # Timestamp para nome do arquivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Usar caminho absoluto baseado no diretório atual
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    output_file = os.path.join(project_root, "server", "exports", f"migration_{timestamp}.sql")
    
    # Garantir que o diretório exports existe
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    sql_content = f"""-- Script de Migração - {timestamp}
-- Este script cria a estrutura necessária para o sistema de dropdowns e AIQ

-- =============================================
-- 1. CRIAR TABELA ORGANIZATIONS_PROJECTS
-- =============================================

CREATE TABLE IF NOT EXISTS organizations_projects (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(organization_id, project_id),
    
    -- Foreign keys
    CONSTRAINT fk_organization 
        FOREIGN KEY (organization_id) 
        REFERENCES organizations(id) 
        ON DELETE CASCADE,
        
    CONSTRAINT fk_project 
        FOREIGN KEY (project_id) 
        REFERENCES projects(id) 
        ON DELETE CASCADE
);

-- =============================================
-- 2. POPULAR TABELAS COM DADOS DE EXEMPLO
-- =============================================

-- Inserir organização de exemplo
INSERT INTO organizations (name, aiq, created_at, updated_at)
VALUES
    ('Tech Solutions Ltda', 150, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (name) DO UPDATE SET
    aiq = EXCLUDED.aiq,
    updated_at = CURRENT_TIMESTAMP;

-- Inserir projeto de exemplo
INSERT INTO projects (name, organization_id, aiq, created_at, updated_at)
VALUES
    ('Sistema de Gestão', (SELECT id FROM organizations WHERE name = 'Tech Solutions Ltda'), 175, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (name, organization_id) DO UPDATE SET
    aiq = EXCLUDED.aiq,
    updated_at = CURRENT_TIMESTAMP;

-- Inserir relacionamento na tabela organizations_projects
INSERT INTO organizations_projects (organization_id, project_id)
VALUES
    ((SELECT id FROM organizations WHERE name = 'Tech Solutions Ltda'),
     (SELECT id FROM projects WHERE name = 'Sistema de Gestão'))
ON CONFLICT (organization_id, project_id) DO NOTHING;

-- =============================================
-- 3. ADICIONAR NOVAS COLUNAS NA TABELA USERS
-- =============================================

-- Adicionar coluna aiq (Artificial Intelligence Quocient)
ALTER TABLE users ADD COLUMN IF NOT EXISTS aiq INTEGER DEFAULT 100;

-- Adicionar coluna account_type para armazenar o tipo de conta selecionada
ALTER TABLE users ADD COLUMN IF NOT EXISTS account_type VARCHAR(50) DEFAULT 'personal';

-- Adicionar coluna selected_organization_id para armazenar a organização selecionada
ALTER TABLE users ADD COLUMN IF NOT EXISTS selected_organization_id INTEGER;

-- Adicionar coluna selected_project_id para armazenar o projeto selecionado
ALTER TABLE users ADD COLUMN IF NOT EXISTS selected_project_id INTEGER;

-- Adicionar foreign keys para as colunas de seleção
ALTER TABLE users 
ADD CONSTRAINT fk_selected_organization 
FOREIGN KEY (selected_organization_id) 
REFERENCES organizations(id);

ALTER TABLE users 
ADD CONSTRAINT fk_selected_project 
FOREIGN KEY (selected_project_id) 
REFERENCES projects(id);

-- =============================================
-- 4. ADICIONAR COLUNA AIQ NAS TABELAS ORGANIZATIONS E PROJECTS
-- =============================================

-- Adicionar coluna aiq na tabela organizations
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS aiq INTEGER DEFAULT 100;

-- Adicionar coluna aiq na tabela projects
ALTER TABLE projects ADD COLUMN IF NOT EXISTS aiq INTEGER DEFAULT 100;

-- =============================================
-- 5. POPULAR VALORES AIQ ALEATÓRIOS (70-200)
-- =============================================

-- Popular valores AIQ aleatórios para usuários
UPDATE users 
SET aiq = FLOOR(RANDOM() * (200 - 70 + 1) + 70)
WHERE aiq IS NULL OR aiq = 100;

-- Popular valores AIQ aleatórios para organizações
UPDATE organizations 
SET aiq = FLOOR(RANDOM() * (200 - 70 + 1) + 70)
WHERE aiq IS NULL OR aiq = 100;

-- Popular valores AIQ aleatórios para projetos
UPDATE projects 
SET aiq = FLOOR(RANDOM() * (200 - 70 + 1) + 70)
WHERE aiq IS NULL OR aiq = 100;

-- =============================================
-- 6. CRIAR ÍNDICES PARA MELHOR PERFORMANCE
-- =============================================

-- Índices para a tabela organizations_projects
CREATE INDEX IF NOT EXISTS idx_organizations_projects_org_id 
ON organizations_projects(organization_id);

CREATE INDEX IF NOT EXISTS idx_organizations_projects_project_id 
ON organizations_projects(project_id);

-- Índices para as novas colunas na tabela users
CREATE INDEX IF NOT EXISTS idx_users_account_type 
ON users(account_type);

CREATE INDEX IF NOT EXISTS idx_users_selected_org 
ON users(selected_organization_id);

CREATE INDEX IF NOT EXISTS idx_users_selected_project 
ON users(selected_project_id);

-- Índices para a coluna aiq
CREATE INDEX IF NOT EXISTS idx_users_aiq 
ON users(aiq);

CREATE INDEX IF NOT EXISTS idx_organizations_aiq 
ON organizations(aiq);

CREATE INDEX IF NOT EXISTS idx_projects_aiq 
ON projects(aiq);

-- =============================================
-- 7. INSERIR DADOS DE EXEMPLO PARA TESTE
-- =============================================

-- Inserir usuário de teste se não existir
INSERT INTO users (firebase_uid, email, first_name, last_name, aiq, account_type, created_at, updated_at)
VALUES
    ('JJ9t5xjMIAdbsmM86U2oLHGDGu62', 'jan.pereira@example.com', 'Jan', 'Pereira', 120, 'personal', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (firebase_uid) DO UPDATE SET
    aiq = EXCLUDED.aiq,
    account_type = EXCLUDED.account_type,
    updated_at = CURRENT_TIMESTAMP;

-- organization_members table removed
    ((SELECT id FROM users WHERE firebase_uid = 'JJ9t5xjMIAdbsmM86U2oLHGDGu62'),
     (SELECT id FROM organizations WHERE name = 'Tech Solutions Ltda'),
     'member', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (user_id, organization_id) DO UPDATE SET
    updated_at = CURRENT_TIMESTAMP;

-- Inserir usuário no projeto (project_members)
INSERT INTO project_members (user_id, project_id, role, created_at, updated_at)
VALUES
    ((SELECT id FROM users WHERE firebase_uid = 'JJ9t5xjMIAdbsmM86U2oLHGDGu62'),
     (SELECT id FROM projects WHERE name = 'Sistema de Gestão'),
     'developer', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (user_id, project_id) DO UPDATE SET
    updated_at = CURRENT_TIMESTAMP;

-- =============================================
-- 8. ATUALIZAR DADOS DE TESTE PARA USUÁRIO ESPECÍFICO
-- =============================================

-- Atualizar dados para o usuário de teste (firebase_uid = JJ9t5xjMIAdbsmM86U2oLHGDGu62)
UPDATE users
SET
    aiq = 120,
    account_type = 'personal',
    selected_organization_id = NULL,
    selected_project_id = NULL
WHERE firebase_uid = 'JJ9t5xjMIAdbsmM86U2oLHGDGu62';

-- =============================================
-- 9. VERIFICAÇÃO FINAL
-- =============================================

-- Verificar se todas as alterações foram aplicadas
SELECT
    'users' as tabela,
    COUNT(*) as total_linhas,
    AVG(aiq) as media_aiq,
    COUNT(CASE WHEN account_type IS NOT NULL THEN 1 END) as com_account_type
FROM users
UNION ALL
SELECT
    'organizations' as tabela,
    COUNT(*) as total_linhas,
    AVG(aiq) as media_aiq,
    NULL as com_account_type
FROM organizations
UNION ALL
SELECT
    'projects' as tabela,
    COUNT(*) as total_linhas,
    AVG(aiq) as media_aiq,
    NULL as com_account_type
FROM projects
UNION ALL
SELECT
    'organizations_projects' as tabela,
    COUNT(*) as total_linhas,
    NULL as media_aiq,
    NULL as com_account_type
FROM organizations_projects
UNION ALL
SELECT
    'organization_members' as tabela,
    COUNT(*) as total_linhas,
    NULL as media_aiq,
    NULL as com_account_type
FROM organization_members
UNION ALL
SELECT
    'project_members' as tabela,
    COUNT(*) as total_linhas,
    NULL as media_aiq,
    NULL as com_account_type
FROM project_members;

-- Script finalizado com sucesso!
"""

    # Escrever o conteúdo no arquivo
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(sql_content)
    
    print(f"Script SQL gerado com sucesso: {output_file}")
    print(f"Total de linhas: {len(sql_content.split(chr(10)))}")
    
    return output_file

if __name__ == "__main__":
    output_file = generate_sql_migration()
    print(f"Execute o script SQL no seu banco de dados PostgreSQL:")
    print(f"   psql -h localhost -U postgres -d saphien -f {output_file}")