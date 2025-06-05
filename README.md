# Feedback Platform 🚀

**Plataforma de Feedback para Sites de Empresas com Recompensas Tokenizadas na Blockchain Ethereum (Sepolia)**

## 📌 Visão Geral

Este projeto conecta empresas interessadas em feedbacks com usuários que desejam compartilhar suas experiências em troca de recompensas em tokens Ethereum (ERC-20).  
O sistema permite:

-   Empresas contratarem planos de feedback
-   Usuários ganharem tokens por feedback útil
-   Transações transparentes via contrato inteligente (Solidity)
-   Integração com Django para backend e front-end

----------

## ✅ Funcionalidades Implementadas

Funcionalidade

Status

Contrato Solidity funcional

✅ Deployado na Sepolia

Mint de tokens em lote (`batchMint`)

✅ Implementado

Transferência de tokens (`transfer`)

✅ Implementado

Verificação de saldo (`check_balance`)

✅ Implementado

Deploy automatizado via Django

✅ Comando`deploy_contract`

Controle de permissões (`MINTER_ROLE`)

✅ Usando OpenZeppelin AccessControl

Eventos de contrato (`BatchMinted`)

✅ Ouvinte via Celery

Integração Celery + Redis

✅ Worker ativo

Tarefas assíncronas (`process_reward_batch`)

✅ Funcionando

Comandos Django CLI (`mint_tokens`,`check_balance`)

✅ Prontos

----------

## 🔧 Requisitos Técnicos

### 🐍 Backend

-   Python 3.10+
-   Django 5.2+
-   `web3.py` (para interação com Ethereum)
-   `celery` + `redis` (para background tasks)
-   `.env` com variáveis de ambiente configuradas

### 🧱 Blockchain

-   Solidity 0.8.28+
-   Hardhat (para compilar e deployar contrato)
-   Sepolia Testnet (via Alchemy ou Infura)
-   Carteira MetaMask (para mintar tokens)

### 💾 Banco de Dados

-   SQLite (desenvolvimento local)
-   PostgreSQL (opcional, para produção)

----------

## 🛠️ Como Rodar o Projeto

### 1. Clone o repositório


git clone https://github.com/seu-usuario/feedback_platform.git

cd feedback_platform

### 2. Crie e ative o ambiente virtual



python -m venv .venv

source .venv/bin/activate # Linux/macOS

.venv\Scripts\activate # Windows

### 3. Instale dependências

pip install -r requirements.txt

### 4. Configure o `.env`

Crie um `.env` na pasta `blockchain/`:

env

# blockchain/.env

WEB3_PROVIDER_URL=https://eth-sepolia.g.alchemy.com/v2/SEU_PROJECT_ID

CHAIN_ID=11155111

CONTRACT_ADDRESS=0xBb4C2d327dBb1914ff208c4dCd9A556f952EC5EF

PRIVATE_KEY=0x... # Chave privada do admin

ADMIN_ADDRESS=0x... # Seu endereço Ethereum

REWARD_PER_FEEDBACK=0.5

MIN_WITHDRAWAL=50

### 5. Compile o contrato
cd blockchain/

npx hardhat compile

### 6. Inicie o Redis

redis-server.exe

### 7. Inicie o worker do Celery

celery -A feedback_platform worker --loglevel=info --pool=solo

### 8. Inicie o servidor Django
python manage.py runserver

----------

## 🧪 Comandos Django CLI

### 🧾 Mintar tokens

python manage.py mint_tokens

### 💰 Verificar saldo

python manage.py check_balance 0xf5b054B8518e9D7f4085feaeD4cBbC642b080ada

### 🔄 Transferir tokens

python manage.py transfer_tokens 0xOutroEnderecoHere 50

### 📦 Deploy do contrato

python manage.py deploy_contract

----------

## 📋 Checklist Final para MVP Completo

Item

Status

**Contrato Solidity funcional**

✅ Sim

**Deploy na Sepolia**

✅ Sim

**Mint de tokens via Django**

✅ Sim

**Transferência de tokens**

✅ Sim

**Verificação de saldo**

✅ Sim

**Deploy automatizado**

✅ Sim

**Controle de permissões (MINTER_ROLE)**

✅ Sim

**Eventos de contrato (BatchMinted)**

✅ Sim

**Testes automatizados**

❌ Pendente

**Documentação da integração com blockchain**

❌ Pendente

**Tratamento de erro robusto**

⚠️ Em progresso

----------

## 🧾 Como funciona a parte da Blockchain

### 📄 Contrato Solidity

-   Nome: `FeedbackToken.sol`
-   Rede: **Ethereum Sepolia**
-   Endereço: `0xBb4C2d327dBb1914ff208c4dCd9A556f952EC5EF`
-   Funções:
    -   `batchMint(address[] calldata recipients, uint256[] calldata amounts)`
    -   `transfer(address to, uint256 amount)`
    -   Eventos: `BatchMinted`, `Transfer`, `RoleGranted`

### 🪙 Modelo de Distribuição de Tokens

-   **Recompensa por feedback:** `0.5 FBTK`
-   **Mint em lote:** tokens são criados em massa e atribuídos a usuários
-   **Saque mínimo:** `50 FBTK`
-   **Controle de acesso:** apenas endereços com `MINTER_ROLE` podem mintar tokens

----------

## 🧪 Eventos e Atualização Automática

### 🎯 Evento `BatchMinted`

Detectado via Celery em tempo real:

python

listen_for_batch_mint_events.delay()

