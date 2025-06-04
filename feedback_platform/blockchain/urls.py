from django.urls import path
from . import views

urlpatterns = [
    # Essa URL será usada para enviar feedback e criar a RewardTransaction PENDING
    path(
        "feedback/submit/<int:company_id>/",
        views.submit_feedback,
        name="submit-feedback",
    ),
    # (caso queira testar withdraw_tokens, pode criar algo assim:)
    path(
        "tokens/withdraw/",
        views.withdraw_tokens,
        name="withdraw-tokens",
    ),
    # Para aprovar feedback:
    path(
        "feedback/approve/<int:feedback_id>/",
        views.approve_feedback,
        name="approve-feedback",
    ),
]