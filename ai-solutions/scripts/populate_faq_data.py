#!/usr/bin/env python3
"""
Script para popular as tabelas de FAQ do banco de dados.
Este script cria categorias e FAQs padrão para a página de ajuda.
"""

import asyncio
import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao path para importações
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config.init_db import get_postgres_db, async_engine
from core.config.init_faq_data import initialize_faq_data, DEFAULT_FAQ_CATEGORIES, DEFAULT_FAQS
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession

async def populate_faq_tables():
    """Popula as tabelas de FAQ com dados padrão"""
    print("🚀 Iniciando população das tabelas FAQ...")
    
    try:
        # Primeiro cria as tabelas se não existirem
        async with async_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        print("✅ Tabelas criadas/verificadas com sucesso")
        
        # Agora popula os dados
        async for db in get_postgres_db():
            await initialize_faq_data(db)
            print("✅ Dados de FAQ populados com sucesso")
            
    except Exception as e:
        print(f"❌ Erro ao popular tabelas FAQ: {e}")
        raise

async def check_existing_data():
    """Verifica se já existem dados nas tabelas FAQ"""
    try:
        async for db in get_postgres_db():
            from sqlalchemy import select, func
            from models.postgres.faq_model import FAQCategory, FAQ
            
            # Verifica categorias
            categories_count = await db.execute(select(func.count()).select_from(FAQCategory))
            categories_count = categories_count.scalar()
            
            # Verifica FAQs
            faqs_count = await db.execute(select(func.count()).select_from(FAQ))
            faqs_count = faqs_count.scalar()
            
            print(f"📊 Dados existentes: {categories_count} categorias, {faqs_count} FAQs")
            
            return categories_count > 0 or faqs_count > 0
            
    except Exception as e:
        print(f"❌ Erro ao verificar dados existentes: {e}")
        return False

async def main():
    """Função principal"""
    print("=" * 50)
    print("📋 POPULADOR DE TABELAS FAQ")
    print("=" * 50)
    
    # Verifica se já existem dados
    has_data = await check_existing_data()
    
    if has_data:
        print("⚠️  Já existem dados nas tabelas FAQ")
        response = input("Deseja continuar e adicionar dados padrão? (s/N): ")
        if response.lower() != 's':
            print("Operação cancelada pelo usuário")
            return
    
    # Popula os dados
    await populate_faq_tables()
    
    print("=" * 50)
    print("✅ População concluída com sucesso!")
    print("📊 Dados criados:")
    print(f"   - Categorias: {len(DEFAULT_FAQ_CATEGORIES)}")
    print(f"   - FAQs: {len(DEFAULT_FAQS)}")
    print("=" * 50)

if __name__ == "__main__":
    # Executa o script assíncrono
    asyncio.run(main())