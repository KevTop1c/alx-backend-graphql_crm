#!/usr/bin/env python3


from datetime import datetime, timedelta
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport


# pylint: disable=unspecified-encoding
# pylint: disable=broad-exception-caught
# Configure GraphQL client
transport = RequestsHTTPTransport(
    url="http://localhost:8000/graphql",
    use_json=True,
)

client = Client(transport=transport, fetch_schema_from_transport=True)

# Calculate date 7 days ago
seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

# GraphQL query for pending orders within last 7 days
query = gql(
    """
    query GetPendingOrders($startDate: DateTime!) {
        allOrders(filter: {orderDateGte: $startDate}) {
            id
            orderDate
            customer {
                id
                name
                email
            }
        }
    }
    """
)

try:
    # Execute query
    result = client.execute(query, variable_values={"startDate": seven_days_ago})

    # Get current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Open log file
    with open("/tmp/order_reminders_log.txt", "a") as log_file:
        orders = result.get("orders", [])

        if not orders:
            log_file.write("No pending orders found from the last 7 days.\n")

        ORDER_COUNT = 0
        for order in orders:
            order_id = order.get(id)
            customer_email = order.get("customer", {}).get("email", "N/A")
            order_date = order.get("orderDate", "Unknown date")
            customer_name = order.get("customer", {}).get("name", "Unknown customer")

            # Log order details
            LOG_ENTRY = (
                f"Order ID: {order_id} | "
                f"Customer: {customer_name} ({customer_email}) | "
                f"Order Date: {order_date}\n"
            )
            log_file.write(LOG_ENTRY)
            ORDER_COUNT += 1
        log_file.write(f"Total orders to process: {ORDER_COUNT}\n")

    # Print success message
    print(f"Order reminders processed! Found {ORDER_COUNT} orders from the last 7 days.")

except Exception as e:
    # Log errors
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("/tmp/order_reminders_log.txt", "a") as log_file:
        log_file.write(f"[{timestamp}] ERROR: {str(e)}\n")
    print(f"Error processing order reminders: {str(e)}")
