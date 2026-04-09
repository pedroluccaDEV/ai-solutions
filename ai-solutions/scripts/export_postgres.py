#!/usr/bin/env python3
"""
Script para exportar a estrutura e todos os dados do banco PostgreSQL Saphien.
Exporta para formato SQL com comandos CREATE TABLE e INSERT.
"""

import os
import sys
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

def export_postgres_database():
    """Exporta o banco de dados PostgreSQL para arquivo SQL"""
    
    # Configurações do banco a partir do .env
    db_url = "postgresql://postgres:root@localhost:5433/saphien"
    
    # Caminhos de exportação
    export_base_dir = Path(__file__).parent.parent / "exports"
    postgres_dir = export_base_dir / "database" / "postgres"
    
    # Criar diretórios se não existirem
    postgres_dir.mkdir(parents=True, exist_ok=True)
    
    # Nome do arquivo com timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = postgres_dir / f"saphien_postgres_backup_{timestamp}.sql"
    
    print(f"Iniciando exportação do banco PostgreSQL...")
    print(f"Diretório de destino: {postgres_dir}")
    print(f"Arquivo de saída: {output_file.name}")
    
    try:
        # Comando pg_dump para exportar estrutura e dados
        cmd = [
            "pg_dump",
            "--dbname", db_url,
            "--file", str(output_file),
            "--verbose",
            "--no-owner",
            "--no-acl",
            "--clean",
            "--if-exists",
            "--create"
        ]
        
        print(f"Executando comando: {' '.join(cmd[:4])} [REDACTED]")
        
        # Executar o comando
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"Exportação concluída com sucesso!")
            print(f"Tamanho do arquivo: {output_file.stat().st_size / 1024 / 1024:.2f} MB")
            
            # Verificar conteúdo do arquivo
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read(1000)  # Ler primeiros 1000 caracteres
            
            if "CREATE TABLE" in content and "INSERT INTO" in content:
                print("Arquivo contém estrutura e dados válidos")
            else:
                print("Arquivo pode não conter dados esperados")
                
            return True, str(output_file)
            
        else:
            print(f"Erro na exportação:")
            print(f"STDERR: {result.stderr}")
            print(f"STDOUT: {result.stdout}")
            return False, result.stderr
            
    except subprocess.TimeoutExpired:
        print("Timeout: A exportação demorou muito (mais de 5 minutos)")
        return False, "Timeout na exportação"
    except FileNotFoundError:
        print("pg_dump não encontrado. Certifique-se que PostgreSQL está instalado")
        return False, "pg_dump não encontrado"
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return False, str(e)

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="Exportar banco PostgreSQL Saphien")
    parser.add_argument("--verbose", "-v", action="store_true", help="Modo verboso")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("EXPORTADOR DE BANCO POSTGRESQL - SAPHIEN")
    print("=" * 60)
    
    success, message = export_postgres_database()
    
    if success:
        print(f"Exportação concluída: {message}")
        sys.exit(0)
    else:
        print(f"Falha na exportação: {message}")
        sys.exit(1)

if __name__ == "__main__":
    main()