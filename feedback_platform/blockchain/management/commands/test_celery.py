import eventlet
eventlet.monkey_patch()

from celery import Celery
app = Celery('test', broker='redis://localhost:6379/0')
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    result_backend='redis://localhost:6379/0',
)

@app.task
def add(x, y):
    return x + y

if __name__ == '__main__':
    result = add.delay(4, 5)
    print("Resultado:", result.get())