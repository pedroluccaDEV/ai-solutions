
#!/usr/bin/env python3
"""
Script para popular a tabela apps com mais aplicativos e depois popular app_services
com serviços baseados no MCP Context7
"""

import sys
import os
import asyncio

# Adicionar o caminho do projeto ao Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from server.dao.postgres.v1.app_dao import AppDAO

async def populate_extended_apps():
    """Popula a tabela apps com mais aplicativos"""
    
    app_dao = AppDAO()
    
    # Lista de aplicativos adicionais baseados na solicitação do usuário
    extended_apps = [
        {
            "name": "Google Sheets",
            "description": "Planilhas online do Google",
            "category": "productivity",
            "service_url": "https://sheets.google.com",
            "documentation_url": "https://developers.google.com/sheets/api",
            "api_base_url": "https://sheets.googleapis.com/v4",
            "logo_url": "https://www.google.com/sheets/about/static/images/logo-sheets.png"
        },
        {
            "name": "Google Calendar",
            "description": "Serviço de calendário do Google",
            "category": "productivity",
            "service_url": "https://calendar.google.com",
            "documentation_url": "https://developers.google.com/calendar/api",
            "api_base_url": "https://www.googleapis.com/calendar/v3",
            "logo_url": "https://www.google.com/calendar/about/static/images/logo-calendar.png"
        },
        {
            "name": "Mailchimp",
            "description": "Plataforma de marketing por email",
            "category": "marketing",
            "service_url": "https://mailchimp.com",
            "documentation_url": "https://mailchimp.com/developer",
            "api_base_url": "https://us1.api.mailchimp.com/3.0",
            "logo_url": "https://cdn-images.mailchimp.com/product/brand_assets/logos/mc-freddie-dark.svg"
        },
        {
            "name": "Notion",
            "description": "Plataforma de produtividade e organização",
            "category": "productivity",
            "service_url": "https://notion.so",
            "documentation_url": "https://developers.notion.com",
            "api_base_url": "https://api.notion.com/v1",
            "logo_url": "https://www.notion.so/images/logo-ios.png"
        },
        {
            "name": "Google Chat",
            "description": "Plataforma de mensagens do Google Workspace",
            "category": "communication",
            "service_url": "https://chat.google.com",
            "documentation_url": "https://developers.google.com/chat/api",
            "api_base_url": "https://chat.googleapis.com/v1",
            "logo_url": "https://www.google.com/chat/about/static/images/logo-chat.png"
        },
        {
            "name": "Calendly",
            "description": "Agendamento de reuniões automatizado",
            "category": "productivity",
            "service_url": "https://calendly.com",
            "documentation_url": "https://developer.calendly.com",
            "api_base_url": "https://api.calendly.com",
            "logo_url": "https://calendly.com/favicon.ico"
        },
        {
            "name": "Discord",
            "description": "Plataforma de comunicação para comunidades",
            "category": "communication",
            "service_url": "https://discord.com",
            "documentation_url": "https://discord.com/developers/docs",
            "api_base_url": "https://discord.com/api/v10",
            "logo_url": "https://assets-global.website-files.com/6257adef93867e50d84d30e2/62595384e89d1d54d704ece7_3437c10597c1526c3dbd98c737c2bcae.svg"
        },
        {
            "name": "Google Docs",
            "description": "Editor de documentos online do Google",
            "category": "productivity",
            "service_url": "https://docs.google.com",
            "documentation_url": "https://developers.google.com/docs/api",
            "api_base_url": "https://docs.googleapis.com/v1",
            "logo_url": "https://www.google.com/docs/about/static/images/logo-docs.png"
        },
        {
            "name": "Google Ads",
            "description": "Plataforma de publicidade do Google",
            "category": "marketing",
            "service_url": "https://ads.google.com",
            "documentation_url": "https://developers.google.com/google-ads/api",
            "api_base_url": "https://googleads.googleapis.com/v14",
            "logo_url": "https://www.google.com/ads/static/images/logo-ads.png"
        },
        {
            "name": "YouTube",
            "description": "Plataforma de vídeos do Google",
            "category": "media",
            "service_url": "https://youtube.com",
            "documentation_url": "https://developers.google.com/youtube/v3",
            "api_base_url": "https://www.googleapis.com/youtube/v3",
            "logo_url": "https://www.youtube.com/img/desktop/yt_1200.png"
        },
        {
            "name": "Telegram",
            "description": "Aplicativo de mensagens instantâneas",
            "category": "communication",
            "service_url": "https://telegram.org",
            "documentation_url": "https://core.telegram.org/api",
            "api_base_url": "https://api.telegram.org/bot",
            "logo_url": "https://telegram.org/img/t_logo.png"
        },
        {
            "name": "GitHub",
            "description": "Plataforma de hospedagem de código",
            "category": "development",
            "service_url": "https://github.com",
            "documentation_url": "https://docs.github.com/en/rest",
            "api_base_url": "https://api.github.com",
            "logo_url": "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"
        },
        {
            "name": "Google Slides",
            "description": "Apresentações online do Google",
            "category": "productivity",
            "service_url": "https://slides.google.com",
            "documentation_url": "https://developers.google.com/slides/api",
            "api_base_url": "https://slides.googleapis.com/v1",
            "logo_url": "https://www.google.com/slides/about/static/images/logo-slides.png"
        },
        {
            "name": "RD Station",
            "description": "Plataforma de marketing digital brasileira",
            "category": "marketing",
            "service_url": "https://rdstation.com",
            "documentation_url": "https://developers.rdstation.com",
            "api_base_url": "https://api.rd.services",
            "logo_url": "https://cdn.rd.gt/assets/images/rd-station-logo.svg"
        },
        {
            "name": "Amazon S3",
            "description": "Serviço de armazenamento em nuvem da AWS",
            "category": "storage",
            "service_url": "https://aws.amazon.com/s3",
            "documentation_url": "https://docs.aws.amazon.com/AmazonS3/latest/API/Welcome.html",
            "api_base_url": "https://s3.amazonaws.com",
            "logo_url": "https://a0.awsstatic.com/libra-css/images/logos/aws_smile-header-desktop-en-white_59x35.png"
        },
        {
            "name": "Apify",
            "description": "Plataforma de web scraping e automação",
            "category": "automation",
            "service_url": "https://apify.com",
            "documentation_url": "https://docs.apify.com",
            "api_base_url": "https://api.apify.com/v2",
            "logo_url": "https://apify.com/favicon-32x32.png"
        }
    ]
    
    try:
        # Verificar aplicativos existentes
        existing_apps = await app_dao.get_all_apps()
        existing_app_names = [app['name'] for app in existing_apps]
        
        apps_to_create = [app for app in extended_apps if app['name'] not in existing_app_names]
        
        if not apps_to_create:
            print("✅ Todos os aplicativos já existem na tabela.")
            return existing_apps
        
        # Criar aplicativos que não existem
        created_apps = []
        for app_data in apps_to_create:
            app = await app_dao.create_app(
                name=app_data['name'],
                description=app_data['description'],
                category=app_data['category'],
                service_url=app_data['service_url'],
                documentation_url=app_data['documentation_url'],
                api_base_url=app_data['api_base_url'],
                logo_url=app_data['logo_url']
            )
            created_apps.append(app)
            print(f"✅ Aplicativo '{app_data['name']}' criado com ID {app['id']}")
        
        print(f"🎉 {len(created_apps)} novos aplicativos foram adicionados.")
        return existing_apps + created_apps
        
    except Exception as e:
        print(f"❌ Erro ao popular aplicativos: {e}")
        raise

