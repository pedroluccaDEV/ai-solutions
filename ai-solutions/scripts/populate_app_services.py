#!/usr/bin/env python3
"""
Script para popular a tabela app_services com serviços de APIs baseados no MCP Context7
"""

import sys
import os
import asyncio

# Adicionar o caminho do projeto ao Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.dao.postgres.v1.app_dao import AppDAO

async def populate_app_services():
    """Popula a tabela app_services com serviços baseados nas APIs dos aplicativos"""
    
    app_dao = AppDAO()
    
    # Serviços para cada aplicativo baseados nas informações do MCP Context7
    app_services_data = [
        # Gmail Services (Triggers e Actions)
        {
            "app_id": 1,  # Gmail
            "services": [
                # Triggers
                {
                    "service_name": "New Email Received",
                    "service_type": "trigger",
                    "description": "Triggered when a new email arrives in the inbox",
                    "endpoint_url": "/gmail/v1/users/{userId}/messages"
                },
                {
                    "service_name": "Email Label Changed",
                    "service_type": "trigger", 
                    "description": "Triggered when an email's labels are modified",
                    "endpoint_url": "/gmail/v1/users/{userId}/messages/{messageId}/modify"
                },
                {
                    "service_name": "Push Notification Watch",
                    "service_type": "trigger",
                    "description": "Real-time notifications for mailbox updates",
                    "endpoint_url": "/gmail/v1/users/{userId}/watch"
                },
                # Actions
                {
                    "service_name": "Send Email",
                    "service_type": "action",
                    "description": "Send a new email message",
                    "endpoint_url": "/gmail/v1/users/{userId}/messages/send"
                },
                {
                    "service_name": "Create Draft",
                    "service_type": "action",
                    "description": "Create a new email draft",
                    "endpoint_url": "/gmail/v1/users/{userId}/drafts"
                },
                {
                    "service_name": "Modify Labels",
                    "service_type": "action",
                    "description": "Add or remove labels from messages",
                    "endpoint_url": "/gmail/v1/users/{userId}/messages/{messageId}/modify"
                }
            ]
        },
        
        # Google Drive Services
        {
            "app_id": 2,  # Google Drive
            "services": [
                # Triggers
                {
                    "service_name": "File Created",
                    "service_type": "trigger",
                    "description": "Triggered when a new file is created in Drive",
                    "endpoint_url": "/drive/v3/files"
                },
                {
                    "service_name": "File Modified",
                    "service_type": "trigger",
                    "description": "Triggered when an existing file is modified",
                    "endpoint_url": "/drive/v3/files/{fileId}"
                },
                {
                    "service_name": "File Shared",
                    "service_type": "trigger",
                    "description": "Triggered when file sharing permissions change",
                    "endpoint_url": "/drive/v3/files/{fileId}/permissions"
                },
                # Actions
                {
                    "service_name": "Upload File",
                    "service_type": "action",
                    "description": "Upload a new file to Google Drive",
                    "endpoint_url": "/upload/drive/v3/files"
                },
                {
                    "service_name": "Download File",
                    "service_type": "action",
                    "description": "Download a file from Google Drive",
                    "endpoint_url": "/drive/v3/files/{fileId}"
                },
                {
                    "service_name": "Share File",
                    "service_type": "action",
                    "description": "Share a file with specific permissions",
                    "endpoint_url": "/drive/v3/files/{fileId}/permissions"
                }
            ]
        },
        
        # Slack Services
        {
            "app_id": 3,  # Slack
            "services": [
                # Triggers
                {
                    "service_name": "New Message in Channel",
                    "service_type": "trigger",
                    "description": "Triggered when a new message is posted in a channel",
                    "endpoint_url": "/conversations.history"
                },
                {
                    "service_name": "Direct Message Received",
                    "service_type": "trigger",
                    "description": "Triggered when a direct message is received",
                    "endpoint_url": "/conversations.history"
                },
                {
                    "service_name": "Reaction Added",
                    "service_type": "trigger",
                    "description": "Triggered when a reaction is added to a message",
                    "endpoint_url": "/reactions.get"
                },
                # Actions
                {
                    "service_name": "Send Message to Channel",
                    "service_type": "action",
                    "description": "Send a message to a Slack channel",
                    "endpoint_url": "/chat.postMessage"
                },
                {
                    "service_name": "Send Direct Message",
                    "service_type": "action",
                    "description": "Send a direct message to a user",
                    "endpoint_url": "/chat.postMessage"
                },
                {
                    "service_name": "Create Channel",
                    "service_type": "action",
                    "description": "Create a new Slack channel",
                    "endpoint_url": "/conversations.create"
                }
            ]
        },
        
        # Trello Services
        {
            "app_id": 4,  # Trello
            "services": [
                # Triggers
                {
                    "service_name": "New Card Created",
                    "service_type": "trigger",
                    "description": "Triggered when a new card is created on a board",
                    "endpoint_url": "/1/cards"
                },
                {
                    "service_name": "Card Moved",
                    "service_type": "trigger",
                    "description": "Triggered when a card is moved between lists",
                    "endpoint_url": "/1/cards/{id}/actions"
                },
                {
                    "service_name": "Card Updated",
                    "service_type": "trigger",
                    "description": "Triggered when a card's details are updated",
                    "endpoint_url": "/1/cards/{id}"
                },
                # Actions
                {
                    "service_name": "Create Card",
                    "service_type": "action",
                    "description": "Create a new card on a Trello board",
                    "endpoint_url": "/1/cards"
                },
                {
                    "service_name": "Update Card",
                    "service_type": "action",
                    "description": "Update an existing card's details",
                    "endpoint_url": "/1/cards/{id}"
                },
                {
                    "service_name": "Add Comment to Card",
                    "service_type": "action",
                    "description": "Add a comment to a Trello card",
                    "endpoint_url": "/1/cards/{id}/actions/comments"
                }
            ]
        },
        
        # WhatsApp Services
        {
            "app_id": 5,  # WhatsApp
            "services": [
                # Triggers
                {
                    "service_name": "Message Received",
                    "service_type": "trigger",
                    "description": "Triggered when a new message is received",
                    "endpoint_url": "/v17.0/{phone-number-id}/messages"
                },
                {
                    "service_name": "Message Status Update",
                    "service_type": "trigger",
                    "description": "Triggered when message status changes (sent, delivered, read)",
                    "endpoint_url": "/v17.0/{phone-number-id}/messages"
                },
                # Actions
                {
                    "service_name": "Send Text Message",
                    "service_type": "action",
                    "description": "Send a text message via WhatsApp",
                    "endpoint_url": "/v17.0/{phone-number-id}/messages"
                },
                {
                    "service_name": "Send Media Message",
                    "service_type": "action",
                    "description": "Send a media message (image, video, document)",
                    "endpoint_url": "/v17.0/{phone-number-id}/messages"
                },
                {
                    "service_name": "Send Template Message",
                    "service_type": "action",
                    "description": "Send a pre-approved template message",
                    "endpoint_url": "/v17.0/{phone-number-id}/messages"
                }
            ]
        },
        
        # Google Forms Services
        {
            "app_id": 6,  # Google Forms
            "services": [
                # Triggers
                {
                    "service_name": "New Form Response",
                    "service_type": "trigger",
                    "description": "Triggered when a new response is submitted to a form",
                    "endpoint_url": "/forms/v1/forms/{formId}/responses"
                },
                {
                    "service_name": "Form Updated",
                    "service_type": "trigger",
                    "description": "Triggered when a form is modified",
                    "endpoint_url": "/forms/v1/forms/{formId}"
                },
                # Actions
                {
                    "service_name": "Create Form",
                    "service_type": "action",
                    "description": "Create a new Google Form",
                    "endpoint_url": "/forms/v1/forms"
                },
                {
                    "service_name": "Get Form Responses",
                    "service_type": "action",
                    "description": "Retrieve responses from a Google Form",
                    "endpoint_url": "/forms/v1/forms/{formId}/responses"
                },
                {
                    "service_name": "Update Form",
                    "service_type": "action",
                    "description": "Update an existing Google Form",
                    "endpoint_url": "/forms/v1/forms/{formId}"
                }
            ]
        }
    ]
    
    try:
        # Verificar se já existem serviços
        existing_services = await app_dao.get_all_app_services()
        if existing_services:
            print(f"⚠️  Já existem {len(existing_services)} serviços na tabela app_services.")
            response = input("Deseja limpar a tabela e recriar os serviços? (s/N): ")
            if response.lower() == 's':
                await app_dao.clear_app_services()
                print("✅ Tabela app_services limpa.")
            else:
                print("❌ Operação cancelada.")
                return
        
        # Inserir os serviços
        total_services = 0
        for app_data in app_services_data:
            app_id = app_data["app_id"]
            services = app_data["services"]
            
            for service in services:
                await app_dao.create_app_service(
                    app_id=app_id,
                    service_name=service["service_name"],
                    service_type=service["service_type"],
                    description=service["description"],
                    endpoint_url=service["endpoint_url"]
                )
                total_services += 1
                print(f"✅ Serviço '{service['service_name']}' ({service['service_type']}) adicionado para app_id {app_id}")
        
        print(f"\n🎉 População concluída! {total_services} serviços foram adicionados à tabela app_services.")
        
        # Mostrar estatísticas
        stats = await app_dao.get_app_services_stats()
        print(f"\n📊 Estatísticas:")
        for stat in stats:
            print(f"   - {stat['app_name']}: {stat['trigger_count']} triggers, {stat['action_count']} actions")
            
    except Exception as e:
        print(f"❌ Erro ao popular serviços: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(populate_app_services())