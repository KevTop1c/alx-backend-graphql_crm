"""Cron jobs for CRM App"""

from datetime import datetime
import requests
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport


# pylint: disable=unspecified-encoding
# pylint: disable=broad-exception-caught
def log_crm_heartbeat():
    """Log heartbeat message to confirm CRM app health"""

    # Get current timestamp
    timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")

    # Base heartbeat message
    heartbeat_message = f"{timestamp} CRM is alive"

    graphql_status = ""
    try:
        # Set up GraphQL transport
        transport = RequestsHTTPTransport(
            url="http://localhost:8000/graphql",
            verify=False,
            retries=3,
        )

        # Initialize the GraphQL client
        client = Client(transport=transport, fetch_schema_from_transport=False)

        # Minimal query to test endpoint responsiveness
        query = gql(
            """
            query {
                __typename
            }
            """
        )

        result = client.execute(query)
        if result.get("__typename"):
            graphql_status = " - GraphQL endpoint responsive"
        else:
            graphql_status = " - GraphQL endpoint responded but with unexpected data"
    except requests.exceptions.RequestException as e:
        graphql_status = f" - GraphQL endpoint unreachable: {str(e)}"

    # Combine message with GraphQL status
    log_message = heartbeat_message + graphql_status + "\n"

    # Append to log file
    try:
        with open("/tmp/crm_heartbeat_log.txt", "a") as log_file:
            log_file.write(log_message)
    except IOError as e:
        # If we can't write to the log file, print to console
        print(f"Error writing to heartbeat log: {e}")
        print(log_message)


def update_low_stock():
    """Runs every 12 hours to update low-stock products and log results."""

    # Define GraphQL transport
    transport = RequestsHTTPTransport(
        url="http://localhost:8000/graphql",
        verify=False,
        retries=3,
    )

    client = Client(transport=transport, fetch_schema_from_transport=False)

    # Define the mutation
    mutation = gql(
        """
        mutation {
            updateLowStockProducts(restockAmount: 50) {
                message
                count
                updatedProducts {
                    name
                    stock
                }
            }
        }
        """
    )

    log_file = "/tmp/low_stock_updates_log.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        result = client.execute(mutation)
        data = result.get("updateLowStockProducts", {})
        message = data.get("message", "No response")
        products = data.get("updatedProducts", [])

        with open(log_file, "a") as f:
            f.write(f"\n[{timestamp}] {message}\n")
            for product in products:
                f.write(f" - {product["name"]}: New stock = {product["stock"]}\n")
    except Exception as e:
        with open(log_file, "a") as f:
            f.write(f"\n[{timestamp}] ERROR: {str(e)}\n")
