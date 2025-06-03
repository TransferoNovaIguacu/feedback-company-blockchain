# feedback_platform/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'feedback_platform.settings')

app = Celery('feedback_platform')

# Configurações essenciais
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()  # Mantenha apenas isso

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')