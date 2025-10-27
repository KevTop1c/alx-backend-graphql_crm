# CRM Application - Celery Setup Guide
This guide explains how to set up and run Celery with Celery Beat for automated weekly CRM report generation.

### Prerequisites
- Python 3.8+
- Redis server
- Django project with GraphQL endpoint

### 1. Install Redis
### On Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

### On macOS (using Homebrew):
```bash
brew install redis
brew services start redis
```

### On Windows:
Download and install Redis from: https://github.com/microsoftarchive/redis/releases

#### Or use Docker:
```bash
docker run -d -p 6379:6379 redis:latest
```

### Verify Redis is Running:
```bash
redis-cli ping
# Should return: PONG
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```
This will install:
- `celery>=5.3.0`
- `django-celery-beat>=2.5.0`
- `redis>=5.0.0`

### 3. Update Django Settings
Add the following to your `crm/settings.py`:
```python
from celery.schedules import crontab

INSTALLED_APPS = [
    # ... other apps
    'django_celery_beat',
    'crm',
]

# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']

# Celery Beat Schedule
CELERY_BEAT_SCHEDULE = {
    'generate-crm-report': {
        'task': 'crm.tasks.generate_crm_report',
        'schedule': crontab(day_of_week='mon', hour=6, minute=0),
    },
}

CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
```

### 4. Run Database Migrations
Run migrations to create the necessary database tables for Celery Beat:
```bash
python manage.py migrate
```
This creates tables for:
- `django_celery_beat_periodictask`
- `django_celery_beat_intervalschedule`
- `django_celery_beat_crontabschedule`
- And other Celery Beat related tables

### 5. Start the Django Development Server
In one terminal window:
```bash
python manage.py runserver
```
The GraphQL endpoint should be available at http://localhost:8000/graphql

### 6. Start Celery Worker
In a second terminal window:
```bash
celery -A crm worker -l info
```
You should see output like:
```
-------------- celery@hostname v5.3.x (emerald-rush)
--- ***** ----- 
-- ******* ---- Linux-x.x.x-x-generic-x86_64-with-glibc2.x
- *** --- * --- 
- ** ---------- [config]
- ** ---------- .> app:         crm:0x...
- ** ---------- .> transport:   redis://localhost:6379/0
- ** ---------- .> results:     redis://localhost:6379/0
- *** --- * --- .> concurrency: 8 (prefork)
-- ******* ---- .> task events: OFF
--- ***** ----- 
-------------- [queues]
               .> celery           exchange=celery(direct) key=celery
               

[tasks]
  . crm.celery.debug_task
  . crm.tasks.generate_crm_report

[2024-10-27 10:00:00,000: INFO/MainProcess] Connected to redis://localhost:6379/0
[2024-10-27 10:00:00,000: INFO/MainProcess] mingle: searching for neighbors
[2024-10-27 10:00:01,000: INFO/MainProcess] mingle: all alone
[2024-10-27 10:00:01,000: INFO/MainProcess] celery@hostname ready.
```

### 7. Start Celery Beat
In a third terminal window:
```bash
celery -A crm beat -l info
```
You should see output like:
```
celery beat v5.3.x (emerald-rush) is starting.
__    -    ... __   -        _
LocalTime -> 2024-10-27 10:00:00
Configuration ->
    . broker -> redis://localhost:6379/0
    . loader -> celery.loaders.app.AppLoader
    . scheduler -> django_celery_beat.schedulers.DatabaseScheduler
    . db -> default
    . logfile -> [stderr]@%INFO
    . maxinterval -> 5.00 seconds (5s)
```
Celery Beat will now schedule the `generate_crm_report` task to run every Monday at 6:00 AM.

### 8. Verify Logs
Check the report log file:
```bash
cat /tmp/crm_report_log.txt
```
You should see entries like:
```
2024-10-27 06:00:00 - Report: 150 customers, 320 orders, 45230.50 revenue.
2024-11-03 06:00:00 - Report: 165 customers, 340 orders, 48750.75 revenue.
```

Monitor the log file in real-time:
```bash
tail -f /tmp/crm_report_log.txt
```

### Manual Task Execution (Testing)
### Test the Task Directly (Python Shell):
```bash
python manage.py shell
```

