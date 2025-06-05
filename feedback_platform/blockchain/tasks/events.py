# blockchain/tasks/events.py
import logging
import time
from decimal import Decimal
from celery import shared_task
from django.conf import settings
from blockchain.services import BlockchainService
from blockchain.models import UserProfile
from django.db import transaction

logger = logging.getLogger(__name__)

@shared_task(name="listen_for_batch_mint_events", queue='event_queue')
def listen_for_batch_mint_events():
    """Escuta eventos BatchMinted e atualiza o sistema via HTTPProvider"""
    try:
        logger.info("🎧 Iniciando escuta de eventos BatchMinted")
        service = BlockchainService(use_ws=False)
        logger.info("✅ Conectado à blockchain via HTTP")
        
        last_block = getattr(settings, 'LAST_PROCESSED_BLOCK', 'latest')

        while True:
            try:
                events = service.contract.events.BatchMinted.get_logs(
                    fromBlock=last_block,
                    toBlock='latest'
                )

                for event in events:
                    logger.info(f"🎉 Evento BatchMinted detectado no bloco {event.blockNumber}")
                    recipients = event.args.recipients
                    amounts = event.args.amounts

                    for recipient, amount in zip(recipients, amounts):
                        try:
                            with transaction.atomic():
                                profile = UserProfile.objects.get(wallet_address__iexact=recipient)
                                token_amount = Decimal(str(amount / 10**18))
                                
                                profile.blockchain_balance += token_amount
                                profile.save(update_fields=['blockchain_balance'])
                                logger.info(f"✅ Saldo atualizado para {recipient}: {profile.blockchain_balance} FBTK")
                        except UserProfile.DoesNotExist:
                            logger.warning(f"❌ Perfil não encontrado para {recipient}")
                        except Exception as e:
                            logger.error(f"🚨 Erro ao atualizar perfil {recipient}: {e}")
                    last_block = event.blockNumber + 1
                    settings.LAST_PROCESSED_BLOCK = last_block

                time.sleep(5)

            except Exception as e:
                logger.error(f"❌ Erro durante a escuta: {e}")
                time.sleep(10)
                service = BlockchainService(use_ws=False)

    except Exception as e:
        logger.exception(f"❌ ERRO CRÍTICO ao iniciar escuta de eventos: {e}")
        raise