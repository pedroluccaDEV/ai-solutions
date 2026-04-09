#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para criar 3 processos de exemplo para demonstração
"""
import sys
import os

# Adicionar o caminho do projeto ao PYTHONPATH
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from datetime import datetime, timezone
from dao.mongo.v1.process_dao import ProcessDAO
from dao.mongo.v1.app_dao import AppDAO

def create_sample_processes():
    """Criar 3 processos de exemplo para demonstração"""
    
    # Buscar aplicativos existentes
    gmail_app = AppDAO.get_app_by_name("Gmail")
    slack_app = AppDAO.get_app_by_name("Slack")
    trello_app = AppDAO.get_app_by_name("Trello")
    notion_app = AppDAO.get_app_by_name("Notion")
    github_app = AppDAO.get_app_by_name("GitHub")
    
    if not all([gmail_app, slack_app, trello_app, notion_app, github_app]):
        print("Erro: Nem todos os aplicativos necessários foram encontrados")
        return
    
    sample_processes = [
        {
            "name": "Gmail to Slack - Notificação de Emails Importantes",
            "description": "Envia notificações no Slack quando emails importantes chegam no Gmail",
            "triggers": [{
                "type": "app_trigger",
                "name": "new_email_received",
                "description": "Disparado quando um novo email é recebido",
                "configuration": {
                    "app_id": gmail_app["id"],
                    "service_name": "new_email_received",
                    "filters": {
                        "sender": "importante@empresa.com"
                    }
                },
                "enabled": True
            }],
            "steps": [{
                "type": "app_action",
                "name": "send_message",
                "description": "Enviar uma mensagem no Slack",
                "parameters": {
                    "app_id": slack_app["id"],
                    "service_name": "send_message",
                    "channel": "#notificacoes",
                    "message": "Novo email importante recebido de {sender}: {subject}"
                }
            }],
            "status": "active",
            "environment_variables": {},
            "created_by": "sample_user_1",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "last_run": datetime.now(timezone.utc),
            "run_count": 15,
            "success_count": 14,
            "error_count": 1
        },
        {
            "name": "GitHub to Trello - Criação de Cards para Issues",
            "description": "Cria automaticamente cards no Trello quando novas issues são abertas no GitHub",
            "triggers": [{
                "type": "app_trigger",
                "name": "new_issue_created",
                "description": "Disparado quando uma nova issue é criada",
                "configuration": {
                    "app_id": github_app["id"],
                    "service_name": "new_issue_created",
                    "repository": "empresa/projeto-principal"
                },
                "enabled": True
            }],
            "steps": [{
                "type": "app_action",
                "name": "create_card",
                "description": "Criar um novo card no Trello",
                "parameters": {
                    "app_id": trello_app["id"],
                    "service_name": "create_card",
                    "board_id": "board_123",
                    "list_id": "lista_backlog",
                    "title": "Issue: {issue_title}",
                    "description": "GitHub Issue #{issue_number}\n\n{issue_body}\n\nLink: {issue_url}"
                }
            }],
            "status": "active",
            "environment_variables": {},
            "created_by": "sample_user_2",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "last_run": datetime.now(timezone.utc),
            "run_count": 8,
            "success_count": 8,
            "error_count": 0
        },
        {
            "name": "Trello to Notion - Sincronização de Tarefas",
            "description": "Sincroniza cards do Trello com páginas no Notion para documentação",
            "triggers": [{
                "type": "app_trigger",
                "name": "new_card_created",
                "description": "Disparado quando um novo card é criado",
                "configuration": {
                    "app_id": trello_app["id"],
                    "service_name": "new_card_created",
                    "board_id": "board_123"
                },
                "enabled": True
            }],
            "steps": [{
                "type": "app_action",
                "name": "create_page",
                "description": "Criar uma nova página no Notion",
                "parameters": {
                    "app_id": notion_app["id"],
                    "service_name": "create_page",
                    "database_id": "database_456",
                    "title": "Tarefa: {card_name}",
                    "content": "**Descrição:** {card_description}\n\n**Status:** {card_status}\n\n**Data de Criação:** {created_date}"
                }
            }],
            "status": "draft",
            "environment_variables": {},
            "created_by": "sample_user_3",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "last_run": None,
            "run_count": 0,
            "success_count": 0,
            "error_count": 0
        }
    ]
    
    created_count = 0
    for process_data in sample_processes:
        try:
            # Verificar se o processo já existe
            existing_processes = ProcessDAO.search_processes_by_name(
                process_data["created_by"], 
                process_data["name"], 
                0, 
                1
            )
            
            if existing_processes:
                print(f"Processo '{process_data['name']}' já existe. Atualizando...")
                process_id = existing_processes[0]["_id"]
                ProcessDAO.update_process(process_id, process_data)
            else:
                process_id = ProcessDAO.create_process(process_data, process_data["created_by"])
                print(f"Processo criado com ID: {process_id}")
                created_count += 1
        except Exception as e:
            print(f"Erro ao criar processo: {e}")
    
    print(f"\nProcesso concluído! {created_count} processos de exemplo criados/atualizados.")

if __name__ == "__main__":
    create_sample_processes()