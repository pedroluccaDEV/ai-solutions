#!/usr/bin/env python3
"""
Script para exportar os dados da tabela providers_apikeys para arquivo SQL.
Gera comandos INSERT para todos os registros da tabela.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

def connect_to_postgres():
    """
    Conecta ao PostgreSQL usando psycopg2
    Retorna uma conexão e cursor
    """
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        # Configuração de conexão
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="saphien",
            user="postgres",
            password="qwe321"
        )
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        return conn, cursor
        
    except ImportError:
        print("Erro: psycopg2 não está disponível")
        return None, None
    except Exception as e:
        print(f"Erro ao conectar ao PostgreSQL: {e}")
        return None, None

def generate_insert_statements(data):
    """
    Gera comandos INSERT a partir dos dados da tabela
    """
    if not data:
        return "-- Tabela providers_apikeys está vazia\n"
    
    insert_statements = []
    
    for row in data:
        # Construir a lista de colunas
        columns = list(row.keys())
        
        # Construir a lista de valores, escapando strings apropriadamente
        values = []
        for col in columns:
            value = row[col]
            if value is None:
                values.append("NULL")
            elif isinstance(value, str):
                # Escapar aspas simples
                escaped_value = value.replace("'", "''")
                values.append(f"'{escaped_value}'")
            elif isinstance(value, bool):
                values.append("TRUE" if value else "FALSE")
            else:
                values.append(str(value))
        
        # Gerar o comando INSERT
        columns_str = ", ".join(columns)
        values_str = ", ".join(values)
        
        insert_sql = f"INSERT INTO providers_apikeys ({columns_str}) VALUES ({values_str});"
        insert_statements.append(insert_sql)
    
    return "\n".join(insert_statements)

def export_providers_apikeys():
    """
    Exporta os dados da tabela providers_apikeys para arquivo SQL
    """
    print("Iniciando exportação da tabela providers_apikeys...")
    
    # Configurar caminhos
    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    exports_dir = project_root / "exports"
    
    # Criar diretório se não existir
    exports_dir.mkdir(exist_ok=True)
    
    # Nome do arquivo com timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = exports_dir / f"providers_apikeys_export_{timestamp}.sql"
    
    print(f"Diretório de destino: {exports_dir}")
    print(f"Arquivo de saída: {output_file.name}")
    
    try:
        # Conectar ao PostgreSQL via psycopg2
        conn, cursor = connect_to_postgres()
        if not conn or not cursor:
            print("Erro: Não foi possível conectar ao PostgreSQL")
            return False
        
        # Consultar dados da tabela
        print("Consultando dados da tabela providers_apikeys...")
        
        # Primeiro, obter todos os dados da tabela
        cursor.execute("SELECT * FROM providers_apikeys ORDER BY id")
        query_result = cursor.fetchall()
        
        if not query_result:
            print("A tabela providers_apikeys está vazia")
            sql_content = f"""-- Exportação da tabela providers_apikeys
-- Data: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
-- Status: Tabela vazia

-- Estrutura da tabela:
-- CREATE TABLE providers_apikeys (
--     id SERIAL PRIMARY KEY,
--     id_provider INTEGER NOT NULL,
--     url VARCHAR NOT NULL,
--     apikey VARCHAR NOT NULL,
--     created_at TIMESTAMP NOT NULL,
--     updated_at TIMESTAMP NOT NULL,
--     status BOOLEAN NOT NULL
-- );

-- Nenhum dado encontrado para exportação.
"""
        else:
            print(f"Encontrados {len(query_result)} registros")
            
            # Gerar conteúdo SQL
            sql_content = f"""-- Exportação da tabela providers_apikeys
-- Data: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
-- Total de registros: {len(query_result)}

-- Estrutura da tabela:
-- CREATE TABLE providers_apikeys (
--     id SERIAL PRIMARY KEY,
--     id_provider INTEGER NOT NULL,
--     url VARCHAR NOT NULL,
--     apikey VARCHAR NOT NULL,
--     created_at TIMESTAMP NOT NULL,
--     updated_at TIMESTAMP NOT NULL,
--     status BOOLEAN NOT NULL
-- );

-- Dados:
{generate_insert_statements(query_result)}

-- Exportação concluída com sucesso.
"""
        
        # Escrever arquivo
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(sql_content)
        
        # Fechar conexão
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        
        print(f"Exportação concluída com sucesso!")
        print(f"Arquivo gerado: {output_file}")
        print(f"Tamanho do arquivo: {output_file.stat().st_size} bytes")
        
        return True
        
    except Exception as e:
        print(f"Erro durante a exportação: {e}")
        return False

def main():
    """Função principal"""
    print("=" * 60)
    print("EXPORTADOR DE PROVIDERS_APIKEYS - SAPHIEN")
    print("=" * 60)
    
    success = export_providers_apikeys()
    
    if success:
        print("Exportação finalizada com sucesso!")
        sys.exit(0)
    else:
        print("Falha na exportação!")
        sys.exit(1)

if __name__ == "__main__":
    main()