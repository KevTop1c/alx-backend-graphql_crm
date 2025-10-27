"""Cron jobs for CRM App"""

from datetime import datetime
import requests


# pylint: disable=unspecified-encoding
def log_crm_heartbeat():
    """Log heartbeat message to confirm CRM app health"""

    # Get current timestamp
    timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")

    # Base heartbeat message
    heartbeat_message = f"{timestamp} CRM is alive"

    graphql_status = ""
    try:
        # Query a simple field to verify GraphQL endpoint is responsive
        response = requests.post(
            "http://localhost:8000/graphql",
            json={
                "query": """
                    query {
                        __schema {
                            queryType {
                                name
                            }
                        }
                    }
                """
            },
            timeout=5,
        )

        if response.status_code == 200:
            graphql_status = " - GraphQL endpoint responsive"
        else:
            graphql_status = (
                f" - GraphQL endpoint returned status {response.status_code}"
            )

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
