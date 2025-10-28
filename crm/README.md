## Setup Steps
- Install Redis and dependencies.
- Run migrations (python manage.py migrate).
- Start Celery worker (celery -A crm worker -l info).
- Start Celery Beat (celery -A crm beat -l info).
- Verify logs in /tmp/crm_report_log.txt.