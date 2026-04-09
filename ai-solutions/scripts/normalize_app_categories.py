#!/usr/bin/env python3
"""
Script para normalizar as categorias dos apps na tabela apps do PostgreSQL.
Converte categorias para português, com inicial maiúscula e remove underscores.
"""

import psycopg2
import sys
from typing import Dict, Optional

# Configuração de conexão com o PostgreSQL
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'saphien',
    'user': 'postgres',
    'password': 'root'
}

# Mapeamento de categorias para português
CATEGORY_MAPPING = {
    # Inglês para Português
    'storage': 'Armazenamento',
    'project_management': 'Gestão de Projetos',
    'communication': 'Comunicação',
    'development': 'Desenvolvimento',
    'productivity': 'Produtividade',
    'automation': 'Automação',
    'integration': 'Integração',
    'analytics': 'Análise',
    'marketing': 'Marketing',
    'finance': 'Finanças',
    'hr': 'Recursos Humanos',
    'sales': 'Vendas',
    'support': 'Suporte',
    'design': 'Design',
    'education': 'Educação',
    'entertainment': 'Entretenimento',
    'health': 'Saúde',
    'travel': 'Viagem',
    'ecommerce': 'E-commerce',
    'social': 'Social',
    'utilities': 'Utilitários',
    'security': 'Segurança',
    'iot': 'IoT',
    'ai': 'Inteligência Artificial',
    'ml': 'Aprendizado de Máquina',
    'blockchain': 'Blockchain',
    'gaming': 'Jogos',
    
    # Português - correções e padronização
    'gestao de projetos': 'Gestão de Projetos',
    'gestão de projetos': 'Gestão de Projetos',
    'comunicação': 'Comunicação',
    'desenvolvimento': 'Desenvolvimento',
    'produtividade': 'Produtividade',
    'automação': 'Automação',
    'integração': 'Integração',
    'análise': 'Análise',
    'recursos humanos': 'Recursos Humanos',
    'e-commerce': 'E-commerce',
    'inteligência artificial': 'Inteligência Artificial',
    'aprendizado de máquina': 'Aprendizado de Máquina',
    
    # Outros casos comuns
    'other': 'Outros',
    'others': 'Outros',
    'misc': 'Diversos',
    'miscellaneous': 'Diversos',
    'general': 'Geral',
    'tools': 'Ferramentas',
    'api': 'API',
    'web': 'Web',
    'mobile': 'Mobile',
    'desktop': 'Desktop',
    'cloud': 'Nuvem',
    'database': 'Banco de Dados',
    'testing': 'Testes',
    'monitoring': 'Monitoramento',
    'logging': 'Logs',
    'documentation': 'Documentação',
    'deployment': 'Deploy',
    'ci_cd': 'CI/CD',
    'devops': 'DevOps',
    'backend': 'Backend',
    'frontend': 'Frontend',
    'fullstack': 'Full Stack'
}

def normalize_category_name(category: Optional[str]) -> str:
    """
    Normaliza o nome da categoria para português com inicial maiúscula.
    
    Args:
        category: Nome da categoria original
        
    Returns:
        Nome da categoria normalizado
    """
    if not category:
        return 'Integração'
    
    # Remove espaços extras e converte para minúsculas
    category = category.strip().lower()
    
    # Remove underscores e substitui por espaços
    category = category.replace('_', ' ')
    
    # Remove espaços extras
    category = ' '.join(category.split())
    
    # Verifica se há mapeamento direto
    if category in CATEGORY_MAPPING:
        return CATEGORY_MAPPING[category]
    
    # Tenta mapear partes da categoria
    for key, value in CATEGORY_MAPPING.items():
        if key in category:
            return value
    
    # Se não houver mapeamento, capitaliza a primeira letra de cada palavra
    words = category.split()
    normalized_words = []
    
    for word in words:
        if word in CATEGORY_MAPPING:
            normalized_words.append(CATEGORY_MAPPING[word])
        else:
            # Capitaliza a primeira letra
            normalized_words.append(word.capitalize())
    
    return ' '.join(normalized_words)

def get_current_categories(conn) -> Dict[str, int]:
    """
    Obtém as categorias atuais e a contagem de apps por categoria.
    
    Args:
        conn: Conexão com o banco de dados
        
    Returns:
        Dicionário com categorias e contagem
    """
    cursor = conn.cursor()
    
    query = """
    SELECT category, COUNT(*) as count 
    FROM apps 
    WHERE category IS NOT NULL 
    GROUP BY category 
    ORDER BY count DESC
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    categories = {}
    for category, count in results:
        categories[category] = count
    
    cursor.close()
    return categories

def update_app_categories(conn):
    """
    Atualiza as categorias dos apps no banco de dados.
    
    Args:
        conn: Conexão com o banco de dados
    """
    cursor = conn.cursor()
    
    # Primeiro, obtém todos os apps
    cursor.execute("SELECT id, category FROM apps WHERE category IS NOT NULL")
    apps = cursor.fetchall()
    
    updates = []
    for app_id, current_category in apps:
        normalized_category = normalize_category_name(current_category)
        
        if normalized_category != current_category:
            updates.append((app_id, normalized_category, current_category))
    
    if not updates:
        print("Nenhuma categoria precisa ser atualizada.")
        return
    
    print(f"Encontradas {len(updates)} categorias para normalizar:")
    
    # Executa as atualizações
    for app_id, new_category, old_category in updates:
        cursor.execute(
            "UPDATE apps SET category = %s WHERE id = %s",
            (new_category, app_id)
        )
        print(f"  '{old_category}' -> '{new_category}'")
    
    conn.commit()
    cursor.close()
    
    print(f"\n{len(updates)} categorias foram normalizadas com sucesso!")

def show_category_statistics(conn, before_update: bool = True):
    """
    Exibe estatísticas das categorias.
    
    Args:
        conn: Conexão com o banco de dados
        before_update: Se True, mostra estatísticas antes da atualização
    """
    stage = "ANTES" if before_update else "DEPOIS"
    print(f"\nESTATISTICAS {stage} DA ATUALIZACAO:")
    print("=" * 50)
    
    categories = get_current_categories(conn)
    total_apps = sum(categories.values())
    
    print(f"Total de apps com categoria: {total_apps}")
    print(f"Total de categorias unicas: {len(categories)}")
    print("\nTop 10 categorias:")
    print("-" * 30)
    
    for i, (category, count) in enumerate(list(categories.items())[:10]):
        normalized = normalize_category_name(category)
        status = "[OK]" if category == normalized else "[ATUALIZAR]"
        print(f"{i+1:2d}. {status} {category} -> {normalized} ({count} apps)")
    
    if len(categories) > 10:
        print(f"... e mais {len(categories) - 10} categorias")

def main():
    """Função principal do script."""
    try:
        print("Iniciando normalização de categorias de apps...")
        
        # Conecta ao banco de dados
        conn = psycopg2.connect(**DB_CONFIG)
        print("Conectado ao banco de dados PostgreSQL")
        
        # Mostra estatísticas antes da atualização
        show_category_statistics(conn, before_update=True)
        
        # Executa a atualização automaticamente
        print("\nExecutando atualização automática das categorias...")
        update_app_categories(conn)
        
        # Mostra estatísticas depois da atualização
        show_category_statistics(conn, before_update=False)
        
        # Fecha a conexão
        conn.close()
        print("\nScript executado com sucesso!")
        
    except psycopg2.Error as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Erro inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()