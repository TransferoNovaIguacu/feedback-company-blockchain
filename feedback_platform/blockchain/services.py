import os
import json
import time
from web3 import Web3
from django.conf import settings
from web3.exceptions import ContractLogicError

class BlockchainService:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER_URL))
        
        # Carregar ABI do contrato
        current_dir = os.path.dirname(os.path.abspath(__file__))
        abi_path = os.path.join(current_dir, 'abis', 'FeedbackToken.json')
        
        with open(abi_path) as f:
            abi_data = json.load(f)
            self.abi = abi_data['abi']
        
        self.contract = self.w3.eth.contract(
            address=settings.CONTRACT_ADDRESS,
            abi=self.abi
        )
        
        # Configurar conta
        self.account = self.w3.eth.account.from_key(settings.PRIVATE_KEY)
        self.admin_address = self.account.address
    
    def batch_mint(self, recipients, amounts):
        """Mint tokens em lote para múltiplos endereços"""
        try:
            # Construir transação
            tx = self.contract.functions.batchMint(
                recipients,
                [int(amount * 10**18) for amount in amounts]
            ).build_transaction({
                'chainId': settings.CHAIN_ID,
                'gas': 5000000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.admin_address),
            })
            
            # Assinar e enviar
            signed_tx = self.w3.eth.account.sign_transaction(tx, settings.PRIVATE_KEY)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            return tx_hash.hex()
        
        except ContractLogicError as e:
            print(f"Erro de contrato: {e}")
            return None
        except Exception as e:
            print(f"Erro inesperado: {e}")
            return None
    
    def transfer(self, to_address, amount):
        """Transferir tokens para um endereço externo"""
        try:
            # Converter para wei
            amount_wei = int(amount * 10**18)
            
            # Construir transação
            tx = self.contract.functions.transfer(
                to_address,
                amount_wei
            ).build_transaction({
                'chainId': settings.CHAIN_ID,
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.admin_address),
            })
            
            # Assinar e enviar
            signed_tx = self.w3.eth.account.sign_transaction(tx, settings.PRIVATE_KEY)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            return tx_hash.hex()
        
        except Exception as e:
            print(f"Erro na transferência: {e}")
            return None
        
    def deploy_contract(self):
        """Deploy do contrato na rede"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        abi_path = os.path.join(current_dir, 'abis', 'FeedbackToken.json')

        with open(abi_path) as f:
            abi_data = json.load(f)
            bytecode = abi_data['bytecode']

        # Criar contrato
        FeedbackToken = self.w3.eth.contract(
            abi=abi_data['abi'],
            bytecode=bytecode
        )

        # Construir transação de deploy
        tx = FeedbackToken.constructor().build_transaction({
            'chainId': settings.CHAIN_ID,
            'gas': 3000000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.admin_address),
        })

        # Assinar e enviar
        signed_tx = self.w3.eth.account.sign_transaction(tx, settings.PRIVATE_KEY)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        # Esperar pela confirmação
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return receipt.contractAddress