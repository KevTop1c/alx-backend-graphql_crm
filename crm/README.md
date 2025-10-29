# CRM Application - Setup and Documentation

## Overview

This CRM (Customer Relationship Management) application is a Django-based system with GraphQL API integration, automated task scheduling using cron jobs, django-crontab, and Celery Beat for periodic operations including customer cleanup, order reminders, heartbeat monitoring, stock management, and weekly reporting.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Scheduled Tasks Overview](#scheduled-tasks-overview)
5. [Running the Application](#running-the-application)
6. [Verification and Monitoring](#verification-and-monitoring)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

- Python 3.8+
- Django 3.2+
- Redis server
- GraphQL endpoint running at `http://localhost:8000/graphql`
- Linux/Unix environment with cron support

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

The `requirements.txt` includes:

- Django
- graphene-django
- gql
- django-crontab
- celery
- django-celery-beat
- redis

### 2. Install and Start Redis

**Ubuntu/Debian:**

```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**macOS:**

```bash
brew install redis
brew services start redis
```

Verify Redis is running:

```bash
redis-cli ping
# Should return: PONG
```

### 3. Run Database Migrations

```bash
python manage.py migrate
```

This will set up the database schema including tables for django-celery-beat.

## Configuration

### Django Settings

Ensure the following are configured in `crm/settings.py`:

```python
INSTALLED_APPS = [
    # ... other apps
    'django_crontab',
    'django_celery_beat',
]

# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Celery Beat Schedule
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'generate-crm-report': {
        'task': 'crm.tasks.generate_crm_report',
        'schedule': crontab(day_of_week='mon', hour=6, minute=0),
    },
}

# Django-Crontab Jobs
CRONJOBS = [
    ('*/5 * * * *', 'crm.cron.log_crm_heartbeat'),
    ('0 */12 * * *', 'crm.cron.update_low_stock'),
]
```

### Make Shell Scripts Executable

```bash
chmod +x crm/cron_jobs/clean_inactive_customers.sh
```

## Scheduled Tasks Overview

### 1. Customer Cleanup Script (Shell Script + Cron)

**Schedule:** Every Sunday at 2:00 AM

**Purpose:** Deletes customers with no orders in the past year

**Script:** `crm/cron_jobs/clean_inactive_customers.sh`

**Log:** `/tmp/customer_cleanup_log.txt`

**Setup:**

```bash
crontab crm/cron_jobs/customer_cleanup_crontab.txt
```

### 2. Order Reminder Script (Python + Cron)

**Schedule:** Daily at 8:00 AM

**Purpose:** Queries GraphQL for pending orders from the last 7 days and logs reminders

**Script:** `crm/cron_jobs/send_order_reminders.py`

**Log:** `/tmp/order_reminders_log.txt`

**Setup:**

```bash
crontab crm/cron_jobs/order_reminders_crontab.txt
```

### 3. Heartbeat Logger (django-crontab)

**Schedule:** Every 5 minutes

**Purpose:** Logs health check messages to confirm CRM application is alive

**Function:** `crm.cron.log_crm_heartbeat`

**Log:** `/tmp/crm_heartbeat_log.txt`

**Setup:**

```bash
python manage.py crontab add
```

### 4. Low Stock Product Updates (django-crontab + GraphQL Mutation)

**Schedule:** Every 12 hours

**Purpose:** Updates products with stock < 10 by incrementing stock by 10 units

**Function:** `crm.cron.update_low_stock`

**GraphQL Mutation:** `UpdateLowStockProducts`

**Log:** `/tmp/low_stock_updates_log.txt`

**Setup:** Included when running `python manage.py crontab add`

### 5. Weekly CRM Report (Celery Beat)

**Schedule:** Every Monday at 6:00 AM

**Purpose:** Generates weekly report with total customers, orders, and revenue

**Task:** `crm.tasks.generate_crm_report`

**Log:** `/tmp/crm_report_log.txt`

**Setup:** Automatically scheduled via Celery Beat (see [Running the Application](#running-the-application))

## Running the Application

### 1. Start Django Development Server

```bash
python manage.py runserver
```

The GraphQL endpoint will be available at `http://localhost:8000/graphql`

### 2. Add Django-Crontab Jobs

```bash
python manage.py crontab add
```

To view active crontab jobs:

```bash
python manage.py crontab show
```

To remove crontab jobs:

```bash
python manage.py crontab remove
```

### 3. Install System Cron Jobs

For the shell and Python scripts:

```bash
# Install customer cleanup cron
crontab -l > current_crontab
cat crm/cron_jobs/customer_cleanup_crontab.txt >> current_crontab
crontab current_crontab
rm current_crontab

# Install order reminders cron
crontab -l > current_crontab
cat crm/cron_jobs/order_reminders_crontab.txt >> current_crontab
crontab current_crontab
rm current_crontab
```

Or manually edit your crontab:

```bash
crontab -e
```

### 4. Start Celery Worker

Open a new terminal and run:

```bash
celery -A crm worker -l info
```

This starts the Celery worker to process tasks.

### 5. Start Celery Beat

Open another terminal and run:

```bash
celery -A crm beat -l info
```

This starts the Celery Beat scheduler for periodic tasks.

**Alternative:** Run worker and beat together (for development):

```bash
celery -A crm worker --beat -l info
```

## Verification and Monitoring

### Check Log Files

Monitor the various log files to verify tasks are running:

```bash
# Customer cleanup log
tail -f /tmp/customer_cleanup_log.txt

# Order reminders log
tail -f /tmp/order_reminders_log.txt

# Heartbeat log
tail -f /tmp/crm_heartbeat_log.txt

# Low stock updates log
tail -f /tmp/low_stock_updates_log.txt

# Weekly CRM report log
tail -f /tmp/crm_report_log.txt
```

### Verify Cron Jobs

```bash
# System crontab
crontab -l

# Django-crontab jobs
python manage.py crontab show
```

### Test GraphQL Endpoint

Visit `http://localhost:8000/graphql` in your browser to access the GraphQL playground and test queries/mutations.

### Monitor Celery Tasks

Check Celery worker and beat logs for task execution status. You can also use Flower for monitoring:

```bash
pip install flower
celery -A crm flower
```

Then visit `http://localhost:5555`

## Troubleshooting

### Redis Connection Issues

```bash
# Check if Redis is running
redis-cli ping

# Restart Redis
sudo systemctl restart redis-server  # Linux
brew services restart redis          # macOS
```

### Celery Tasks Not Running

1. Ensure Redis is running
2. Check Celery worker is active: `celery -A crm inspect active`
3. Verify Celery Beat is running and scheduling tasks
4. Check `CELERY_BEAT_SCHEDULE` configuration in settings.py

### Cron Jobs Not Executing

1. Check cron service is running: `sudo systemctl status cron`
2. Verify crontab entries: `crontab -l`
3. Check script permissions: Scripts should be executable (`chmod +x`)
4. Review system logs: `grep CRON /var/log/syslog`

### Django-Crontab Issues

1. Ensure `django_crontab` is in `INSTALLED_APPS`
2. Re-add jobs: `python manage.py crontab remove && python manage.py crontab add`
3. Check for syntax errors in `CRONJOBS` configuration

### GraphQL Endpoint Not Accessible

1. Ensure Django server is running on port 8000
2. Verify `graphene-django` is properly configured
3. Check firewall settings if accessing remotely

### Log Files Not Created

1. Verify `/tmp` directory has write permissions
2. Check the user running cron/celery has appropriate permissions
3. Manually create log files with: `touch /tmp/logfile.txt`

## Additional Commands

### Clear All Logs

```bash
rm /tmp/customer_cleanup_log.txt
rm /tmp/order_reminders_log.txt
rm /tmp/crm_heartbeat_log.txt
rm /tmp/low_stock_updates_log.txt
rm /tmp/crm_report_log.txt
```

### Run Tasks Manually

```bash
# Test Django-crontab functions
python manage.py shell
>>> from crm.cron import log_crm_heartbeat, update_low_stock
>>> log_crm_heartbeat()
>>> update_low_stock()

# Test Celery task
python manage.py shell
>>> from crm.tasks import generate_crm_report
>>> generate_crm_report.delay()
```

## Production Considerations

1. **Use a production WSGI server** (e.g., Gunicorn, uWSGI) instead of Django's development server
2. **Configure proper logging** with log rotation for production environments
3. **Use environment variables** for sensitive configuration (Redis URL, secret keys)
4. **Set up monitoring** for Celery workers and Beat scheduler
5. **Use a process manager** (e.g., systemd, supervisor) to keep Celery processes running
6. **Secure GraphQL endpoint** with authentication and rate limiting
7. **Regular backups** of Redis data if using it for result persistence

## Support

For issues or questions, please refer to the official documentation:

- [Django Documentation](https://docs.djangoproject.com/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Graphene-Django Documentation](https://docs.graphene-python.org/projects/django/)
- [Django-Crontab Documentation](https://github.com/kraiz/django-crontab)

---

**Last Updated:** October 2025
