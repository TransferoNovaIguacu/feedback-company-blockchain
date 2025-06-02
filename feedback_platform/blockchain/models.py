from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class Company(models.Model):
    name = models.CharField(max_length=255)

class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)
    is_useful = models.BooleanField(default=False)
    
    
    class Meta:
        ordering = ['-created_at']

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    wallet_address = models.CharField(max_length=42, blank=True, null=True)
    virtual_balance = models.DecimalField(max_digits=36, decimal_places=18, default=0)
    blockchain_balance = models.DecimalField(max_digits=36, decimal_places=18, default=0)

class RewardTransaction(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pendente'),
        ('PROCESSING', 'Processando'),
        ('CONFIRMED', 'Confirmado'),
        ('FAILED', 'Falhou'),
    )
    
    TX_TYPE_CHOICES = (
        ('REWARD', 'Recompensa'),
        ('WITHDRAWAL', 'Saque'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=36, decimal_places=18)
    tx_type = models.CharField(max_length=20, choices=TX_TYPE_CHOICES)
    tx_hash = models.CharField(max_length=66, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    processed_at = models.DateTimeField(null=True, blank=True)