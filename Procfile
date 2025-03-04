web: gunicorn finance_project.wsgi --log-file -
worker: celery -A finance_project worker --loglevel=info --pool=solo
beat: celery -A finance_project beat --loglevel=info