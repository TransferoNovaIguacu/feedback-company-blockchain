import logging
from celery import Celery
from django.conf import settings

logger = logging.getLogger(__name__)

app = Celery('blockchain')
app.config_from_object('django.conf:settings', namespace='CELERY')

@app.task(name="demo_task")
def demo_task():
    logger.info("✅ TAREFA DEMO EXECUTADA COM SUCESSO!")
    print("=== TAREFA EXECUTADA NO CONSOLE ===")
    return "RESULTADO DA TAREFA"