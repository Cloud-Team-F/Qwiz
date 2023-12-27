import os

from azure.messaging.webpubsubservice import WebPubSubServiceClient

service = WebPubSubServiceClient.from_connection_string(
    connection_string=os.environ["PubSubConnectionString"], hub="hub"
)


def get_pubsub_client() -> WebPubSubServiceClient:
    """
    Returns the pubsub client for accessing the pubsub service.

    Returns:
        WebPubSubServiceClient: The pubsub client object.
    """
    return service
