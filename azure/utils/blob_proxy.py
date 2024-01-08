import os
import uuid

from azure.storage.blob import BlobClient
from azure.storage.blob.aio import BlobClient as AsyncBlobClient


def get_blob_client(filetype: str = None, blob_name: str = None) -> BlobClient:
    """
    Returns a BlobClient object for accessing a blob in Azure Blob Storage.

    Parameters:
    - filetype (str): The file type of the blob. Default is "pdf".
    - blob_name (str): The name of the blob. Default is a randomly generated UUID.

    Returns:
    - BlobClient: The BlobClient object for accessing the blob.
    """
    if blob_name is None:
        blob_name_gen = str(uuid.uuid4())
    if filetype is None:
        filetype = "pdf"

    return BlobClient.from_connection_string(
        os.environ["AzureStorageConnectionString"],
        container_name=os.environ["DocumentBlobContainer"],
        blob_name=(blob_name_gen + "." + filetype) if blob_name is None else blob_name,
    )


def get_async_blob_client(filetype: str = None, blob_name: str = None) -> AsyncBlobClient:
    """
    Returns an instance of AsyncBlobClient for accessing Azure Blob Storage.

    Args:
        filetype (str, optional): The file type of the blob. Defaults to "pdf".
        blob_name (str, optional): The name of the blob. Defaults to a random UUID.

    Returns:
        AsyncBlobClient: An instance of AsyncBlobClient.

    """
    if blob_name is None:
        blob_name_gen = str(uuid.uuid4())
    if filetype is None:
        filetype = "pdf"

    return AsyncBlobClient.from_connection_string(
        os.environ["AzureStorageConnectionString"],
        container_name=os.environ["DocumentBlobContainer"],
        blob_name=(blob_name_gen + "." + filetype) if blob_name is None else blob_name,
    )
