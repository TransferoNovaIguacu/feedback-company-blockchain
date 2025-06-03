# blockchain/apps.py
from django.apps import AppConfig

class BlockchainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blockchain'
    
    def ready(self):
        import blockchain.tasks.rewards
        import blockchain.tasks.events