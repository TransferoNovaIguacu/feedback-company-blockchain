from __future__ import absolute_import, unicode_literals
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
dotenv_path = BASE_DIR / 'blockchain' / '.env'
load_dotenv(dotenv_path)
print("DEBUG: .env carregado de", dotenv_path)
print("DEBUG: WEB3_PROVIDER_URL lido:", os.environ.get("WEB3_PROVIDER_URL"))

from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'feedback_platform.settings')

app = Celery('feedback_platform')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')