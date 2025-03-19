from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finance_project.settings')

app = Celery('finance_project')

app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    enable_utc=True,
    task_track_started=True,
    worker_max_tasks_per_child=1000,
    worker_prefetch_multiplier=1
)

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(['finance_data'])

app.conf.beat_schedule = {
    'update_currency_data_every_midnight': {
        'task': 'finance_data.tasks.update_currency_data',
        'schedule': crontab(hour=0, minute=0),  # كل منتصف ليل
        #'schedule': timedelta(minutes=5),
    },
    'update_predictions_every_midnight': {
        'task': 'finance_data.tasks.update_predictions',
        'schedule': crontab(hour=0, minute=0),
    },
    'update_trading_analytics_every_midnight': {
        'task': 'finance_data.tasks.update_trading_analytics',
        'schedule': crontab(hour=0, minute=0),
    },
    'check_alerts_every_midnight': {
        'task': 'finance_data.tasks.check_alerts',
        'schedule': crontab(hour=0, minute=0),
    },
    'update_trade_statuses_every_midnight': {
        'task': 'finance_data.tasks.update_trade_statuses',
        'schedule': crontab(hour=0, minute=0),
    },
    'update_user_statistics_every_midnight': {
        'task': 'finance_data.tasks.update_user_statistics',
        'schedule': crontab(hour=0, minute=0),
    },
}