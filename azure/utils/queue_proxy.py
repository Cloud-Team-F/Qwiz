import os

from azure.storage.queue import QueueClient

DocumentsQueue = QueueClient.from_connection_string(
    os.environ["AzureStorageConnectionString"], os.environ["DocumentQueue"]
)


def get_queue_client() -> QueueClient:
    """
    Returns the queue client for accessing the documents queue.

    Returns:
        QueueClient: The queue client object.
    """
    return DocumentsQueue
