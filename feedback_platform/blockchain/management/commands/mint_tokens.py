from django.core.management.base import BaseCommand
from blockchain.services import BlockchainService

class Command(BaseCommand):
    help = 'Minta tokens para múltiplos endereços'
    def handle(self, *args, **kwargs):
        service = BlockchainService()
        recipients = ["0x6D68105c0947bF1BfeB8594D5A771387Eac66E0c"]
        amounts = [100]
        tx_hash = service.batch_mint(recipients, amounts)
        
        if tx_hash:
            self.stdout.write(self.style.SUCCESS(f"✅ Tokens mintados! Hash da transação: 0x{tx_hash}"))
            self.stdout.write(self.style.SUCCESS(f"🔗 Explorer: https://sepolia.etherscan.io/tx/0x{tx_hash}")) 
        else:
            self.stdout.write(self.style.ERROR("❌ Falha ao mintar tokens"))