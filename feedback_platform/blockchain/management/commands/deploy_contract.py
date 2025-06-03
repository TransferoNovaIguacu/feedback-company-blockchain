from django.core.management.base import BaseCommand
from blockchain.services import BlockchainService
from django.conf import settings

class Command(BaseCommand):
    help = 'Deploy do contrato na rede configurada'
    
    def handle(self, *args, **options):
        service = BlockchainService()
        contract_address = service.deploy_contract()
        
        if contract_address:
            self.stdout.write(self.style.SUCCESS(
                f'✅ Contrato deployado em: {contract_address}\n'
                f'🔗 Explorer: https://sepolia.etherscan.io/address/{contract_address}'
            ))
            
            self.stdout.write(self.style.WARNING(
                '⚠️ Atualize o CONTRACT_ADDRESS no seu .env!'
            ))
            
            settings.CONTRACT_ADDRESS = contract_address
        else:
            self.stdout.write(self.style.ERROR(
                '❌ Falha no deploy do contrato'
            ))