#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Change to project directory
cd "$PROJECT_DIR"

# Execute the cleanup command and log results
python manage.py shell << EOF
from django.utils import timezone
from datetime import timedelta
from crm.models import Customer

# Calculate date one year ago
one_year_ago = timezone.now() - timedelta(days=365)

# Find customers with no orders in the last year
inactive_customers = Customer.objects.filter(
    order__isnull=True
).distinct() | Customer.objects.exclude(
    order__order_date__gte=one_year_ago
).distinct()

# Get count before deletion
count_before = inactive_customers.count()

# Delete inactive customers
inactive_customers.delete()

# Log the results
timestamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
log_message = f"[{timestamp}] Deleted {count_before} inactive customers (no orders since {one_year_ago.strftime('%Y-%m-%d')})\n"

with open('/tmp/customer_cleanup_log.txt', 'a') as f:
    f.write(log_message)

print(f"Cleanup completed: {count_before} customers deleted")
EOF