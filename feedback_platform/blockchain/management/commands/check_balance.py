from django.core.management.base import BaseCommand
from blockchain.services import BlockchainService

class Command(BaseCommand):
    help = 'Verifica o saldo de tokens de um endereço'

    def add_arguments(self, parser):
        parser.add_argument('address', type=str, help='Endereço para verificar')

    def handle(self, *args, **options):
        service = BlockchainService()
        address = options['address']
        
        try:
            balance = service.check_balance(address)
            self.stdout.write(self.style.SUCCESS(f"💰 Saldo de {address}: {balance} FBTK"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erro ao verificar saldo: {e}"))