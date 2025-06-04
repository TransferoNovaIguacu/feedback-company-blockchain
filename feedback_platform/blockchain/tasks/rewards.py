from decimal import Decimal
import logging
from celery import shared_task
from django.utils import timezone
from blockchain.models import RewardTransaction, UserProfile
from blockchain.services import BlockchainService
from web3 import Web3

logger = logging.getLogger(__name__)

@shared_task(name="process_reward_batch")
def process_reward_batch():
    try:
        # 1) Instancia o serviço e verifica se o contrato carregou
        service = BlockchainService()
        logger.debug("[STEP] Instanciou BlockchainService")
        if not service.contract:
            logger.error("❌ Contrato não carregado. Não é possível mintar tokens.")
            return None

        # 2) Busca todas as RewardTransaction PENDING com wallet_address não-nulo
        pending_rewards = RewardTransaction.objects.filter(
            status='PENDING',
            tx_type='REWARD',
            user__userprofile__wallet_address__isnull=False
        ).select_related('user__userprofile')

        if not pending_rewards.exists():
            logger.info("Nenhuma recompensa pendente")
            return None

        logger.info(f"Processando {pending_rewards.count()} recompensas pendentes")

        # 3) Agrupa valores por wallet_address (strip() + ignora vazios)
        rewards_by_wallet = {}
        tx_ids = []
        for reward in pending_rewards:
            raw_wallet = reward.user.userprofile.wallet_address
            if raw_wallet is None:
                logger.warning(f"[WARNING] reward.id={reward.id} → wallet_address None. Pulando.")
                continue

            wallet = raw_wallet.strip()
            if wallet == "":
                logger.warning(f"[WARNING] reward.id={reward.id} → wallet_address vazio após strip. Pulando.")
                continue

            if wallet not in rewards_by_wallet:
                rewards_by_wallet[wallet] = Decimal(0)
            rewards_by_wallet[wallet] += reward.amount
            tx_ids.append(reward.id)

        logger.debug(f"[STEP] rewards_by_wallet (raw): {rewards_by_wallet}")

        if not rewards_by_wallet:
            logger.info("Nenhum endereço válido depois de agrupar.")
            return None

        # 4) Valida cada endereço com Web3.is_address(...) e monta listas finais
        valid_wallets = []
        valid_amounts = []
        for wallet, total in rewards_by_wallet.items():
            # Atenção: validar com is_address (underscore), não isAddress
            if not Web3.is_address(wallet):
                logger.warning(f"[WARNING] Endereço inválido: {wallet!r}. Pulando.")
                continue

            checksum_addr = Web3.to_checksum_address(wallet)
            valid_wallets.append(checksum_addr)
            valid_amounts.append(float(total))

        logger.debug(f"[STEP] valid_wallets = {valid_wallets}")
        logger.debug(f"[STEP] valid_amounts = {valid_amounts}")

        if not valid_wallets:
            logger.info("Nenhuma carteira válida após validação final. Abortando.")
            return None

        # 5) Chama batch_mint no serviço
        tx_hash = service.batch_mint(valid_wallets, valid_amounts)

        if not tx_hash:
            logger.error("❌ batch_mint retornou None. Verifique os logs de batch_mint.")
            return None

        # 6) Atualiza as RewardTransaction para PROCESSING e ajusta saldos
        RewardTransaction.objects.filter(id__in=tx_ids).update(
            status='PROCESSING',
            tx_hash=tx_hash,
            processed_at=timezone.now()
        )

        for checksum_addr, amt in zip(valid_wallets, valid_amounts):
            profile = UserProfile.objects.filter(wallet_address=checksum_addr).first()
            if profile:
                profile.virtual_balance -= Decimal(str(amt))
                profile.blockchain_balance += Decimal(str(amt))
                profile.save()
                logger.info(f"✅ Saldo atualizado para {checksum_addr}: {profile.blockchain_balance}")
            else:
                logger.warning(f"❌ Perfil não encontrado para {checksum_addr}")

        logger.info(f"Transação de mint enviada: {tx_hash}")
        return tx_hash

    except Exception as e:
        logger.error(f"❌ Erro ao processar recompensas: {e}")
        return None