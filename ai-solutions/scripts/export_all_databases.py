#!/usr/bin/env python3
"""
Script principal para exportar todos os bancos de dados do Saphien.
Permite exportar PostgreSQL, MongoDB ou ambos em uma única execução.
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

def run_export(script_name):
    """Executa um script de exportação específico"""
    script_path = Path(__file__).parent / script_name
    
    if not script_path.exists():
        print(f"❌ Script não encontrado: {script_name}")
        return False
    
    try:
        # Executar o script usando o mesmo interpretador Python
        import subprocess
        result = subprocess.run([sys.executable, str(script_path)], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"{script_name} executado com sucesso!")
            if result.stdout:
                print(f"   Saída: {result.stdout.strip()}")
            return True
        else:
            print(f"{script_name} falhou:")
            if result.stderr:
                print(f"   Erro: {result.stderr.strip()}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"{script_name} timeout (mais de 5 minutos)")
        return False
    except Exception as e:
        print(f"Erro ao executar {script_name}: {e}")
        return False

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="Exportar todos os bancos de dados Saphien")
    parser.add_argument("--postgres", action="store_true", help="Exportar apenas PostgreSQL")
    parser.add_argument("--mongodb", action="store_true", help="Exportar apenas MongoDB")
    parser.add_argument("--all", action="store_true", help="Exportar todos os bancos (padrão)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Modo verboso")
    
    args = parser.parse_args()
    
    # Definir quais bancos exportar
    export_postgres = args.postgres or args.all or (not args.postgres and not args.mongodb)
    export_mongodb = args.mongodb or args.all or (not args.postgres and not args.mongodb)
    
    print("=" * 60)
    print("EXPORTADOR COMPLETO DE BANCOS DE DADOS - SAPHIEN")
    print("=" * 60)
    print(f"Data/hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"PostgreSQL: {'SIM' if export_postgres else 'NAO'}")
    print(f"MongoDB: {'SIM' if export_mongodb else 'NAO'}")
    print("=" * 60)
    
    # Criar estrutura de diretórios
    export_base_dir = Path(__file__).parent.parent / "exports"
    postgres_dir = export_base_dir / "database" / "postgres"
    mongodb_dir = export_base_dir / "database" / "mongodb"
    
    postgres_dir.mkdir(parents=True, exist_ok=True)
    mongodb_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Estrutura de diretórios criada:")
    print(f"   - {postgres_dir}")
    print(f"   - {mongodb_dir}")
    
    success_count = 0
    total_tasks = 0
    
    # Executar exportações
    if export_postgres:
        total_tasks += 1
        print("\n" + "=" * 40)
        print("INICIANDO EXPORTAÇÃO POSTGRESQL")
        print("=" * 40)
        if run_export("export_postgres.py"):
            success_count += 1
    
    if export_mongodb:
        total_tasks += 1
        print("\n" + "=" * 40)
        print("INICIANDO EXPORTAÇÃO MONGODB")
        print("=" * 40)
        if run_export("export_mongodb.py"):
            success_count += 1
    
    # Resultado final
    print("\n" + "=" * 60)
    print("RESULTADO DA EXPORTAÇÃO")
    print("=" * 60)
    print(f"Tarefas concluídas: {success_count}/{total_tasks}")
    
    if success_count == total_tasks:
        print("Todas as exportações foram bem-sucedidas!")
        print(f"Arquivos salvos em: {export_base_dir / 'database'}")
        sys.exit(0)
    else:
        print("Algumas exportações falharam!")
        sys.exit(1)

if __name__ == "__main__":
    main()