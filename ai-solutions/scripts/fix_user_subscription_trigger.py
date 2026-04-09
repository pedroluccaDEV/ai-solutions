#!/usr/bin/env python3
"""
Script para corrigir a trigger de criação de usuários com subscription.
A trigger original estava tentando acessar NEW.plan_id que não existe na tabela users.
Este script modifica a trigger para usar o plano gratuito padrão (ID: 7).
"""

import asyncio
import asyncpg
import sys
import os
from urllib.parse import urlparse

# Adicionar o caminho do servidor ao sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.config.settings import settings

async def fix_user_subscription_trigger():
    """Corrige a função da trigger para usar plano gratuito padrão"""
    
    # SQL para modificar a função da trigger
    sql = """
    CREATE OR REPLACE FUNCTION public.create_user_with_subscription()
    RETURNS trigger
    LANGUAGE plpgsql
    AS $function$
    DECLARE
        new_subscription_id BIGINT;
        plan_monthly_credits INTEGER;
        default_plan_id INTEGER := 1; -- Plano gratuito padrão
    BEGIN
        -- Usar plano gratuito padrão (ID: 7)
        SELECT monthly_credits INTO plan_monthly_credits
        FROM subscription_plans 
        WHERE id = default_plan_id;
        
        IF NOT FOUND THEN
            RAISE EXCEPTION 'Plano gratuito padrão com ID % não existe', default_plan_id;
        END IF;
        
        -- Inserir na tabela user_subscriptions
        INSERT INTO user_subscriptions (user_id, plan_id, subscription_type, status, starts_at, expires_at, auto_renew)
        VALUES (
            NEW.id,
            default_plan_id,
            'monthly',
            'active',
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP + INTERVAL '30 days',
            true
        )
        RETURNING id INTO new_subscription_id;
        
        -- Inserir na tabela user_credits
        INSERT INTO user_credits (user_id, subscription_credits, recharge_credits, last_monthly_reset)
        VALUES (
            NEW.id,
            plan_monthly_credits,
            0,
            CURRENT_TIMESTAMP
        );
        
        -- Atualizar o subscription_id do usuário
        NEW.subscription_id := new_subscription_id;
        
        RETURN NEW;
    END;
    $function$;
    """
    
    try:
        # Parse da URL do PostgreSQL
        parsed_url = urlparse(settings.POSTGRES_URL)
        
        # Extrair informações de conexão da URL
        host = parsed_url.hostname
        port = parsed_url.port or 5433
        user = parsed_url.username
        password = parsed_url.password
        database = parsed_url.path.lstrip('/')
        
        # Conectar ao PostgreSQL
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        
        # Executar o SQL para modificar a função
        await conn.execute(sql)
        print("Função da trigger atualizada com sucesso!")
        print("Agora todos os novos usuários receberão o plano gratuito padrão (ID: 1)")
        
        # Verificar se a função foi criada corretamente
        result = await conn.fetchrow(
            "SELECT prosrc FROM pg_proc WHERE proname = 'create_user_with_subscription'"
        )
        if result:
            print("Função verificada com sucesso no banco de dados")
        
        await conn.close()
        
    except Exception as e:
        print(f"Erro ao atualizar a trigger: {e}")
        raise

async def test_trigger_fix():
    """Testa se a correção da trigger funciona"""
    try:
        # Parse da URL do PostgreSQL
        parsed_url = urlparse(settings.POSTGRES_URL)
        
        # Extrair informações de conexão da URL
        host = parsed_url.hostname
        port = parsed_url.port or 5433
        user = parsed_url.username
        password = parsed_url.password
        database = parsed_url.path.lstrip('/')
        
        # Conectar ao PostgreSQL
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        
        # Verificar se a função existe
        result = await conn.fetchrow(
            "SELECT proname, prosrc FROM pg_proc WHERE proname = 'create_user_with_subscription'"
        )
        
        if result:
            print("Função encontrada:")
            print(f"   Nome: {result['proname']}")
            # Mostrar parte do código fonte para verificação
            src_preview = result['prosrc'][:200] + "..." if len(result['prosrc']) > 200 else result['prosrc']
            print(f"   Código fonte (preview): {src_preview}")
        else:
            print("Função não encontrada")
        
        await conn.close()
        
    except Exception as e:
        print(f"Erro ao testar a trigger: {e}")

if __name__ == "__main__":
    print("Iniciando correção da trigger de criação de usuários...")
    print("=" * 60)
    
    # Executar a correção
    asyncio.run(fix_user_subscription_trigger())
    
    print("=" * 60)
    print("Testando a correção...")
    asyncio.run(test_trigger_fix())
    
    print("=" * 60)
    print("Instruções de uso:")
    print("1. Execute este script com: python -m server.scripts.fix_user_subscription_trigger")
    print("2. Reinicie o servidor backend para aplicar as mudanças")
    print("3. Teste criando um novo usuário")