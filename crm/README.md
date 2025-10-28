# CRM Application – Celery Setup Guide ✅
This project is a Django-based CRM system with automated weekly report generation using Celery, Redis, and Celery Beat. The report runs every Monday at 6:00 AM and logs CRM metrics (customers, orders, revenue).

## ✅ Prerequistes
| Dependency         | Version |
| ------------------ | ------- |
| Python             | 3.10+   |
| Django             | 4.x     |
| Redis              | Latest  |
| Celery             | 5.3+    |
| django-celery-beat | 2.5+    |

---

## ✅ Installation & Setup
### 1️⃣ Clone the project
```bash
git clone https://github.com/<your-org>/<your-repo>.git
cd crm
```

### 2️⃣ Create and activate a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate       # macOS/Linux
venv\Scripts\activate          # Windows
```

### 3️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

---

## ✅ Environment Variables
Create `.env` file in the project root:
```bash
cp .env.example .env
```

Example .env content:
```bash
SECRET_KEY=your_secret_key
DEBUG=True
REDIS_URL=redis://localhost:6379/0
```

---

## ✅ Redis Installation
### On macOS (using Homebrew):
```bash
brew install redis
brew services start redis
```

### On Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

### On Windows:
Download and install Redis from: https://github.com/microsoftarchive/redis/releases

### Or use Docker:
```bash
docker run -d -p 6379:6379 redis:latest
```

### Verify Redis is Running:
```bash
redis-cli ping
# Should return: PONG
```

### Install Dependencies
```bash
pip install -r requirements.txt
```
This will install:
- `celery>=5.3.0`
- `django-celery-beat>=2.5.0`
- `redis>=5.0.0`

--- 

## ✅ Update Django Settings (already included in project)
Confirm these exist inside `crm/settings.py`:
```bash
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
```

---

## ✅ Database Migrations
Run migrations to create the necessary database tables for Celery Beat:
```bash
python manage.py migrate
```

--- 

## ✅ Start the Application Services
Open 3 terminal windows:
| Terminal | Command                        | Purpose         |
| -------- | ------------------------------ | --------------- |
| 1        | `python manage.py runserver`   | Starts Django   |
| 2        | `celery -A crm worker -l info` | Executes tasks  |
| 3        | `celery -A crm beat -l info`   | Schedules tasks |

GraphQL Endpoint:
➡️ http://localhost:8000/graphql

---

## ✅ Verify the Report Task is Working
Manually trigger once:
```bash
python manage.py shell -c "from crm.tasks import generate_crm_report; generate_crm_report()"
```

Check logs:
```
cat /tmp/crm_report_log.txt
tail -f /tmp/crm_report_log.txt
```

Expected output:
```yaml
2024-10-27 06:00:00 - Report: 150 customers, 320 orders, 45230.50 revenue.
```

---

## ✅ Admin Monitoring Commands
```bash
celery -A crm inspect active
celery -A crm inspect scheduled
celery -A crm purge
celery -A crm control shutdown
```

---

## ✅ Running Tests
```bash
python manage.py test
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