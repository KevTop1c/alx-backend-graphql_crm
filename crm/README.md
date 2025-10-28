# CRM Application - Celery Setup Guide

This guide explains how to configure Celery with Celery Beat to generate a weekly CRM report and log the results.

---

## Setup Steps

- **Install Redis and dependencies**
   - Ensure Redis is installed and running locally (`redis://localhost:6379/0`).
   - Install project dependencies from `requirements.txt`.

- **Run database migrations**
   ```bash
   python manage.py migrate
   ```

- **Start Celery worker**
    ```bash
    celery -A crm worker -l info
    ```

- **Start Celery Beat**
    ```bash
    celery -A crm beat -l info
    ```

- **Verify the weekly CRM report logs**
    - Check logs generated at:
        ```baash
        /tmp/crm_report_log.txt
        ```