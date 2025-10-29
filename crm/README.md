# CRM Application Setup

## Install Redis and Dependencies

### Install Redis

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

**Verify Redis is running:**

```bash
redis-cli ping
```

### Install Python Dependencies

```bash
pip install -r requirements.txt
```

## Run Migrations

```bash
python manage.py migrate
```

## Start Celery Worker

```bash
celery -A crm worker -l info
```

## Start Celery Beat

```bash
celery -A crm beat -l info
```

## Verify Logs

Check the logs in `/tmp/crm_report_log.txt`:

```bash
cat /tmp/crm_report_log.txt
```

Or monitor in real-time:

```bash
tail -f /tmp/crm_report_log.txt
```
