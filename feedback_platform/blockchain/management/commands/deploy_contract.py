from django.core.management.base import BaseCommand
from blockchain.services import BlockchainService
import os

class Command(BaseCommand):
    help = 'Deploy do contrato na rede configurada'
    
    def handle(self, *args, **options):
        service = BlockchainService()
        contract_address = service.deploy_contract(
            private_key=os.getenv('PRIVATE_KEY')
        )
        
        self.stdout.write(self.style.SUCCESS(
            f'✅ Contrato deployado em: {contract_address}\n'
            f'🔗 Explorer: {service.w3.eth.block_explorer}/address/{contract_address}'
        ))
        
        self.stdout.write(self.style.WARNING(
            '⚠️ Atualize o CONTRACT_ADDRESS no seu .env!'
        ))