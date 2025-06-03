import logging
import time
from celery import shared_task
from web3.exceptions import TransactionNotFound
from django.conf import settings
from blockchain.services import BlockchainService
from blockchain.models import RewardTransaction, UserProfile
from django.db import transaction

logger = logging.getLogger(__name__)

@shared_task(name="listen_for_batch_mint_events", queue='event_queue')
def listen_for_batch_mint_events():
    """Escuta eventos BatchMinted e atualiza o sistema"""
    service = BlockchainService()
    event_filter = service.contract.events.BatchMinted.create_filter(fromBlock='latest')
    
    while True:
        try:
            for event in event_filter.get_new_entries():
                logger.info("Evento BatchMinted detectado: %s", event)
                
                recipients = event['args']['recipients']
                amounts = event['args']['amounts']
                
                for recipient, amount in zip(recipients, amounts):
                    try:
                        with transaction.atomic():
                            profile = UserProfile.objects.get(wallet_address=recipient)
                            profile.blockchain_balance += amount / 10**18
                            profile.save()
                            logger.info(f"✅ Saldo atualizado para {recipient}: {profile.blockchain_balance} FBTK")
                    except UserProfile.DoesNotExist:
                        logger.warning(f"❌ Perfil não encontrado para {recipient}")
                    except Exception as e:
                        logger.error(f"🚨 Erro ao atualizar perfil {recipient}: {e}")
            
            time.sleep(5)

        except Exception as e:
            logger.error(f"❌ Erro ao escutar eventos: {e}")
            time.sleep(10)