from eth_account import Account
new_account = Account.create()
print("Endereço:", new_account.address)
print("Chave privada:", new_account.key.hex())