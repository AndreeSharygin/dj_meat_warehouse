import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
# Зачем Celery: для периодических задач — проверка просроченных заявок каждый день, отправка уведомлений.

# Ежедневная проверка в 6:00 утра
app.conf.beat_schedule = {
    'check-orders-daily': {
        'task': 'orders.tasks.check_shipment_dates',
        'schedule': crontab(hour=6, minute=0),
    },
}