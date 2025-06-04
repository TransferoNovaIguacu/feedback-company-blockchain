import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'feedback_platform.settings')
django.setup()

from blockchain.services import BlockchainService

def test_batch_mint():
    service = BlockchainService()
    
    print("Contrato carregado?", service.contract is not None)
    print("Endereço admin:", service.admin_address)
    
    recipients = ["0xf5b054B8518e9D7f4085feaeD4cBbC642b080ada"]
    amounts = [0.5]
    
    tx_hash = service.batch_mint(recipients, amounts)
    print("Resultado:", tx_hash)

if __name__ == "__main__":
    test_batch_mint()