# feedback_platform/blockchain/tests.py

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.conf import settings
from decimal import Decimal
from unittest import mock

from .models import Company, Feedback, UserProfile, RewardTransaction


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class BlockchainViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Usuário normal e usuário staff
        self.user = User.objects.create_user(username="regular_user", password="senha123")
        self.staff = User.objects.create_user(username="staff_user", password="senha123", is_staff=True)

        # Cria uma empresa para associar ao feedback
        self.company = Company.objects.create(name="Empresa Teste")

        # Cria o perfil com saldo zero
        self.profile = UserProfile.objects.create(
            user=self.user,
            wallet_address="0xABCDEF0123456789abcdef0123456789ABCDEF01",
            virtual_balance=Decimal("0.0"),
            blockchain_balance=Decimal("0.0"),
        )

    def test_submit_feedback_gera_feedback_e_recompensa_pendente(self):
        """
        Ao enviar POST em /api/feedback/submit/<company_id>/:
        - Cria Feedback com is_approved=False
        - Incrementa virtual_balance em settings.REWARD_PER_FEEDBACK
        - Gera uma RewardTransaction(status="PENDING")
        """
        self.client.login(username="regular_user", password="senha123")

        reward_amount = Decimal(settings.REWARD_PER_FEEDBACK)

        url = reverse("submit-feedback", args=[self.company.id])
        response = self.client.post(url, {"comment": "Ótimo serviço!"})

        # Verifica 200 OK e JSON de sucesso
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("new_balance", data)

        # Feedback criado corretamente
        fb = Feedback.objects.filter(user=self.user, company=self.company).first()
        self.assertIsNotNone(fb)
        self.assertEqual(fb.comment, "Ótimo serviço!")
        self.assertFalse(fb.is_approved)

        # virtual_balance incrementou em reward_amount
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.virtual_balance, reward_amount)

        # RewardTransaction PENDING criado com o amount correto
        tx = RewardTransaction.objects.filter(
            user=self.user,
            amount=reward_amount,
            tx_type="REWARD",
            status="PENDING"
        ).first()
        self.assertIsNotNone(tx)
        self.assertIsNone(tx.processed_at)

    def test_withdraw_tokens_saldo_insuficiente_retorna_400(self):
        """
        Se o usuário tentar sacar mais do que tem em blockchain_balance,
        deve receber status 400 e mensagem de saldo insuficiente.
        """
        self.profile.blockchain_balance = Decimal("2.0")
        self.profile.save()

        self.client.login(username="regular_user", password="senha123")
        url = reverse("withdraw-tokens")
        response = self.client.post(url, {"amount": "10.0", "wallet_address": "0xDESTINO"})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("Saldo insuficiente", data["message"])

    @override_settings(MIN_WITHDRAWAL="1.0")
    @mock.patch("blockchain.views.BlockchainService.transfer")
    def test_withdraw_tokens_valido_chama_blockchainservice_transfer(self, mock_transfer):
        """
        Cenário: usuário tem saldo suficiente E MIN_WITHDRAWAL = 1.0.
        - Deve chamar BlockchainService.transfer e retornar o tx_hash
        - Criar RewardTransaction(status="PROCESSING", tx_type="WITHDRAWAL")
        - Diminuir blockchain_balance do perfil
        """
        self.profile.blockchain_balance = Decimal("10.0")
        self.profile.save()

        # Simula que transfer() retorna um tx_hash
        mock_transfer.return_value = "0xFAKEWITHDRAWHASH"

        self.client.login(username="regular_user", password="senha123")
        url = reverse("withdraw-tokens")
        response = self.client.post(
            url, {"amount": "5.0", "wallet_address": "0xDESTINO"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["tx_hash"], "0xFAKEWITHDRAWHASH")

        # RewardTransaction criada com status=PROCESSING
        tx = RewardTransaction.objects.filter(
            user=self.user,
            tx_type="WITHDRAWAL",
            status="PROCESSING"
        ).first()
        self.assertIsNotNone(tx)
        self.assertEqual(tx.amount, Decimal("5.0"))
        self.assertEqual(tx.tx_hash, "0xFAKEWITHDRAWHASH")

        # blockchain_balance deve ter sido reduzido de 10.0 para 5.0
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.blockchain_balance, Decimal("5.0"))

        mock_transfer.assert_called_once()

    def test_approve_feedback_sem_permissao_retorna_302(self):
        """
        Usuário normal (não staff) que visita /api/feedback/approve/<id>/ 
        deve ser redirecionado (302) pela falta de permissão.
        """
        feedback = Feedback.objects.create(
            user=self.user,
            company=self.company,
            comment="Comentário qualquer",
            is_approved=False
        )
        self.client.login(username="regular_user", password="senha123")
        url = reverse("approve-feedback", args=[feedback.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

    def test_approve_feedback_staff_aprova_correto(self):
        """
        Staff faz POST em /api/feedback/approve/<id>/:
        - feedback.is_approved fica True
        - virtual_balance do autor incrementa em settings.REWARD_PER_FEEDBACK
        - gera RewardTransaction(status="PENDING", tx_type="REWARD")
        """
        feedback = Feedback.objects.create(
            user=self.user,
            company=self.company,
            comment="Precisamos melhorar",
            is_approved=False
        )

        # Garante que virtual_balance inicia em 0
        self.profile.virtual_balance = Decimal("0.0")
        self.profile.save()

        # Faz login como staff
        self.client.login(username="staff_user", password="senha123")
        url = reverse("approve-feedback", args=[feedback.id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("Feedback aprovado", data["message"])

        # feedback.is_approved deve ser True
        feedback.refresh_from_db()
        self.assertTrue(feedback.is_approved)

        # virtual_balance deve ter aumentado em reward_amount
        reward_amount = Decimal(settings.REWARD_PER_FEEDBACK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.virtual_balance, reward_amount)

        # Deve existir RewardTransaction PENDING com esse reward_amount
        tx = RewardTransaction.objects.filter(
            user=self.user,
            amount=reward_amount,
            tx_type="REWARD",
            status="PENDING"
        ).first()
        self.assertIsNotNone(tx)
