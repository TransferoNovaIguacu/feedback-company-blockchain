import os
import json
import time
from venv import logger
from web3 import Web3
from pathlib import Path
from django.conf import settings
from web3.exceptions import ContractLogicError, InvalidAddress

class BlockchainService:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER_URL))
        self.account = self.w3.eth.account.from_key(settings.PRIVATE_KEY)
        self.admin_address = self.account.address
        
        if hasattr(settings, 'CONTRACT_ADDRESS') and self.w3.is_address(settings.CONTRACT_ADDRESS):
            if not self._load_contract():
                logger.warning("⚠️ Contrato não carregado")
        else:
            logger.warning("⚠️ CONTRACT_ADDRESS não definido ou inválido")
    
    def _load_contract(self):
        """Carrega o contrato deployado"""
        try:
            current_dir = Path(__file__).resolve().parent
            contract_json_path = current_dir / 'artifacts' / 'contracts' / 'FeedbackToken.sol' / 'FeedbackToken.json'
            
            with open(contract_json_path, 'r') as f:
                contract_data = json.load(f)
                abi = contract_data['abi']
            
            self.contract = self.w3.eth.contract(
                address=settings.CONTRACT_ADDRESS,
                abi=abi
            )
            return True
        except FileNotFoundError:
            logger.error("❌ Arquivo FeedbackToken.json não encontrado")
            return False
        except Exception as e:
            logger.error(f"❌ Erro ao carregar contrato: {e}")
            self.contract = None
            return False

    def deploy_contract(self):
        """Deploy do contrato na rede"""
        try:
            current_dir = Path(__file__).resolve().parent
            contract_json_path = current_dir / 'artifacts' / 'contracts' / 'FeedbackToken.sol' / 'FeedbackToken.json'
            
            with open(contract_json_path, 'r') as f:
                contract_data = json.load(f)
                abi = contract_data['abi']
                bytecode = contract_data['bytecode']

            FeedbackToken = self.w3.eth.contract(
                abi=abi,
                bytecode=bytecode
            )

            tx = FeedbackToken.constructor().build_transaction({
                'chainId': settings.CHAIN_ID,
                'gas': 3000000,
                'gasPrice': self.w3.eth.generate_gas_price({'maxPriorityFeePerGas': 2e9}),
                'nonce': self.w3.eth.get_transaction_count(self.admin_address),
            })

            signed_tx = self.w3.eth.account.sign_transaction(tx, settings.PRIVATE_KEY)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            settings.CONTRACT_ADDRESS = receipt.contractAddress
            self._load_contract()
            
            return receipt.contractAddress

        except Exception as e:
            print(f"Erro no deploy: {e}")
            return None
    
    def batch_mint(self, recipients, amounts):
        try:
            # Obter base fee do último bloco (EIP-1559)
            latest_block = self.w3.eth.get_block('latest')
            base_fee = latest_block.get('baseFeePerGas')

            if base_fee is not None:
                # Usar transação EIP-1559
                max_priority_fee = int(2e9)  # 2 Gwei
                max_fee_per_gas = base_fee + max_priority_fee
                
                transaction_params = {
                    'type': 2,
                    'maxPriorityFeePerGas': max_priority_fee,
                    'maxFeePerGas': max_fee_per_gas,
                    'gas': 5000000,
                    'chainId': settings.CHAIN_ID,
                    'nonce': self.w3.eth.get_transaction_count(self.admin_address),
                }
                logger.info(f"✅ Usando EIP-1559 | Base Fee: {base_fee} | Max Fee: {max_fee_per_gas}")
            else:
                # Fallback para transação legada (gasPrice)
                gas_price = int(2e9)  # 2 Gwei (fixo)
                
                transaction_params = {
                    'gas': 5000000,
                    'gasPrice': gas_price,
                    'chainId': settings.CHAIN_ID,
                    'nonce': self.w3.eth.get_transaction_count(self.admin_address),
                    # Não incluir 'type' para transações legadas
                }
                logger.info(f"⚠️ Fallback para transação legada | gasPrice: {gas_price}")

            # Construir e assinar transação
            tx = self.contract.functions.batchMint(
                recipients,
                [int(amount * 10**18) for amount in amounts]
            ).build_transaction(transaction_params)

            signed_tx = self.w3.eth.account.sign_transaction(tx, settings.PRIVATE_KEY)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            logger.info(f"🔗 Transação enviada: {tx_hash.hex()}")
            return tx_hash.hex()

        except Exception as e:
            logger.error(f"❌ Erro ao mintar tokens: {e}")
            return None
    
    def transfer(self, to_address, amount):
        try:
            latest_block = self.w3.eth.get_block('latest')
            base_fee = latest_block['baseFeePerGas']

            max_priority_fee_per_gas = int(2e9)
            max_fee_per_gas = base_fee + max_priority_fee_per_gas

            amount_wei = int(amount * 10**18)

            tx = self.contract.functions.transfer(
                to_address,
                amount_wei
            ).build_transaction({
                'chainId': settings.CHAIN_ID,
                'gas': 200000,
                'maxPriorityFeePerGas': max_priority_fee_per_gas,
                'maxFeePerGas': base_fee + 2e9,
                'nonce': self.w3.eth.get_transaction_count(self.admin_address),
                'type': 2,
            })

            signed_tx = self.w3.eth.account.sign_transaction(tx, settings.PRIVATE_KEY)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            return tx_hash.hex()

        except Exception as e:
            print(f"Erro na transferência: {e}")
            return None
        
    def check_balance(self, address):
        """Verifica o saldo de tokens de um endereço"""
        if not self.contract:
            raise Exception("Contrato não carregado")
        
        balance = self.contract.functions.balanceOf(address).call()
        return balance / 10**18