"""Celery tasks for CRM application"""

from datetime import datetime
from decimal import Decimal
from celery import shared_task
import requests


# pylint: disable=broad-exception-caught
# pylint: disable=unspecified-encoding
@shared_task
def generate_crm_report():
    """
    Generate a weekly CRM report with customer, order, and revenue statistics.
    Queries GraphQL endpoint and logs results to /tmp/crm_report_log.txt
    """

    # GraphQL query to fetch all required data
    graphql_query = """
        query GetCRMStats {
            allCustomers {
                id
            }
            allOrders {
                id
                totalAmount
            }
        }
    """

    try:
        # Query the GraphQL endpoint
        response = requests.post(
            "http://localhost:8000/graphql",
            json={"query": graphql_query},
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        if response.status_code != 200:
            error_msg = (
                f"GraphQL request failed with status code {response.status_code}"
            )
            log_error(error_msg)
            return {"error": error_msg}

        data = response.json()

        # Check for GraphQL errors
        if "errors" in data:
            error_msg = f"GraphQL errors: {data['errors']}"
            log_error(error_msg)
            return {"error": error_msg}

        # Extract data
        customers = data.get("data", {}).get("allCustomers", [])
        orders = data.get("data", {}).get("allOrders", [])

        # Calculate statistics
        total_customers = len(customers)
        total_orders = len(orders)

        # Calculate total revenue
        total_revenue = Decimal("0.00")
        for order in orders:
            amount = order.get("totalAmount")
            if amount is not None:
                try:
                    total_revenue += Decimal(str(amount))
                except (ValueError, TypeError):
                    pass  # Skip invalid amounts

        # Format timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Create report message
        report_message = (
            f"{timestamp} - Report: "
            f"{total_customers} customers, "
            f"{total_orders} orders, "
            f"{total_revenue:.2f} revenue.\n"
        )

        # Log the report
        try:
            with open("/tmp/crm_report_log.txt", "a") as log_file:
                log_file.write(report_message)
        except IOError as e:
            error_msg = f"Error writing to log file: {e}"
            print(error_msg)
            return {"error": error_msg}

        # Return success result
        return {
            "success": True,
            "customers": total_customers,
            "orders": total_orders,
            "revenue": float(total_revenue),
            "timestamp": timestamp,
        }

    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to connect to GraphQL endpoint: {str(e)}"
        log_error(error_msg)
        return {"error": error_msg}

    except Exception as e:
        error_msg = f"Unexpected error generating report: {str(e)}"
        log_error(error_msg)
        return {"error": error_msg}


def log_error(error_message):
    """Helper function to log errors"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"{timestamp} - ERROR: {error_message}\n"

    try:
        with open("/tmp/crm_report_log.txt", "a") as log_file:
            log_file.write(log_message)
    except IOError:
        print(log_message)
