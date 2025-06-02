from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Feedback, UserProfile, RewardTransaction
from django.conf import settings
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from blockchain.services import BlockchainService
from decimal import Decimal, InvalidOperation


@login_required
def submit_feedback(request, company_id):
    if request.method == 'POST':
        comment = request.POST.get('comment', '')
        
        # Criar feedback
        feedback = Feedback.objects.create(
            user=request.user,
            company_id=company_id,
            comment=comment
        )
        
        # Atualizar saldo virtual
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile.virtual_balance += Decimal(settings.REWARD_PER_FEEDBACK)
        profile.save()
        
        # Criar transação pendente
        RewardTransaction.objects.create(
            user=request.user,
            amount=Decimal(settings.REWARD_PER_FEEDBACK),
            tx_type='REWARD',
            status='PENDING'
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Feedback enviado! Você ganhou ' + 
                       str(settings.REWARD_PER_FEEDBACK) + 
                       ' tokens. Eles serão creditados em breve.',
            'new_balance': str(profile.virtual_balance)
        })
    
    return JsonResponse({'status': 'error', 'message': 'Método inválido'}, status=400)
@login_required
def withdraw_tokens(request):
    if request.method == 'POST':
        try:
            # Validar entrada
            amount = Decimal(request.POST.get('amount', '0'))
            wallet_address = request.POST.get('wallet_address', '').strip()
            
            if amount <= 0:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Valor inválido para saque'
                }, status=400)
            
            if not wallet_address:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Endereço da carteira é obrigatório'
                }, status=400)
            
            # Verificar saldo
            profile = UserProfile.objects.get(user=request.user)
            if amount > profile.blockchain_balance:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Saldo insuficiente para saque'
                }, status=400)
            
            # Verificar mínimo de saque
            min_withdrawal = Decimal(settings.MIN_WITHDRAWAL)
            if amount < min_withdrawal:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Saque mínimo é {min_withdrawal} tokens'
                }, status=400)
            
            # Criar registro de transação
            transaction = RewardTransaction.objects.create(
                user=request.user,
                amount=amount,
                tx_type='WITHDRAWAL',
                status='PENDING'
            )
            
            # Iniciar transferência na blockchain
            service = BlockchainService()
            tx_hash = service.transfer(wallet_address, float(amount))
            
            if tx_hash:
                # Atualizar transação
                transaction.tx_hash = tx_hash
                transaction.status = 'PROCESSING'
                transaction.save()
                
                # Atualizar saldo do usuário
                profile.blockchain_balance -= amount
                profile.save()
                
                return JsonResponse({
                    'status': 'success',
                    'tx_hash': tx_hash,
                    'message': f'Saque iniciado! Transação: {tx_hash}'
                })
            
            return JsonResponse({
                'status': 'error',
                'message': 'Falha ao iniciar saque'
            }, status=500)
            
        except InvalidOperation:
            return JsonResponse({
                'status': 'error',
                'message': 'Valor inválido'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Método inválido'
    }, status=400)