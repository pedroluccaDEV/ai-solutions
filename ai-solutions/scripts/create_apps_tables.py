import psycopg2
import os
from datetime import datetime

def create_apps_tables():
    """Cria as tabelas apps e app_services no PostgreSQL"""
    
    # Configuração da conexão PostgreSQL
    conn = psycopg2.connect(
        host="localhost",
        port="5433",
        database="saphien",
        user="postgres",
        password="root"
    )
    
    try:
        with conn.cursor() as cursor:
            # Criar tabela apps
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS apps (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    description TEXT,
                    category VARCHAR(100),
                    service_url VARCHAR(500),
                    documentation_url VARCHAR(500),
                    api_base_url VARCHAR(500),
                    logo_url VARCHAR(500),
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Criar tabela app_services
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_services (
                    id SERIAL PRIMARY KEY,
                    app_id INTEGER REFERENCES apps(id) ON DELETE CASCADE,
                    service_name VARCHAR(255) NOT NULL,
                    service_type VARCHAR(50) NOT NULL CHECK (service_type IN ('trigger', 'action')),
                    description TEXT,
                    endpoint_url VARCHAR(500),
                    http_method VARCHAR(10),
                    request_schema JSONB,
                    response_schema JSONB,
                    parameters JSONB,
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Criar índices
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_apps_name ON apps(name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_apps_category ON apps(category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_services_app_id ON app_services(app_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_services_service_type ON app_services(service_type)")
            
            conn.commit()
            print("Tabelas apps e app_services criadas com sucesso!")
            
    except Exception as e:
        conn.rollback()
        print(f"Erro ao criar tabelas: {e}")
    finally:
        conn.close()

def populate_initial_apps():
    """Popula a tabela com aplicativos iniciais"""
    
    conn = psycopg2.connect(
        host="localhost",
        port="5433",
        database="saphien",
        user="postgres",
        password="root"
    )
    
    try:
        with conn.cursor() as cursor:
            # Aplicativos populares
            apps_data = [
                {
                    'name': 'Gmail',
                    'description': 'Serviço de email do Google',
                    'category': 'email',
                    'service_url': 'https://mail.google.com',
                    'documentation_url': 'https://developers.google.com/gmail/api',
                    'api_base_url': 'https://gmail.googleapis.com',
                    'logo_url': 'https://www.google.com/gmail/about/static/images/logo-gmail.png'
                },
                {
                    'name': 'Google Drive',
                    'description': 'Serviço de armazenamento em nuvem do Google',
                    'category': 'storage',
                    'service_url': 'https://drive.google.com',
                    'documentation_url': 'https://developers.google.com/drive/api',
                    'api_base_url': 'https://www.googleapis.com/drive/v3',
                    'logo_url': 'https://www.google.com/drive/static/images/drive/logo-drive.png'
                },
                {
                    'name': 'Slack',
                    'description': 'Plataforma de comunicação em equipe',
                    'category': 'communication',
                    'service_url': 'https://slack.com',
                    'documentation_url': 'https://api.slack.com',
                    'api_base_url': 'https://slack.com/api',
                    'logo_url': 'https://a.slack-edge.com/80588/marketing/img/meta/slack_hash_256.png'
                },
                {
                    'name': 'Trello',
                    'description': 'Ferramenta de gerenciamento de projetos',
                    'category': 'productivity',
                    'service_url': 'https://trello.com',
                    'documentation_url': 'https://developer.atlassian.com/cloud/trello',
                    'api_base_url': 'https://api.trello.com/1',
                    'logo_url': 'https://d2k1ftgv7pobq7.cloudfront.net/meta/u/res/images/trello-header-logos/167dc5b8fb13d7c3c6ab6d3d44a6c3d4/trello-logo-blue.png'
                },
                {
                    'name': 'WhatsApp',
                    'description': 'Aplicativo de mensagens',
                    'category': 'communication',
                    'service_url': 'https://whatsapp.com',
                    'documentation_url': 'https://developers.facebook.com/docs/whatsapp',
                    'api_base_url': 'https://graph.facebook.com/v17.0',
                    'logo_url': 'https://static.whatsapp.net/rsrc.php/v3/y7/r/DSxOAUB0raA.png'
                },
                {
                    'name': 'Google Forms',
                    'description': 'Ferramenta de criação de formulários',
                    'category': 'forms',
                    'service_url': 'https://forms.google.com',
                    'documentation_url': 'https://developers.google.com/forms/api',
                    'api_base_url': 'https://forms.googleapis.com/v1',
                    'logo_url': 'https://www.gstatic.com/forms/logo_single_rgb_48dp.png'
                }
            ]
            
            for app_data in apps_data:
                # Primeiro verificar se o app já existe
                cursor.execute("SELECT id FROM apps WHERE name = %s", (app_data['name'],))
                existing_app = cursor.fetchone()
                
                if not existing_app:
                    cursor.execute("""
                        INSERT INTO apps (name, description, category, service_url, documentation_url, api_base_url, logo_url)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        app_data['name'],
                        app_data['description'],
                        app_data['category'],
                        app_data['service_url'],
                        app_data['documentation_url'],
                        app_data['api_base_url'],
                        app_data['logo_url']
                    ))
            
            conn.commit()
            print("Aplicativos iniciais populados com sucesso!")
            
    except Exception as e:
        conn.rollback()
        print(f"Erro ao popular aplicativos: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_apps_tables()
    populate_initial_apps()