from django.core.management.base import BaseCommand
from blockchain.models import UserProfile
from collections import defaultdict

class Command(BaseCommand):
    help = 'Remove perfis duplicados'

    def handle(self, *args, **kwargs):
        # Agrupa perfis pelo wallet_address
        address_map = defaultdict(list)
        for profile in UserProfile.objects.all():
            address_map[profile.wallet_address].append(profile)

        # Remove duplicados, deixando apenas um por endereço
        for address, profiles in address_map.items():
            if len(profiles) > 1:
                main_profile = profiles[0]
                for profile in profiles[1:]:
                    # Transfere o saldo para o perfil principal
                    main_profile.virtual_balance += profile.virtual_balance
                    main_profile.blockchain_balance += profile.blockchain_balance
                    main_profile.save()
                    
                    # Deleta o perfil duplicado
                    profile.delete()
                self.stdout.write(self.style.SUCCESS(f"✅ Corrigido: {len(profiles)} perfis com {address}"))
        
        self.stdout.write(self.style.SUCCESS("✅ Todos os perfis duplicados removidos!"))