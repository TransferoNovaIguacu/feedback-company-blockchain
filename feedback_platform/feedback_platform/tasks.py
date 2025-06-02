from decimal import Decimal
import os
import time
import logging
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from blockchain.models import RewardTransaction, UserProfile
from ..blockchain.services import BlockchainService

logger = logging.getLogger(__name__)

@shared_task
def process_reward_batch():
    # Buscar recompensas pendentes
    pending_rewards = RewardTransaction.objects.filter(
        status='PENDING',
        tx_type='REWARD',
        user__userprofile__wallet_address__isnull=False
    ).select_related('user__userprofile')
    
    if not pending_rewards:
        logger.info("Nenhuma recompensa pendente para processar")
        return
    
    logger.info(f"Processando {pending_rewards.count()} recompensas pendentes")
    
    # Agrupar por carteira
    rewards_by_wallet = {}
    transaction_ids = []
    
    for reward in pending_rewards:
        wallet = reward.user.userprofile.wallet_address
        if wallet:
            if wallet not in rewards_by_wallet:
                rewards_by_wallet[wallet] = Decimal(0)
            rewards_by_wallet[wallet] += reward.amount
            transaction_ids.append(reward.id)
    
    # Preparar dados para batch mint
    wallets = list(rewards_by_wallet.keys())
    amounts = [float(amount) for amount in rewards_by_wallet.values()]
    
    try:
        service = BlockchainService()
        tx_hash = service.batch_mint(wallets, amounts)
        
        if tx_hash:
            # Atualizar transações
            RewardTransaction.objects.filter(id__in=transaction_ids).update(
                status='PROCESSING',
                tx_hash=tx_hash,
                processed_at=timezone.now()
            )
            
            # Atualizar saldos dos usuários
            for wallet, amount in rewards_by_wallet.items():
                profile = UserProfile.objects.get(wallet_address=wallet)
                profile.virtual_balance -= amount
                profile.blockchain_balance += amount
                profile.save()
            
            logger.info(f"Transação de mint enviada: {tx_hash}")
            return tx_hash
    
    except Exception as e:
        logger.error(f"Erro ao processar recompensas: {str(e)}")
        # Adicionar lógica de retry ou tratamento de erro
        
    return None