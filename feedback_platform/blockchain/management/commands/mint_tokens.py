from django.core.management.base import BaseCommand
from blockchain.services import BlockchainService

class Command(BaseCommand):
    help = 'Minta tokens para múltiplos endereços'

    def handle(self, *args, **kwargs):
        service = BlockchainService()
        recipients = ["0xf5b054B8518e9D7f4085feaeD4cBbC642b080ada"]
        amounts = [100]
        
        tx_hash = service.batch_mint(recipients, amounts)
        
        if tx_hash:
            self.stdout.write(self.style.SUCCESS(f"✅ Tokens mintados! Hash da transação: 0x{tx_hash}"))
            self.stdout.write(self.style.SUCCESS(f"🔗 Explorer: https://sepolia.etherscan.io/tx/0x{tx_hash}")) 
        else:
            self.stdout.write(self.style.ERROR("❌ Falha ao mintar tokens"))