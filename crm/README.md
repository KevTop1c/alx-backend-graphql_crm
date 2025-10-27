# CRM Setup Instructions

1. Install Redis and dependencies.
2. Run migrations using: python manage.py migrate
3. Start Celery worker: celery -A crm worker -l info
4. Start Celery Beat: celery -A crm beat -l info
5. Verify logs in /tmp/crm_report_log.txt

---

### Step 1: Install Redis and dependencies
#### On Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

#### On macOS (using Homebrew):
```bash
brew install redis
brew services start redis
```

#### On Windows:
Download and install Redis from: https://github.com/microsoftarchive/redis/releases

#### Or use Docker:
```bash
docker run -d -p 6379:6379 redis:latest
```

#### Verify Redis is Running:
```bash
redis-cli ping
# Should return: PONG
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```
This will install:
- `celery>=5.3.0`
- `django-celery-beat>=2.5.0`
- `redis>=5.0.0`

#### Update Django Settings
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
---

### Step 2: Run migrations
Run migrations to create the necessary database tables for Celery Beat:
```bash
python manage.py migrate
```
This creates tables for:
- `django_celery_beat_periodictask`
- `django_celery_beat_intervalschedule`
- `django_celery_beat_crontabschedule`
- And other Celery Beat related tables

#### Start the Django Development Server
In one terminal window:
```bash
python manage.py runserver
```
The GraphQL endpoint should be available at http://localhost:8000/graphql

---

### Step 3: Start Celery worker
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

---

### Step 4: Start Celery Beat
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

---

### Step 5: Verify logs
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

---

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