### 📈 Atualização de saldos

Quando o evento `BatchMinted` é detectado, o sistema atualiza automaticamente os saldos no banco de dados Django.

----------

## 🧪 Testes Automatizados (Pendente)

-   Testar `BlockchainService` com mocks do Web3.py
-   Testar `process_reward_batch` com fixtures de `RewardTransaction`
-   Testar `check_balance` e `transfer_tokens` via Django shell
-   Testar eventos com `BatchMinted` e `Transfer`

----------

## 📚 Documentação da Integração com Blockchain

### 🔐 Configuração

Use o `.env` para armazenar credenciais sensíveis:

env

PRIVATE_KEY=0x... # Não versione no Git!

CONTRACT_ADDRESS=0x...

WEB3_PROVIDER_URL=https://...

### 🧾 Funções do `BlockchainService`

Método

Descrição

`deploy_contract()`

Deploya o contrato e atualiza o endereço no`.env`

`batch_mint(recipients, amounts)`

Minta tokens para múltiplos endereços

`transfer(to_address, amount)`

Transfere tokens para outro endereço

`check_balance(address)`

Verifica o saldo de tokens de um usuário

`has_minter_role(address)`

Verifica se um endereço tem permissão para mintar

`listen_for_batch_mint_events()`

Ouvinte de eventos para atualização em tempo real

----------

## 📝 Fluxo de Recompensas

1.  **Usuário envia feedback**
2.  **Sistema cria uma `RewardTransaction` com status `PENDING`**
3.  **Worker do Celery processa a fila com `process_reward_batch`**
4.  **Tokens são mintados via `batchMint` no contrato**
5.  **Saldo do usuário é atualizado no Django**
6.  **Evento `BatchMinted` é escutado e atualiza saldos automaticamente**

----------

## 📁 Estrutura do Projeto

feedback_platform/

├── feedback_platform/ # Configuração do Django

│ ├── celery.py

│ └── settings.py

├── blockchain/ # Integração com Ethereum

│ ├── contracts/ # FeedbackToken.sol

│ ├── tasks/ # Tarefas assíncronas (Celery)

│ ├── services.py # Interação com contrato

│ └── models.py # UserProfile, RewardTransaction

└── manage.py

----------

## 🧰 Comandos Úteis

# Deploy do contrato

python manage.py deploy_contract

  

# Mintar tokens

python manage.py mint_tokens

  

# Verificar saldo

python manage.py check_balance 0xf5b054B8518e9D7f4085feaeD4cBbC642b080ada

  

# Transferir tokens

python manage.py transfer_tokens 0xOutroEnderecoHere 50

----------

## 🧠 Dicas de Desenvolvimento

### 🧾 Logs

Use o logging do Django para depurar transações e eventos:

python

import logging

logger = logging.getLogger(__name__)

### 🧪 Debugar no Etherscan

Acesse:  
[https://sepolia.etherscan.io/address/0xBb4C2d327dBb1914ff208c4dCd9A556f952EC5EF](https://sepolia.etherscan.io/address/0xBb4C2d327dBb1914ff208c4dCd9A556f952EC5EF)

### 🧾 Validação de Eventos

Use o Django shell para validar eventos:

bash

python manage.py shell

python

from blockchain.tasks.events import listen_for_batch_mint_events

listen_for_batch_mint_events.delay()

----------

## 🛡️ Segurança

-   **Chave privada:** nunca versione no Git (use `.gitignore .env`)
-   **Permissões no contrato:** `MINTER_ROLE` é necessário para mintar tokens
-   **Transações seguras:** todas as funções Solidity têm `onlyRole(MINTER_ROLE)`
-   **Auditoria:** eventos `BatchMinted` são registrados no Django

----------

## 🧪 Problemas Comuns e Soluções

### 🔴 Erro: `No result backend is configured`

➡️ Adicione no `settings.py`:

python

CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

### 🔴 Erro: `NotRegistered: 'blockchain.tasks.rewards.process_reward_batch'`

➡️ Confirme que `blockchain` está em `INSTALLED_APPS`

### 🔴 Erro: `PrivateKey invalido`

➡️ Confirme que `PRIVATE_KEY` no `.env` começa com `0x` e é válido

### 🔴 Erro: `gasPrice': None`

➡️ Use `generate_gas_price` no `services.py`:

python

'gasPrice': self.w3.eth.generate_gas_price({'maxPriorityFeePerGas': 2e9})

----------

## 📈 Próximos Passos Recomendados

1.  **Adicionar testes unitários**
    
    -   Para `BlockchainService`
    -   Para `process_reward_batch`
    -   Para `events.py`
2.  **Documentar a API do Django**
    
    -   Usar Swagger ou Django REST Framework
3.  **Implementar interface web para feedbacks**
    
    -   Formulário de feedback
    -   Histórico de recompensas
    -   Botão de saque de tokens
4.  **Validar o contrato no Etherscan**
    
    -   [https://sepolia.etherscan.io/verifyContract](https://sepolia.etherscan.io/verifyContract)
    
5.  **Melhorar tratamento de erro**
    
    -   Adicionar retry automático para transações
    -   Melhorar logs de falha
    -   Validação de `tx_hash` e `receipt.status`

----------

### 🧑‍💻 Contribuição

Se você quiser contribuir com melhorias (testes, front-end, validação de eventos), fique à vontade!  
Pull requests são bem-vindos.

----------

### 📄 Licença

MIT License – veja `LICENSE` para detalhes.

----------
