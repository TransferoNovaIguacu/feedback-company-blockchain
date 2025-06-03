from django.core.management.base import BaseCommand
from blockchain.services import BlockchainService

class Command(BaseCommand):
    help = 'Transfere tokens para um endereço'

    def add_arguments(self, parser):
        parser.add_argument('to_address', type=str, help='Endereço de destino')
        parser.add_argument('amount', type=float, help='Quantidade de tokens')

    def handle(self, *args, **options):
        service = BlockchainService()
        to_address = options['to_address']
        amount = options['amount']
        
        tx_hash = service.transfer(to_address, amount)
        
        if tx_hash:
            self.stdout.write(self.style.SUCCESS(f"✅ Tokens transferidos! Hash da transação: {tx_hash}"))
            self.stdout.write(self.style.SUCCESS(f"🔗 Explorer: https://sepolia.etherscan.io/tx/{tx_hash}")) 
        else:
            self.stdout.write(self.style.ERROR("❌ Falha na transferência"))