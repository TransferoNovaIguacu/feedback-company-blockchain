import os
import django
import time
import logging
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'feedback_platform.settings')
django.setup()

from blockchain.services import BlockchainService
from blockchain.models import UserProfile, User
from blockchain.tasks.events import listen_for_batch_mint_events
from decimal import Decimal

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_test_profile():
    """Cria um perfil de teste"""
    user, created = User.objects.get_or_create(
        username='test_events_user',
        defaults={'password': 'testpass'}
    )
    
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'wallet_address': "0xf5b054B8518e9D7f4085feaeD4cBbC642b080ada",
            'blockchain_balance': Decimal('0.0')
        }
    )
    
    logger.info(f"Perfil de teste: {profile.wallet_address}")
    return profile

def send_test_transaction():
    """Envia uma transação de teste para a blockchain"""
    service = BlockchainService()
    recipients = ["0xf5b054B8518e9D7f4085feaeD4cBbC642b080ada"]
    amounts = [0.5]  # 0.5 tokens
    
    logger.info("Enviando transação de teste...")
    tx_hash = service.batch_mint(recipients, amounts)
    logger.info(f"✅ Transação enviada: {tx_hash}")
    return tx_hash

def run_test():
    print("=== TESTE DE ESCUTA DE EVENTOS ===")
    
    # 1. Configurar perfil de teste
    profile = setup_test_profile()
    print(f"Saldo inicial: {profile.blockchain_balance} FBTK")
    
    # 2. Iniciar a tarefa de escuta
    print("Iniciando tarefa de escuta...")
    task = listen_for_batch_mint_events.delay()
    print(f"ID da tarefa: {task.id}")
    
    # 3. Aguardar 10 segundos para a tarefa iniciar
    print("Aguardando 10 segundos para a tarefa iniciar...")
    time.sleep(10)
    
    # 4. Enviar transação de teste
    tx_hash = send_test_transaction()
    
    # 5. Monitorar por 60 segundos
    print("Monitorando por atualizações (60 segundos)...")
    for i in range(60):
        profile.refresh_from_db()
        print(f"Saldo atual: {profile.blockchain_balance} FBTK")
        time.sleep(1)
    
    print("=== TESTE COMPLETO ===")
    print(f"Saldo final: {profile.blockchain_balance} FBTK")

if __name__ == "__main__":
    run_test()