```python
>>> from crm.tasks import generate_crm_report
>>> result = generate_crm_report()
>>> print(result)
```

### Trigger Task via Celery (Asynchronously):
```bash
python manage.py shell
```

```python
>>> from crm.tasks import generate_crm_report
>>> task = generate_crm_report.delay()
>>> print(f"Task ID: {task.id}")
>>> print(f"Task Status: {task.status}")
```

### Using Django Admin
- Navigate to http://localhost:8000/admin/
- Go to "Periodic Tasks" under "DJANGO_CELERY_BEAT"
- View or modify the scheduled tasks
- You can also manually trigger tasks from here

### Celery Beat Schedule Configuration
The task is scheduled with the following crontab expression:
```python
crontab(day_of_week='mon', hour=6, minute=0)
```
This means:
- Day of week: Monday (0 = Sunday, 1 = Monday, ..., 6 = Saturday)
- Hour: 6 (6:00 AM)
- Minute: 0

### Modify the Schedule
To change the schedule, update CELERY_BEAT_SCHEDULE in settings.py:
```python
# Run every day at midnight
'schedule': crontab(hour=0, minute=0),

# Run every Sunday at 9:00 AM
'schedule': crontab(day_of_week='sun', hour=9, minute=0),

# Run every 6 hours
'schedule': crontab(minute=0, hour='*/6'),

# Run on the 1st of every month at 7:00 AM
'schedule': crontab(minute=0, hour=7, day_of_month='1'),
```

After changing the schedule, restart Celery Beat:
```bash
# Stop with Ctrl+C, then restart
celery -A crm beat -l info
```

## Monitoring and Management
### Check Task Status
```bash
celery -A crm inspect active
celery -A crm inspect scheduled
celery -A crm inspect registered
```

### View Worker Stats
```bash
celery -A crm inspect stats
```

### Purge All Tasks
```bash
celery -A crm purge
```

### Control Workers
```bash
# Gracefully shutdown workers
celery -A crm control shutdown

# Restart worker pool
celery -A crm control pool_restart
```

## Troubleshooting
### Redis Connection Issues
**Problem:** `Error: Can't connect to Redis`
#### Solution:
**1. Check if Redis is running:**
```bash   
redis-cli ping
```

**2. Verify Redis URL in settings:**
```python
CELERY_BROKER_URL = 'redis://localhost:6379/0'
```

### Task Not Executing
**Problem:** Task scheduled but not executing
#### Solutions:
1. Ensure both Celery worker AND Celery Beat are running
2. Check worker logs for errors
3. Verify Django server is running on `localhost:8000`
4. Check the database for scheduled tasks:
```bash
python manage.py shell
```
```python
>>> from django_celery_beat.models import PeriodicTask
>>> print(PeriodicTask.objects.all())
```

### GraphQL Endpoint Not Responding
**Problem:** Report shows GraphQL connection errors
#### Solutions:
1. Verify Django server is running
2. Test GraphQL endpoint manually:
```bash   
curl -X POST http://localhost:8000/graphql \
     -H "Content-Type: application/json" \
     -d '{"query":"{ allCustomers { id } }"}'
```
3. Check for authentication requirements

### Permission Issues with Log File
**Problem:** `IOError: Permission denied: /tmp/crm_report_log.txt`
#### Solution:
1. Check file permissions:
```bash
ls -la /tmp/crm_report_log.txt
```

2. Ensure the user running Celery has write access:
```bash
sudo chmod 666 /tmp/crm_report_log.txt
```

## Summary of Commands
```bash
# Installation
pip install -r requirements.txt
python manage.py migrate

# Start services
python manage.py runserver                  # Terminal 1
celery -A crm worker -l info                # Terminal 2
celery -A crm beat -l info                  # Terminal 3

# Testing
python manage.py shell -c "from crm.tasks import generate_crm_report; generate_crm_report()"

# Monitoring
tail -f /tmp/crm_report_log.txt
celery -A crm inspect active
celery -A crm inspect scheduled

# Verify logs
cat /tmp/crm_report_log.txt

# Management
celery -A crm control shutdown
celery -A crm purge
```