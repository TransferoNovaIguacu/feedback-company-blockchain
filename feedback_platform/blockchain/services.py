# feedback_platform/blockchain/services.py
import os
import json
import logging
from pathlib import Path
from django.conf import settings
from web3 import Web3, WebSocketProvider
from web3.exceptions import ContractLogicError, InvalidAddress

# Inicializa o logger
logger = logging.getLogger(__name__)


class BlockchainService:
    def __init__(self, use_ws=False):
        # ✅ Ajusta o provider com base em use_ws
        provider_url = settings.WEB3_WS_PROVIDER_URL if use_ws else settings.WEB3_HTTP_PROVIDER_URL
        
        if use_ws:
            self.w3 = Web3(Web3.WebSocketProvider(provider_url))
            logger.info("[BlockchainService] ✅ Usando WebSocketProvider")
        else:
            self.w3 = Web3(Web3.HTTPProvider(provider_url))
            logger.info("[BlockchainService] 🚫 Usando HTTPProvider")

        # ✅ Valida conexão
        if not self.w3.is_connected():
            logger.error("❌ Falha ao conectar com o provider Ethereum")
            raise ConnectionError("Não foi possível conectar ao provider Ethereum")

        # ✅ Carrega contrato
        if hasattr(settings, 'CONTRACT_ADDRESS') and Web3.is_address(settings.CONTRACT_ADDRESS):
            if not self._load_contract():
                logger.warning("⚠️ Contrato não carregado")
        else:
            logger.warning("⚠️ CONTRACT_ADDRESS não definido ou inválido")

    def _load_contract(self):
        """Carrega o contrato deployado a partir do ABI gerado pelo Hardhat/Truffle/etc."""
        try:
            current_dir = Path(__file__).resolve().parent
            contract_json_path = (
                current_dir / "artifacts" / "contracts" / "FeedbackToken.sol" / "FeedbackToken.json"
            )

            with open(contract_json_path, "r") as f:
                contract_data = json.load(f)
                abi = contract_data["abi"]

            self.contract = self.w3.eth.contract(
                address=settings.CONTRACT_ADDRESS,
                abi=abi,
            )
            return True

        except FileNotFoundError:
            logger.error(
                "❌ Arquivo FeedbackToken.json não encontrado em artifacts/.../FeedbackToken.json"
            )
            self.contract = None
            return False

        except Exception as e:
            logger.error(f"❌ Erro ao carregar contrato: {e}")
            self.contract = None
            return False

    def deploy_contract(self):
        """Faz deploy do contrato na rede, retorna o endereço do novo contrato ou None em caso de falha."""
        try:
            current_dir = Path(__file__).resolve().parent
            contract_json_path = (
                current_dir / "artifacts" / "contracts" / "FeedbackToken.sol" / "FeedbackToken.json"
            )
            with open(contract_json_path, "r") as f:
                contract_data = json.load(f)
                abi = contract_data["abi"]
                bytecode = contract_data["bytecode"]

            FeedbackToken = self.w3.eth.contract(abi=abi, bytecode=bytecode)

            tx = FeedbackToken.constructor().build_transaction(
                {
                    "chainId": settings.CHAIN_ID,
                    "gas": 3000000,
                    "gasPrice": self.w3.eth.generate_gas_price({"maxPriorityFeePerGas": 2_000_000_000}),
                    "nonce": self.w3.eth.get_transaction_count(self.admin_address),
                }
            )

            signed_tx = self.w3.eth.account.sign_transaction(tx, settings.PRIVATE_KEY)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            # Atualiza CONTRACT_ADDRESS em settings e recarrega o contrato
            settings.CONTRACT_ADDRESS = receipt.contractAddress
            self._load_contract()
            return receipt.contractAddress

        except Exception as e:
            logger.error(f"Erro no deploy: {e}")
            return None

    def batch_mint(self, recipients, amounts):
        """
        Recebe:
          - recipients: lista de endereços (strings “0x…” já no checksum)
          - amounts: lista de floats (valores em token, ex: 1.5 significa 1.5 FBTK)
        Constrói a transação batchMint(recipients, amountsEmWei).
        """
        try:
            # 1) Pega o último bloco e tenta usar EIP-1559
            latest_block = self.w3.eth.get_block("latest")
            base_fee = latest_block.get("baseFeePerGas")

            if base_fee is not None:
                max_priority_fee = int(2e9)  # 2 Gwei
                max_fee_per_gas = base_fee + max_priority_fee

                transaction_params = {
                    "type": 2,  # EIP-1559
                    "maxPriorityFeePerGas": max_priority_fee,
                    "maxFeePerGas": max_fee_per_gas,
                    "gas": 5_000_000,
                    "chainId": settings.CHAIN_ID,
                    "nonce": self.w3.eth.get_transaction_count(self.admin_address),
                }
                logger.info(
                    f"✅ batch_mint usando EIP-1559 | Base Fee: {base_fee} | Max Fee: {max_fee_per_gas}"
                )

            else:
                # 2) Fallback para legacy
                gas_price = int(2e9)  # 2 Gwei fixo
                transaction_params = {
                    "gas": 5_000_000,
                    "gasPrice": gas_price,
                    "chainId": settings.CHAIN_ID,
                    "nonce": self.w3.eth.get_transaction_count(self.admin_address),
                }
                logger.info(f"⚠️ batch_mint fallback legacy | gasPrice: {gas_price}")

            # 3) Verifica se existe algum None em recipients
            for idx, r in enumerate(recipients):
                if r is None or not isinstance(r, str) or not r.startswith("0x") or len(r) != 42:
                    logger.error(f"[ERROR] batch_mint recebeu recipients[{idx}] = {r!r}")
                    raise ValueError(f"batch_mint recebeu recipients[{idx}] inválido: {r!r}")

            # 4) Converte amounts → wei e verifica se não há None
            wei_amounts = []
            for amt in amounts:
                if amt is None:
                    raise ValueError("batch_mint recebeu amount None")
                try:
                    wei_amounts.append(int(amt * 10 ** 18))
                except Exception as e:
                    raise ValueError(f"Falha ao converter amount='{amt}' em int wei: {e}")
            logger.debug(f"[DEBUG batch_mint] raw amounts = {amounts}")

            # 5) Constroi a transação corretamente usando transaction_params
            tx = self.contract.functions.batchMint(recipients, wei_amounts).build_transaction(
                transaction_params
            )

            # 6) Assina e envia
            signed_tx = self.w3.eth.account.sign_transaction(tx, settings.PRIVATE_KEY)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            logger.info(f"🔗 Transação batchMint enviada: {tx_hash.hex()}")
            return tx_hash.hex()

        except Exception as e:
            logger.error(f"❌ Erro ao mintar tokens em batch_mint: {e}")
            return None

    def transfer(self, to_address, amount):
        """
        Transfere `amount` tokens (float) para `to_address` (string “0x…”).
        """
        try:
            latest_block = self.w3.eth.get_block("latest")
            base_fee = latest_block["baseFeePerGas"]
            max_priority_fee_per_gas = int(2e9)
            max_fee_per_gas = base_fee + max_priority_fee_per_gas
            amount_wei = int(amount * 10 ** 18)

            tx = self.contract.functions.transfer(to_address, amount_wei).build_transaction(
                {
                    "chainId": settings.CHAIN_ID,
                    "gas": 200_000,
                    "maxPriorityFeePerGas": max_priority_fee_per_gas,
                    "maxFeePerGas": max_fee_per_gas,
                    "nonce": self.w3.eth.get_transaction_count(self.admin_address),
                    "type": 2,
                }
            )

            signed_tx = self.w3.eth.account.sign_transaction(tx, settings.PRIVATE_KEY)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            return tx_hash.hex()

        except Exception as e:
            logger.error(f"Erro na transferência: {e}")
            return None

    def check_balance(self, address):
        """
        Retorna o saldo de tokens de `address` (float, já em unidades normais de token).
        """
        if not self.contract:
            raise Exception("Contrato não carregado")

        balance = self.contract.functions.balanceOf(address).call()
        return balance / 10 ** 18
