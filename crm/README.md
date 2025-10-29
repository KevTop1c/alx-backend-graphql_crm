# CRM Automation & Scheduling Setup Guide

## Overview

This CRM system includes multiple automated tasks for customer management, order reminders, system health checks, stock management, and reporting. The automation uses a combination of cron jobs, django-crontab, and Celery with Redis.

## Prerequisites

### System Requirements

- Python 3.8+
- Django 3.2+
- Redis server
- GraphQL endpoint running on http://localhost:8000/graphql

## Python Dependencies

Add the following to your `requirements.txt`:

```text
django-crontab
celery
django-celery-beat
redis
gql
```

## Installation & Setup

### 1. Basic Django Configuration

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Add to INSTALLED_APPS in crm/settings.py:

```python
INSTALLED_APPS = [
    # ... existing apps ...
    'django_crontab',
    'django_celery_beat',
]
```

3. Run migrations:

```bash
python manage.py migrate
```

## 2. Redis Setup

1. Install Redis:

```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Windows - Download from https://redis.io/download/
```

2. Start Redis service:

```bash
# Linux/macOS
redis-server

# Windows
redis-server.exe
```

## 3. Celery Configuration

1. Create `crm/celery.py` with Redis broker configuration
2. Update `crm/__init__.py` to load Celery app
3. Configure Celery Beat schedule in `crm/settings.py`

### Automated Tasks

### Task 1: Customer Cleanup Script

- **Script:** `crm/cron_jobs/clean_inactive_customers.sh`
- **Schedule:** Every Sunday at 2:00 AM
- **Purpose:** Deletes customers with no orders in the past year
- **Logs:** `/tmp/customer_cleanup_log.txt`

**To activate:**

```bash
chmod +x crm/cron_jobs/clean_inactive_customers.sh
crontab crm/cron_jobs/customer_cleanup_crontab.txt
```

### Task 2: Order Reminders Script

- **Script:** `crm/cron_jobs/send_order_reminders.py`
- **Schedule:** Daily at 8:00 AM
- **Purpose:** Sends reminders for pending orders from the last 7 days
- **Logs:** `/tmp/order_reminders_log.txt`

**To activate:**

```bash
crontab crm/cron_jobs/order_reminders_crontab.txt
```

### Task 3: System Heartbeat Logger

- **Function:** `crm.cron.log_crm_heartbeat`
- **Schedule:** Every 5 minutes
- **Purpose:** Monitors system health and GraphQL endpoint responsiveness
- **Logs:** `/tmp/crm_heartbeat_log.txt`

**To activate:**

```bash
python manage.py crontab add
```

### Task 4: Low Stock Product Updates

- **Function:** `crm.cron.update_low_stock`
- **Schedule:** Every 12 hours
- **Purpose:** Automatically restocks products with inventory below 10 units
- **Logs:** `/tmp/low_stock_updates_log.txt`

**To activate:**

```bash
python manage.py crontab add
```

### Task 5: Weekly CRM Reports

- **Task:** `crm.tasks.generate_crm_report`
- **Schedule:** Every Monday at 6:00 AM
- **Purpose:** Generates weekly reports with customer, order, and revenue metrics
- **Logs:** `/tmp/crm_report_log.txt`

**To activate:**

```bash
# Start Celery worker
celery -A crm worker -l info


# Start Celery Beat scheduler
celery -A crm beat -l info
```

## Service Management

### Starting All Services

1. **Start Redis:**

```bash
redis-server
```

2. **Start Django Development Server:**

```bash
python manage.py runserver
```

3. **Start Celery Worker (in separate terminal):**

```bash
celery -A crm worker -l info
```

4. **Start Celery Beat (in separate terminal):**

```bash
celery -A crm beat -l info
```

5. **Activate Django Crontab:**

```bash
python manage.py crontab add
python manage.py crontab show  # Verify jobs are scheduled
```

### Monitoring Logs

Check the following log files for task execution:

- Customer cleanup: `/tmp/customer_cleanup_log.txt`
- Order reminders: `/tmp/order_reminders_log.txt`
- System heartbeat: `/tmp/crm_heartbeat_log.txt`
- Stock updates: `/tmp/low_stock_updates_log.txt`
- CRM reports: `/tmp/crm_report_log.txt`

### Verification Steps

1. **Check cron jobs:**

```bash
crontab -l
python manage.py crontab show
```

2. **Verify Celery:**

```bash
celery -A crm status
```

3. **Test GraphQL endpoint:**

```bash
curl -X POST http://localhost:8000/graphql -H "Content-Type: application/json" -d '{"query": "{ hello }"}'
```

## Troubleshooting

### Common Issues

1. **Redis Connection Error:**

   - Ensure Redis server is running: `redis-cli ping` (should return "PONG")

2. **Cron Jobs Not Executing:**

   - Verify script permissions: chmod +x script_name.sh
   - Check system cron service: sudo service cron status

3. **Celery Tasks Not Running:**

   - Verify Redis connection
   - Check Celery worker is running
   - Confirm Beat scheduler is active

4. **GraphQL Connection Errors:**
   - Ensure Django development server is running on port 8000
   - Verify GraphQL endpoint is accessible

### Log Locations

All automation tasks log to `/tmp/` directory with descriptive filenames. Monitor these files to verify task execution and identify any issues.

## Security Notes

- Ensure proper file permissions on all scripts
- Consider moving logs from /tmp/ to a persistent location in production
- Secure Redis with authentication in production environments
- Review and adjust cron job permissions as needed