async def populate_extended_app_services():
    """Popula a tabela app_services com serviços baseados nas APIs dos aplicativos"""
    
    app_dao = AppDAO()
    
    # Obter todos os aplicativos
    all_apps = await app_dao.get_all_apps()
    app_id_map = {app['name']: app['id'] for app in all_apps}
    
    # Serviços para cada aplicativo baseados nas informações do MCP Context7
    app_services_data = [
        # Gmail Services
        {
            "app_name": "Gmail",
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
                }
            ]
        },
        
        # Google Drive Services
        {
            "app_name": "Google Drive",
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
                }
            ]
        },
        
        # Google Sheets Services
        {
            "app_name": "Google Sheets",
            "services": [
                # Triggers
                {
                    "service_name": "Spreadsheet Updated",
                    "service_type": "trigger",
                    "description": "Triggered when a spreadsheet is modified",
                    "endpoint_url": "/v4/spreadsheets/{spreadsheetId}"
                },
                {
                    "service_name": "Data Source Refreshed",
                    "service_type": "trigger",
                    "description": "Triggered when a data source is refreshed",
                    "endpoint_url": "/v4/spreadsheets/{spreadsheetId}/values:batchGet"
                },
                # Actions
                {
                    "service_name": "Create Spreadsheet",
                    "service_type": "action",
                    "description": "Create a new Google Sheets spreadsheet",
                    "endpoint_url": "/v4/spreadsheets"
                },
                {
                    "service_name": "Update Cell Values",
                    "service_type": "action",
                    "description": "Update values in a spreadsheet",
                    "endpoint_url": "/v4/spreadsheets/{spreadsheetId}/values:batchUpdate"
                }
            ]
        },
        
        # Google Calendar Services
        {
            "app_name": "Google Calendar",
            "services": [
                # Triggers
                {
                    "service_name": "Event Created",
                    "service_type": "trigger",
                    "description": "Triggered when a new event is created",
                    "endpoint_url": "/calendar/v3/calendars/{calendarId}/events"
                },
                {
                    "service_name": "Event Updated",
                    "service_type": "trigger",
                    "description": "Triggered when an event is modified",
                    "endpoint_url": "/calendar/v3/calendars/{calendarId}/events/{eventId}"
                },
                # Actions
                {
                    "service_name": "Create Event",
                    "service_type": "action",
                    "description": "Create a new calendar event",
                    "endpoint_url": "/calendar/v3/calendars/{calendarId}/events"
                },
                {
                    "service_name": "Update Event",
                    "service_type": "action",
                    "description": "Update an existing calendar event",
                    "endpoint_url": "/calendar/v3/calendars/{calendarId}/events/{eventId}"
                }
            ]
        },
        
        # Slack Services
        {
            "app_name": "Slack",
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
                }
            ]
        },
        
        # Trello Services
        {
            "app_name": "Trello",
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
                }
            ]
        },
        
        # WhatsApp Services
        {
            "app_name": "WhatsApp",
            "services": [
                # Triggers
                {
                    "service_name": "Message Received",
                    "service_type": "trigger",
                    "description": "Triggered when a new message is received",
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
                }
            ]
        },
        
        # Mailchimp Services
        {
            "app_name": "Mailchimp",
            "services": [
                # Triggers
                {
                    "service_name": "New Subscriber",
                    "service_type": "trigger",
                    "description": "Triggered when a new subscriber joins a list",
                    "endpoint_url": "/3.0/lists/{list_id}/members"
                },
                # Actions
                {
                    "service_name": "Add Subscriber",
                    "service_type": "action",
                    "description": "Add a new subscriber to a list",
                    "endpoint_url": "/3.0/lists/{list_id}/members"
                },
                {
                    "service_name": "Send Campaign",
                    "service_type": "action",
                    "description": "Send an email campaign",
                    "endpoint_url": "/3.0/campaigns"
                }
            ]
        },
        
        # Notion Services
        {
            "app_name": "Notion",
            "services": [
                # Triggers
                {
                    "service_name": "Page Created",
                    "service_type": "trigger",
                    "description": "Triggered when a new page is created",
                    "endpoint_url": "/v1/pages"
                },
                {
                    "service_name": "Page Updated",
                    "service_type": "trigger",
                    "description": "Triggered when a page is modified",
                    "endpoint_url": "/v1/pages/{page_id}"
                },
                # Actions
                {
                    "service_name": "Create Page",
                    "service_type": "action",
                    "description": "Create a new Notion page",
                    "endpoint_url": "/v1/pages"
                },
                {
                    "service_name": "Update Page",
                    "service_type": "action",
                    "description": "Update an existing Notion page",
                    "endpoint_url": "/v1/pages/{page_id}"
                }
            ]
        },
        
        # Google Chat Services
        {
            "app_name": "Google Chat",
            "services": [
                # Triggers
                {
                    "service_name": "New Message",
                    "service_type": "trigger",
                    "description": "Triggered when a new message is received",
                    "endpoint_url": "/v1/spaces/{space}/messages"
                },
                # Actions
                {
                    "service_name": "Send Message",
                    "service_type": "action",
                    "description": "Send a message to Google Chat",
                    "endpoint_url": "/v1/spaces/{space}/messages"
                }
            ]
        },
        
        # Calendly Services
        {
            "app_name": "Calendly",
            "services": [
                # Triggers
                {
                    "service_name": "Event Scheduled",
                    "service_type": "trigger",
                    "description": "Triggered when an event is scheduled",
                    "endpoint_url": "/scheduled_events"
                },
                # Actions
                {
                    "service_name": "Create Event Type",
                    "service_type": "action",
                    "description": "Create a new event type",
                    "endpoint_url": "/event_types"
                }
            ]
        },
        
        # Discord Services
        {
            "app_name": "Discord",
            "services": [
                # Triggers
                {
                    "service_name": "Message Created",
                    "service_type": "trigger",
                    "description": "Triggered when a message is created",
                    "endpoint_url": "/channels/{channel_id}/messages"
                },
                # Actions
                {
                    "service_name": "Send Message",
                    "service_type": "action",
                    "description": "Send a message to Discord",
                    "endpoint_url": "/channels/{channel_id}/messages"
                }
            ]
        },
        
        # Google Docs Services
        {
            "app_name": "Google Docs",
            "services": [
                # Triggers
                {
                    "service_name": "Document Updated",
                    "service_type": "trigger",
                    "description": "Triggered when a document is modified",
                    "endpoint_url": "/v1/documents/{documentId}"
                },
                # Actions
                {
                    "service_name": "Create Document",
                    "service_type": "action",
                    "description": "Create a new Google Docs document",
                    "endpoint_url": "/v1/documents"
                }
            ]
        },
        
        # Google Ads Services
        {
            "app_name": "Google Ads",
            "services": [
                # Triggers
                {
                    "service_name": "Campaign Updated",
                    "service_type": "trigger",
                    "description": "Triggered when a campaign is modified",
                    "endpoint_url": "/v14/customers/{customerId}/campaigns"
                },
                # Actions
                {
                    "service_name": "Create Campaign",
                    "service_type": "action",
                    "description": "Create a new Google Ads campaign",
                    "endpoint_url": "/v14/customers/{customerId}/campaigns"
                }
            ]
        },
        
        # YouTube Services
        {
            "app_name": "YouTube",
            "services": [
                # Triggers
                {
                    "service_name": "Video Uploaded",
                    "service_type": "trigger",
                    "description": "Triggered when a new video is uploaded",
                    "endpoint_url": "/v3/search"
                },
                # Actions
                {
                    "service_name": "Upload Video",
                    "service_type": "action",
                    "description": "Upload a video to YouTube",
                    "endpoint_url": "/v3/videos"
                }
            ]
        },
        
        # Telegram Services
        {
            "app_name": "Telegram",
            "services": [
                # Triggers
                {
                    "service_name": "Message Received",
                    "service_type": "trigger",
                    "description": "Triggered when a message is received",
                    "endpoint_url": "/getUpdates"
                },
                # Actions
                {
                    "service_name": "Send Message",
                    "service_type": "action",
                    "description": "Send a message via Telegram",
                    "endpoint_url": "/sendMessage"
                }
            ]
        },
        
        # GitHub Services
        {
            "app_name": "GitHub",
            "services": [
                # Triggers
                {
                    "service_name": "New Issue",
                    "service_type": "trigger",
                    "description": "Triggered when a new issue is created",
                    "endpoint_url": "/repos/{owner}/{repo}/issues"
                },
                # Actions
                {
                    "service_name": "Create Issue",
                    "service_type": "action",
                    "description": "Create a new GitHub issue",
                    "endpoint_url": "/repos/{owner}/{repo}/issues"
                }
            ]
        },
        
        # Google Slides Services
        {
            "app_name": "Google Slides",
            "services": [
                # Triggers
                {
                    "service_name": "Presentation Updated",
                    "service_type": "trigger",
                    "description": "Triggered when a presentation is modified",
                    "endpoint_url": "/v1/presentations/{presentationId}"
                },
                # Actions
                {
                    "service_name": "Create Presentation",
                    "service_type": "action",
                    "description": "Create a new Google Slides presentation",
                    "endpoint_url": "/v1/presentations"
                }
            ]
        },
        
        # RD Station Services
        {
            "app_name": "RD Station",
            "services": [
                # Triggers
                {
                    "service_name": "New Lead",
                    "service_type": "trigger",
                    "description": "Triggered when a new lead is created",
                    "endpoint_url": "/platform/contacts"
                },
                # Actions
                {
                    "service_name": "Create Lead",
                    "service_type": "action",
                    "description": "Create a new lead in RD Station",
                    "endpoint_url": "/platform/contacts"
                }
            ]
        },
        
        # Amazon S3 Services
        {
            "app_name": "Amazon S3",
            "services": [
                # Triggers
                {
                    "service_name": "File Uploaded",
                    "service_type": "trigger",
                    "description": "Triggered when a file is uploaded to S3",
                    "endpoint_url": "/{bucket}/{key}"
                },
                # Actions
                {
                    "service_name": "Upload File",
                    "service_type": "action",
                    "description": "Upload a file to Amazon S3",
                    "endpoint_url": "/{bucket}/{key}"
                }
            ]
        },
        
        # Apify Services
        {
            "app_name": "Apify",
            "services": [
                # Triggers
                {
                    "service_name": "Actor Finished",
                    "service_type": "trigger",
                    "description": "Triggered when an actor finishes execution",
                    "endpoint_url": "/v2/actor-runs"
                },
                # Actions
                {
                    "service_name": "Run Actor",
                    "service_type": "action",
                    "description": "Run an Apify actor",
                    "endpoint_url": "/v2/actor-runs"
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
            app_name = app_data["app_name"]
            if app_name not in app_id_map:
                print(f"⚠️  Aplicativo '{app_name}' não encontrado. Pulando...")
                continue
                
            app_id = app_id_map[app_name]
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
                print(f"✅ Serviço '{service['service_name']}' ({service['service_type']}) adicionado para {app_name}")
        
        print(f"🎉 População concluída! {total_services} serviços foram adicionados à tabela app_services.")
        
        # Mostrar estatísticas
        stats = await app_dao.get_app_services_stats()
        print(f"\n📊 Estatísticas:")
        for stat in stats:
            print(f"   - {stat['app_name']}: {stat['trigger_count']} triggers, {stat['action_count']} actions")
            
    except Exception as e:
        print(f"❌ Erro ao popular serviços: {e}")
        raise

async def main():
    """Função principal para executar a população completa"""
    print("🚀 Iniciando população de aplicativos e serviços...")
    
    # Primeiro, popular aplicativos
    print("\n📱 Populando tabela apps...")
    apps = await populate_extended_apps()
    
    # Depois, popular serviços
    print("\n⚙️  Populando tabela app_services...")
    await populate_extended_app_services()
    
    print("\n✅ População completa concluída!")

if __name__ == "__main__":
    asyncio.run(main())
                   