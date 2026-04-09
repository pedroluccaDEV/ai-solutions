#!/usr/bin/env python3
"""
Script para popular triggers de exemplo no MongoDB
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Adicionar o caminho do projeto ao Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dao.mongo.v1.trigger_dao import TriggerDAO
from pymongo import MongoClient
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sample_triggers():
    """Criar 3 triggers de exemplo para um usuário de teste"""
    
    # ID do usuário logado (UID do usuário janantoniopereira@gmail.com)
    test_user_id = "JJ9t5xjMIAdbsmM86U2oLHGDGu62"
    
    # Triggers de exemplo
    sample_triggers = [
        {
            "name": "Gmail → Slack - Notificação de Emails Importantes",
            "description": "Envia notificações no Slack quando emails marcados como importantes chegam no Gmail",
            "source_app": "gmail",
            "target_app": "slack",
            "trigger_service": "new_important_email",
            "action_service": "send_channel_message",
            "status": "active",
            "created_by": test_user_id,
            "created_at": datetime.now() - timedelta(days=7),
            "updated_at": datetime.now() - timedelta(days=1),
            "last_run": datetime.now() - timedelta(hours=2),
            "run_count": 15,
            "success_count": 14,
            "error_count": 1
        },
        {
            "name": "GitHub → Trello - Criação de Cards para Issues",
            "description": "Cria automaticamente cards no Trello quando novas issues são abertas no GitHub",
            "source_app": "github",
            "target_app": "trello",
            "trigger_service": "new_issue_created",
            "action_service": "create_card",
            "status": "active",
            "created_by": test_user_id,
            "created_at": datetime.now() - timedelta(days=5),
            "updated_at": datetime.now() - timedelta(hours=6),
            "last_run": datetime.now() - timedelta(hours=3),
            "run_count": 8,
            "success_count": 8,
            "error_count": 0
        },
        {
            "name": "Google Forms → Google Sheets - Backup de Respostas",
            "description": "Salva automaticamente as respostas do Google Forms em uma planilha do Google Sheets",
            "source_app": "google_forms",
            "target_app": "google_sheets",
            "trigger_service": "new_form_response",
            "action_service": "append_row",
            "status": "draft",
            "created_by": test_user_id,
            "created_at": datetime.now() - timedelta(days=2),
            "updated_at": datetime.now() - timedelta(hours=1),
            "last_run": None,
            "run_count": 0,
            "success_count": 0,
            "error_count": 0
        },
        {
            "name": "Trello → Slack - Notificação de Cards Concluídos",
            "description": "Envia notificações no Slack quando cards são movidos para a coluna 'Concluído' no Trello",
            "source_app": "trello",
            "target_app": "slack",
            "trigger_service": "card_moved_to_done",
            "action_service": "send_direct_message",
            "status": "active",
            "created_by": test_user_id,
            "created_at": datetime.now() - timedelta(days=3),
            "updated_at": datetime.now() - timedelta(hours=4),
            "last_run": datetime.now() - timedelta(hours=1),
            "run_count": 12,
            "success_count": 11,
            "error_count": 1
        },
        {
            "name": "Slack → Google Calendar - Criação de Eventos",
            "description": "Cria eventos no Google Calendar baseado em mensagens específicas no Slack",
            "source_app": "slack",
            "target_app": "google_calendar",
            "trigger_service": "message_contains_keyword",
            "action_service": "create_event",
            "status": "draft",
            "created_by": test_user_id,
            "created_at": datetime.now() - timedelta(days=1),
            "updated_at": datetime.now() - timedelta(minutes=30),
            "last_run": None,
            "run_count": 0,
            "success_count": 0,
            "error_count": 0
        }
    ]
    
    try:
        # Conectar ao MongoDB
        client = MongoClient('mongodb://localhost:27017/')
        db = client['saphien']
        
        # Verificar se a coleção triggers existe
        if 'triggers' not in db.list_collection_names():
            logger.info("Criando coleção triggers...")
            db.create_collection('triggers')
        
        # Limpar triggers existentes do usuário de teste
        db.triggers.delete_many({"created_by": test_user_id})
        logger.info(f"Triggers existentes do usuário {test_user_id} removidas")
        
        # Inserir triggers de exemplo
        inserted_ids = []
        for trigger_data in sample_triggers:
            result = db.triggers.insert_one(trigger_data)
            inserted_ids.append(result.inserted_id)
            logger.info(f"Trigger criada: {trigger_data['name']}")
        
        logger.info(f"✅ {len(inserted_ids)} triggers de exemplo criadas com sucesso!")
        logger.info(f"📊 Triggers criadas:")
        for trigger in sample_triggers:
            logger.info(f"   • {trigger['name']} ({trigger['status']})")
        
        # Verificar se as triggers foram criadas
        count = db.triggers.count_documents({"created_by": test_user_id})
        logger.info(f"📈 Total de triggers do usuário: {count}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar triggers de exemplo: {str(e)}")
        return False

def main():
    """Função principal"""
    logger.info("🚀 Iniciando população de triggers de exemplo...")
    
    success = create_sample_triggers()
    
    if success:
        logger.info("✅ População de triggers concluída com sucesso!")
        logger.info("")
        logger.info("📋 Triggers disponíveis para teste:")
        logger.info("   1. Gmail → Slack - Notificação de Emails Importantes")
        logger.info("   2. GitHub → Trello - Criação de Cards para Issues")
        logger.info("   3. Google Forms → Google Sheets - Backup de Respostas")
        logger.info("   4. Trello → Slack - Notificação de Cards Concluídos")
        logger.info("   5. Slack → Google Calendar - Criação de Eventos")
        logger.info("")
        logger.info("💡 Triggers criadas para o usuário 'JJ9t5xjMIAdbsmM86U2oLHGDGu62' (janantoniopereira@gmail.com)")
    else:
        logger.error("❌ Falha na população de triggers")
        sys.exit(1)

if __name__ == "__main__":
    main()