#!/usr/bin/env python3
"""
Script para popular o banco de dados com aplicativos populares e seus serviços
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from dao.mongo.v1.app_dao import AppDAO

def populate_apps():
    """Popular aplicativos com serviços baseados em APIs populares"""
    
    apps_data = [
        {
            "name": "Gmail",
            "description": "Serviço de email do Google",
            "category": "communication",
            "icon_url": "https://www.gstatic.com/images/branding/product/1x/gmail_2020q4_48dp.png",
            "api_documentation_url": "https://developers.google.com/gmail/api",
            "authentication_type": "OAuth2",
            "services": [
                {
                    "name": "new_email_received",
                    "description": "Disparado quando um novo email é recebido",
                    "service_type": "trigger",
                    "parameters": [
                        {"name": "label", "type": "string", "required": False, "description": "Label específica para monitorar"},
                        {"name": "sender", "type": "string", "required": False, "description": "Email do remetente específico"}
                    ]
                },
                {
                    "name": "send_email",
                    "description": "Enviar um novo email",
                    "service_type": "action",
                    "parameters": [
                        {"name": "to", "type": "string", "required": True, "description": "Email do destinatário"},
                        {"name": "subject", "type": "string", "required": True, "description": "Assunto do email"},
                        {"name": "body", "type": "string", "required": True, "description": "Corpo do email"}
                    ]
                }
            ]
        },
        {
            "name": "Google Drive",
            "description": "Serviço de armazenamento em nuvem do Google",
            "category": "storage",
            "icon_url": "https://www.gstatic.com/images/branding/product/1x/drive_2020q4_48dp.png",
            "api_documentation_url": "https://developers.google.com/drive/api",
            "authentication_type": "OAuth2",
            "services": [
                {
                    "name": "new_file_created",
                    "description": "Disparado quando um novo arquivo é criado",
                    "service_type": "trigger",
                    "parameters": [
                        {"name": "folder_id", "type": "string", "required": False, "description": "ID da pasta específica"}
                    ]
                },
                {
                    "name": "create_file",
                    "description": "Criar um novo arquivo",
                    "service_type": "action",
                    "parameters": [
                        {"name": "name", "type": "string", "required": True, "description": "Nome do arquivo"},
                        {"name": "content", "type": "string", "required": True, "description": "Conteúdo do arquivo"},
                        {"name": "folder_id", "type": "string", "required": False, "description": "ID da pasta de destino"}
                    ]
                }
            ]
        },
        {
            "name": "Slack",
            "description": "Plataforma de comunicação em equipe",
            "category": "communication",
            "icon_url": "https://a.slack-edge.com/80588/marketing/img/meta/slack_hash_256.png",
            "api_documentation_url": "https://api.slack.com/",
            "authentication_type": "OAuth2",
            "services": [
                {
                    "name": "new_message_received",
                    "description": "Disparado quando uma nova mensagem é recebida",
                    "service_type": "trigger",
                    "parameters": [
                        {"name": "channel", "type": "string", "required": False, "description": "Canal específico"}
                    ]
                },
                {
                    "name": "send_message",
                    "description": "Enviar uma mensagem",
                    "service_type": "action",
                    "parameters": [
                        {"name": "channel", "type": "string", "required": True, "description": "Canal de destino"},
                        {"name": "message", "type": "string", "required": True, "description": "Texto da mensagem"}
                    ]
                }
            ]
        },
        {
            "name": "Trello",
            "description": "Ferramenta de gerenciamento de projetos",
            "category": "project_management",
            "icon_url": "https://a.trellocdn.com/prgb/dist/images/ios/apple-touch-icon-152x152-precomposed.0307bc39eb6d6a6a9a0e.png",
            "api_documentation_url": "https://developer.atlassian.com/cloud/trello/",
            "authentication_type": "OAuth2",
            "services": [
                {
                    "name": "new_card_created",
                    "description": "Disparado quando um novo card é criado",
                    "service_type": "trigger",
                    "parameters": [
                        {"name": "board_id", "type": "string", "required": False, "description": "ID do quadro específico"}
                    ]
                },
                {
                    "name": "create_card",
                    "description": "Criar um novo card",
                    "service_type": "action",
                    "parameters": [
                        {"name": "board_id", "type": "string", "required": True, "description": "ID do quadro"},
                        {"name": "list_id", "type": "string", "required": True, "description": "ID da lista"},
                        {"name": "title", "type": "string", "required": True, "description": "Título do card"},
                        {"name": "description", "type": "string", "required": False, "description": "Descrição do card"}
                    ]
                }
            ]
        },
        {
            "name": "WhatsApp Business",
            "description": "API do WhatsApp para negócios",
            "category": "communication",
            "icon_url": "https://static.whatsapp.net/rsrc.php/v3/yP/r/rYZqPCfGJ0g.png",
            "api_documentation_url": "https://developers.facebook.com/docs/whatsapp/",
            "authentication_type": "API Key",
            "services": [
                {
                    "name": "new_message_received",
                    "description": "Disparado quando uma nova mensagem é recebida",
                    "service_type": "trigger",
                    "parameters": [
                        {"name": "phone_number", "type": "string", "required": False, "description": "Número de telefone específico"}
                    ]
                },
                {
                    "name": "send_message",
                    "description": "Enviar uma mensagem",
                    "service_type": "action",
                    "parameters": [
                        {"name": "phone_number", "type": "string", "required": True, "description": "Número de telefone do destinatário"},
                        {"name": "message", "type": "string", "required": True, "description": "Texto da mensagem"}
                    ]
                }
            ]
        },
        {
            "name": "Google Forms",
            "description": "Criação e gerenciamento de formulários",
            "category": "productivity",
            "icon_url": "https://www.gstatic.com/images/branding/product/1x/forms_2020q4_48dp.png",
            "api_documentation_url": "https://developers.google.com/forms/api",
            "authentication_type": "OAuth2",
            "services": [
                {
                    "name": "new_form_response",
                    "description": "Disparado quando um novo formulário é respondido",
                    "service_type": "trigger",
                    "parameters": [
                        {"name": "form_id", "type": "string", "required": True, "description": "ID do formulário"}
                    ]
                },
                {
                    "name": "create_form",
                    "description": "Criar um novo formulário",
                    "service_type": "action",
                    "parameters": [
                        {"name": "title", "type": "string", "required": True, "description": "Título do formulário"},
                        {"name": "questions", "type": "array", "required": True, "description": "Lista de perguntas"}
                    ]
                }
            ]
        },
        {
            "name": "Notion",
            "description": "Plataforma de produtividade e organização",
            "category": "productivity",
            "icon_url": "https://www.notion.so/images/favicon.ico",
            "api_documentation_url": "https://developers.notion.com/",
            "authentication_type": "OAuth2",
            "services": [
                {
                    "name": "new_page_created",
                    "description": "Disparado quando uma nova página é criada",
                    "service_type": "trigger",
                    "parameters": [
                        {"name": "database_id", "type": "string", "required": False, "description": "ID do banco de dados específico"}
                    ]
                },
                {
                    "name": "create_page",
                    "description": "Criar uma nova página",
                    "service_type": "action",
                    "parameters": [
                        {"name": "database_id", "type": "string", "required": True, "description": "ID do banco de dados"},
                        {"name": "title", "type": "string", "required": True, "description": "Título da página"},
                        {"name": "content", "type": "string", "required": False, "description": "Conteúdo da página"}
                    ]
                }
            ]
        },
        {
            "name": "GitHub",
            "description": "Plataforma de desenvolvimento e versionamento",
            "category": "development",
            "icon_url": "https://github.githubassets.com/favicons/favicon.png",
            "api_documentation_url": "https://docs.github.com/en/rest",
            "authentication_type": "OAuth2",
            "services": [
                {
                    "name": "new_issue_created",
                    "description": "Disparado quando uma nova issue é criada",
                    "service_type": "trigger",
                    "parameters": [
                        {"name": "repository", "type": "string", "required": False, "description": "Repositório específico"}
                    ]
                },
                {
                    "name": "create_issue",
                    "description": "Criar uma nova issue",
                    "service_type": "action",
                    "parameters": [
                        {"name": "repository", "type": "string", "required": True, "description": "Repositório de destino"},
                        {"name": "title", "type": "string", "required": True, "description": "Título da issue"},
                        {"name": "body", "type": "string", "required": False, "description": "Descrição da issue"}
                    ]
                }
            ]
        }
    ]
    
    created_count = 0
    for app_data in apps_data:
        try:
            # Verificar se o aplicativo já existe
            existing_app = AppDAO.get_app_by_name(app_data["name"])
            if existing_app:
                print(f"Aplicativo '{app_data['name']}' já existe. Atualizando...")
                AppDAO.update_app(existing_app["id"], app_data)
            else:
                app_id = AppDAO.create_app(app_data)
                print(f"Aplicativo '{app_data['name']}' criado com ID: {app_id}")
                created_count += 1
        except Exception as e:
            print(f"Erro ao criar aplicativo '{app_data['name']}': {e}")
    
    print(f"\nProcesso concluído! {created_count} aplicativos criados/atualizados.")

if __name__ == "__main__":
    populate_apps()