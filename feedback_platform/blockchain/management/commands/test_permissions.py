from django.core.management.base import BaseCommand
from blockchain.services import BlockchainService

class Command(BaseCommand):
    help = 'Testa se um endereço sem MINTER_ROLE pode mintar tokens'

    def handle(self, *args, **kwargs):
        service = BlockchainService()
        test_address = "0xaC72AF89c28B198492f242d9225817D5391f328C"
        recipients = [test_address]
        amounts = [100]
        
        tx_hash = service.batch_mint(recipients, amounts)
        
        if tx_hash:
            self.stdout.write(self.style.SUCCESS(f"⚠️ Erro: {test_address} conseguiu mintar tokens!"))
        else:
            self.stdout.write(self.style.SUCCESS("✅ Apenas MINTER_ROLE pode mintar tokens."))