"""Cron jobs for CRM App"""

from datetime import datetime
import requests
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport


# pylint: disable=unspecified-encoding
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
