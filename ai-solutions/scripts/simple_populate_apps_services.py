
#!/usr/bin/env python3
"""
Script simples para popular as tabelas apps e app_services usando psycopg2 diretamente
"""

import psycopg2
import sys
import os
from datetime import datetime

def get_db_connection():
    """Retorna uma conexão com o banco PostgreSQL"""
    return psycopg2.connect(
        host="localhost",
        port="5433",
        database="saphien",
        user="postgres",
        password="root"
    )

def populate_apps():
    """Popula a tabela apps com aplicativos"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Lista de aplicativos
    apps = [
        # Aplicativos existentes
        ("Gmail", "Serviço de email do Google", "email", "https://mail.google.com", 
         "https://developers.google.com/gmail/api", "https://gmail.googleapis.com", 
         "https://www.google.com/gmail/about/static/images/logo-gmail.png"),
        
        ("Google Drive", "Serviço de armazenamento em nuvem do Google", "storage", 
         "https://drive.google.com", "https://developers.google.com/drive/api", 
         "https://www.googleapis.com/drive/v3", 
         "https://www.google.com/drive/static/images/drive/logo-drive.png"),
        
        ("Slack", "Plataforma de comunicação em equipe", "communication", 
         "https://slack.com", "https://api.slack.com", "https://slack.com/api", 
         "https://a.slack-edge.com/80588/marketing/img/meta/slack_hash_256.png"),
        
        ("Trello", "Ferramenta de gerenciamento de projetos", "productivity", 
         "https://trello.com", "https://developer.atlassian.com/cloud/trello", 
         "https://api.trello.com/1", 
         "https://d2k1ftgv7pobq7.cloudfront.net/meta/u/res/images/trello-header-logos/167dc5b8fb13d7c3c6ab6d3d44a6c3d4/trello-logo-blue.png"),
        
        ("WhatsApp", "Aplicativo de mensagens", "communication", 
         "https://whatsapp.com", "https://developers.facebook.com/docs/whatsapp", 
         "https://graph.facebook.com/v17.0", 
         "https://static.whatsapp.net/rsrc.php/v3/y7/r/DSxOAUB0raA.png"),
        
        ("Google Forms", "Formulários online do Google", "productivity", 
         "https://forms.google.com", "https://developers.google.com/forms/api", 
         "https://forms.googleapis.com/v1", 
         "https://www.google.com/forms/about/static/images/logo-forms.png"),
        
        # Novos aplicativos
        ("Google Sheets", "Planilhas online do Google", "productivity", 
         "https://sheets.google.com", "https://developers.google.com/sheets/api", 
         "https://sheets.googleapis.com/v4", 
         "https://www.google.com/sheets/about/static/images/logo-sheets.png"),
        
        ("Google Calendar", "Serviço de calendário do Google", "productivity", 
         "https://calendar.google.com", "https://developers.google.com/calendar/api", 
         "https://www.googleapis.com/calendar/v3", 
         "https://www.google.com/calendar/about/static/images/logo-calendar.png"),
        
        ("Mailchimp", "Plataforma de marketing por email", "marketing", 
         "https://mailchimp.com", "https://mailchimp.com/developer", 
         "https://us1.api.mailchimp.com/3.0", 
         "https://cdn-images.mailchimp.com/product/brand_assets/logos/mc-freddie-dark.svg"),
        
        ("Notion", "Plataforma de produtividade e organização", "productivity", 
         "https://notion.so", "https://developers.notion.com", 
         "https://api.notion.com/v1", 
         "https://www.notion.so/images/logo-ios.png"),
        
        ("Google Chat", "Plataforma de mensagens do Google Workspace", "communication", 
         "https://chat.google.com", "https://developers.google.com/chat/api", 
         "https://chat.googleapis.com/v1", 
         "https://www.google.com/chat/about/static/images/logo-chat.png"),
        
        ("Calendly", "Agendamento de reuniões automatizado", "productivity", 
         "https://calendly.com", "https://developer.calendly.com", 
         "https://api.calendly.com", 
         "https://calendly.com/favicon.ico"),
        
        ("Discord", "Plataforma de comunicação para comunidades", "communication", 
         "https://discord.com", "https://discord.com/developers/docs", 
         "https://discord.com/api/v10", 
         "https://assets-global.website-files.com/6257adef93867e50d84d30e2/62595384e89d1d54d704ece7_3437c10597c1526c3dbd98c737c2bcae.svg"),
        
        ("Google Docs", "Editor de documentos online do Google", "productivity", 
         "https://docs.google.com", "https://developers.google.com/docs/api", 
         "https://docs.googleapis.com/v1", 
         "https://www.google.com/docs/about/static/images/logo-docs.png"),
        
        ("Google Ads", "Plataforma de publicidade do Google", "marketing", 
         "https://ads.google.com", "https://developers.google.com/google-ads/api", 
         "https://googleads.googleapis.com/v14", 
         "https://www.google.com/ads/static/images/logo-ads.png"),
        
        ("YouTube", "Plataforma de vídeos do Google", "media", 
         "https://youtube.com", "https://developers.google.com/youtube/v3", 
         "https://www.googleapis.com/youtube/v3", 
         "https://www.youtube.com/img/desktop/yt_1200.png"),
        
        ("Telegram", "Aplicativo de mensagens instantâneas", "communication", 
         "https://telegram.org", "https://core.telegram.org/api", 
         "https://api.telegram.org/bot", 
         "https://telegram.org/img/t_logo.png"),
        
        ("GitHub", "Plataforma de hospedagem de código", "development", 
         "https://github.com", "https://docs.github.com/en/rest", 
         "https://api.github.com", 
         "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"),
        
        ("Google Slides", "Apresentações online do Google", "productivity", 
         "https://slides.google.com", "https://developers.google.com/slides/api", 
         "https://slides.googleapis.com/v1", 
         "https://www.google.com/slides/about/static/images/logo-slides.png"),
        
        ("RD Station", "Plataforma de marketing digital brasileira", "marketing", 
         "https://rdstation.com", "https://developers.rdstation.com", 
         "https://api.rd.services", 
         "https://cdn.rd.gt/assets/images/rd-station-logo.svg"),
        
        ("Amazon S3", "Serviço de armazenamento em nuvem da AWS", "storage", 
         "https://aws.amazon.com/s3", "https://docs.aws.amazon.com/AmazonS3/latest/API/Welcome.html", 
         "https://s3.amazonaws.com", 
         "https://a0.awsstatic.com/libra-css/images/logos/aws_smile-header-desktop-en-white_59x35.png"),
        
        ("Apify", "Plataforma de web scraping e automação", "automation", 
         "https://apify.com", "https://docs.apify.com", 
         "https://api.apify.com/v2", 
         "https://apify.com/favicon-32x32.png")
    ]
    
    try:
        # Verificar aplicativos existentes
        cursor.execute("SELECT name FROM apps WHERE is_active = true")
        existing_apps = [row[0] for row in cursor.fetchall()]
        
        apps_to_create = [app for app in apps if app[0] not in existing_apps]
        
        if not apps_to_create:
            print("Todos os aplicativos já existem na tabela.")
            return
        
        # Criar aplicativos que não existem
        created_count = 0
        for app_data in apps_to_create:
            cursor.execute("""
                INSERT INTO apps (name, description, category, service_url, documentation_url, 
                                api_base_url, logo_url, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, app_data + (True, datetime.now(), datetime.now()))
            created_count += 1
            print(f"Aplicativo '{app_data[0]}' criado")
        
        conn.commit()
        print(f"{created_count} novos aplicativos foram adicionados.")
        
    except Exception as e:
        conn.rollback()
        print(f"Erro ao popular aplicativos: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def populate_app_services():
    """Popula a tabela app_services com serviços"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Serviços para cada aplicativo
    app_services = [
        # Gmail
        ("Gmail", "New Email Received", "trigger", "Triggered when a new email arrives in the inbox", "/gmail/v1/users/{userId}/messages"),
        ("Gmail", "Email Label Changed", "trigger", "Triggered when an email's labels are modified", "/gmail/v1/users/{userId}/messages/{messageId}/modify"),
        ("Gmail", "Send Email", "action", "Send a new email message", "/gmail/v1/users/{userId}/messages/send"),
        ("Gmail", "Create Draft", "action", "Create a new email draft", "/gmail/v1/users/{userId}/drafts"),
        
        # Google Drive
        ("Google Drive", "File Created", "trigger", "Triggered when a new file is created in Drive", "/drive/v3/files"),
        ("Google Drive", "File Modified", "trigger", "Triggered when an existing file is modified", "/drive/v3/files/{fileId}"),
        ("Google Drive", "Upload File", "action", "Upload a new file to Google Drive", "/upload/drive/v3/files"),
        ("Google Drive", "Download File", "action", "Download a file from Google Drive", "/drive/v3/files/{fileId}"),
        
        # Google Sheets
        ("Google Sheets", "Spreadsheet Updated", "trigger", "Triggered when a spreadsheet is modified", "/v4/spreadsheets/{spreadsheetId}"),
        ("Google Sheets", "Data Source Refreshed", "trigger", "Triggered when a data source is refreshed", "/v4/spreadsheets/{spreadsheetId}/values:batchGet"),
        ("Google Sheets", "Create Spreadsheet", "action", "Create a new Google Sheets spreadsheet", "/v4/spreadsheets"),
        ("Google Sheets", "Update Cell Values", "action", "Update values in a spreadsheet", "/v4/spreadsheets/{spreadsheetId}/values:batchUpdate"),
        
        # Google Calendar
        ("Google Calendar", "Event Created", "trigger", "Triggered when a new event is created", "/calendar/v3/calendars/{calendarId}/events"),
        ("Google Calendar", "Event Updated", "trigger", "Triggered when an event is modified", "/calendar/v3/calendars/{calendarId}/events/{eventId}"),
        ("Google Calendar", "Create Event", "action", "Create a new calendar event", "/calendar/v3/calendars/{calendarId}/events"),
        ("Google Calendar", "Update Event", "action", "Update an existing calendar event", "/calendar/v3/calendars/{calendarId}/events/{eventId}"),
        
        # Slack
        ("Slack", "New Message in Channel", "trigger", "Triggered when a new message is posted in a channel", "/conversations.history"),
        ("Slack", "Direct Message Received", "trigger", "Triggered when a direct message is received", "/conversations.history"),
        ("Slack", "Send Message to Channel", "action", "Send a message to a Slack channel", "/chat.postMessage"),
        ("Slack", "Send Direct Message", "action", "Send a direct message to a user", "/chat.postMessage"),
        
        # Trello
        ("Trello", "New Card Created", "trigger", "Triggered when a new card is created on a board", "/1/cards"),
        ("Trello", "Card Moved", "trigger", "Triggered when a card is moved between lists", "/1/cards/{id}/actions"),
        ("Trello", "Create Card", "action", "Create a new card on a Trello board", "/1/cards"),
        ("Trello", "Update Card", "action", "Update an existing card's details", "/1/cards/{id}"),
        
        # WhatsApp
        ("WhatsApp", "Message Received", "trigger", "Triggered when a new message is received", "/v17.0/{phone-number-id}/messages"),
        ("WhatsApp", "Send Text Message", "action", "Send a text message via WhatsApp", "/v17.0/{phone-number-id}/messages"),
        ("WhatsApp", "Send Media Message", "action", "Send a media message (image, video, document)", "/v17.0/{phone-number-id}/messages"),
        
        # Mailchimp
        ("Mailchimp", "New Subscriber", "trigger", "Triggered when a new subscriber joins a list", "/3.0/lists/{list_id}/members"),
        ("Mailchimp", "Add Subscriber", "action", "Add a new subscriber to a list", "/3.0/lists/{list_id}/members"),
        ("Mailchimp", "Send Campaign", "action", "Send an email campaign", "/3.0/campaigns"),
        
        # Notion
        ("Notion", "Page Created", "trigger", "Triggered when a new page is created", "/v1/pages"),
        ("Notion", "Page Updated", "trigger", "Triggered when a page is modified", "/v1/pages/{page_id}"),
        ("Notion", "Create Page", "action", "Create a new Notion page", "/v1/pages"),
        ("Notion", "Update Page", "action", "Update an existing Notion page", "/v1/pages/{page_id}"),
        
        # Google Chat
        ("Google Chat", "New Message", "trigger", "Triggered when a new message is received", "/v1/spaces/{space}/messages"),
        ("Google Chat", "Send Message", "action", "Send a message to Google Chat", "/v1/spaces/{space}/messages"),
        
        # Calendly
        ("Calendly", "Event Scheduled", "trigger", "Triggered when an event is scheduled", "/scheduled_events"),
        ("Calendly", "Create Event Type", "action", "Create a new event type", "/event_types"),
        
        # Discord
        ("Discord", "Message Created", "trigger", "Triggered when a message is created", "/channels/{channel_id}/messages"),
        ("Discord", "Send Message", "action", "Send a message to Discord", "/channels/{channel_id}/messages"),
        
        # Google Docs
        ("Google Docs", "Document Updated", "trigger", "Triggered when a document is modified", "/v1/documents/{documentId}"),
        ("Google Docs", "Create Document", "action", "Create a new Google Docs document", "/v1/documents"),
        
        # Google Ads
        ("Google Ads", "Campaign Updated", "trigger", "Triggered when a campaign is modified", "/v14/customers/{customerId}/campaigns"),
        ("Google Ads", "Create Campaign", "action", "Create a new Google Ads campaign", "/v14/customers/{customerId}/campaigns"),
        
        # YouTube
        ("YouTube", "Video Uploaded", "trigger", "Triggered when a new video is uploaded", "/v3/search"),
        ("YouTube", "Upload Video", "action", "Upload a video to YouTube", "/v3/videos"),
        
        # Telegram
        ("Telegram", "Message Received", "trigger", "Triggered when a message is received", "/getUpdates"),
        ("Telegram", "Send Message", "action", "Send a message via Telegram", "/sendMessage"),
        
        # GitHub
        ("GitHub", "New Issue", "trigger", "Triggered when a new issue is created", "/repos/{owner}/{repo}/issues"),
        ("GitHub", "Create Issue", "action", "Create a new GitHub issue", "/repos/{owner}/{repo}/issues"),
        
        # Google Slides
        ("Google Slides", "Presentation Updated", "trigger", "Triggered when a presentation is modified", "/v1/presentations/{presentationId}"),
        ("Google Slides", "Create Presentation", "action", "Create a new Google Slides presentation", "/v1/presentations"),
        
        # RD Station
        ("RD Station", "New Lead", "trigger", "Triggered when a new lead is created", "/platform/contacts"),
        ("RD Station", "Create Lead", "action", "Create a new lead in RD Station", "/platform/contacts"),
        
        # Amazon S3
        ("Amazon S3", "File Uploaded", "trigger", "Triggered when a file is uploaded to S3", "/{bucket}/{key}"),
        ("Amazon S3", "Upload File", "action", "Upload a file to Amazon S3", "/{bucket}/{key}"),
        
        # Apify
        ("Apify", "Actor Finished", "trigger", "Triggered when an actor finishes execution", "/v2/actor-runs"),
        ("Apify", "Run Actor", "action", "Run an Apify actor", "/v2/actor-runs")
    ]
    
    try:
        # Verificar se já existem serviços
        cursor.execute("SELECT COUNT(*) FROM app_services WHERE is_active = true")
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            print(f"Ja existem {existing_count} serviços na tabela app_services.")
            response = input("Deseja limpar a tabela e recriar os serviços? (s/N): ")
            if response.lower() == 's':
                cursor.execute("DELETE FROM app_services")
                print("Tabela app_services limpa.")
            else:
                print("Operação cancelada.")
                return
        
        # Obter IDs dos aplicativos
        app_ids = {}
        for app_name, _, _, _, _ in app_services:
            if app_name not in app_ids:
                cursor.execute("SELECT id FROM apps WHERE name = %s AND is_active = true", (app_name,))
                result = cursor.fetchone()
                if result:
                    app_ids[app_name] = result[0]
                else:
                    print(f"Aplicativo '{app_name}' não encontrado. Pulando serviços...")
        
        # Inserir os serviços
        created_count = 0
        for app_name, service_name, service_type, description, endpoint_url in app_services:
            if app_name not in app_ids:
                continue
                
            app_id = app_ids[app_name]
            cursor.execute("""
                INSERT INTO app_services (app_id, service_name, service_type, description,
                                        endpoint_url, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (app_id, service_name, service_type, description, endpoint_url, True, datetime.now(), datetime.now()))
            created_count += 1
            print(f"Serviço '{service_name}' ({service_type}) adicionado para {app_name}")
        
        conn.commit()
        print(f"{created_count} serviços foram adicionados à tabela app_services.")
        
        # Mostrar estatísticas
        cursor.execute("""
            SELECT a.name,
                   COUNT(CASE WHEN s.service_type = 'trigger' THEN 1 END) as trigger_count,
                   COUNT(CASE WHEN s.service_type = 'action' THEN 1 END) as action_count
            FROM apps a
            LEFT JOIN app_services s ON a.id = s.app_id AND s.is_active = true
            WHERE a.is_active = true
            GROUP BY a.id, a.name
            ORDER BY a.name
        """)
        
        print(f"\nEstatísticas:")
        for app_name, trigger_count, action_count in cursor.fetchall():
            print(f"   - {app_name}: {trigger_count} triggers, {action_count} actions")
            
    except Exception as e:
        conn.rollback()
        print(f"Erro ao popular serviços: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def main():
    """Função principal para executar a população completa"""
    print("Iniciando população de aplicativos e serviços...")
    
    # Primeiro, popular aplicativos
    print("\nPopulando tabela apps...")
    populate_apps()
    
    # Depois, popular serviços
    print("\nPopulando tabela app_services...")
    populate_app_services()
    
    print("\nPopulação completa concluída!")

if __name__ == "__main__":
    main()