from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Feedback, UserProfile, RewardTransaction
from django.conf import settings
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from blockchain.services import BlockchainService
from decimal import Decimal, InvalidOperation
from django.contrib.admin.views.decorators import staff_member_required


@login_required
def submit_feedback(request, company_id):
    if request.method == 'POST':
        comment = request.POST.get('comment', '')

        feedback = Feedback.objects.create(
            user=request.user,
            company_id=company_id,
            comment=comment,
            is_approved=False
        )
        
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile.virtual_balance += Decimal(settings.REWARD_PER_FEEDBACK)
        profile.save()
        

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
            
            profile = UserProfile.objects.get(user=request.user)
            if amount > profile.blockchain_balance:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Saldo insuficiente para saque'
                }, status=400)
            
            min_withdrawal = Decimal(settings.MIN_WITHDRAWAL)
            if amount < min_withdrawal:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Saque mínimo é {min_withdrawal} tokens'
                }, status=400)
            

            transaction = RewardTransaction.objects.create(
                user=request.user,
                amount=amount,
                tx_type='WITHDRAWAL',
                status='PENDING'
            )
            
            service = BlockchainService()
            tx_hash = service.transfer(wallet_address, float(amount))
            
            if tx_hash:
                transaction.tx_hash = tx_hash
                transaction.status = 'PROCESSING'
                transaction.save()
                
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

@login_required
@staff_member_required
def approve_feedback(request, feedback_id):
    feedback = get_object_or_404(Feedback, id=feedback_id)
    
    if feedback.is_approved:
        return JsonResponse({'status': 'error', 'message': 'Feedback já aprovado'})
    
    feedback.is_approved = True
    feedback.save()
    
    profile, created = UserProfile.objects.get_or_create(user=feedback.user)
    profile.virtual_balance += Decimal(settings.REWARD_PER_FEEDBACK)
    profile.save()
    
    RewardTransaction.objects.create(
        user=feedback.user,
        amount=Decimal(settings.REWARD_PER_FEEDBACK),
        tx_type='REWARD',
        status='PENDING'
    )
    
    return JsonResponse({
        'status': 'success',
        'message': f'Feedback aprovado! Usuário ganhou {settings.REWARD_PER_FEEDBACK} tokens.'
    })