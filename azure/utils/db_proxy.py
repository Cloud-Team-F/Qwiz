import os

from azure.cosmos import ContainerProxy, CosmosClient

MyCosmos = CosmosClient.from_connection_string(os.environ["AzureCosmosDBConnectionString"])
MainDBProxy = MyCosmos.get_database_client(os.environ["Database"])


def get_user_container() -> ContainerProxy:
    """
    Retrieves the container client for the user container.

    Returns:
        ContainerProxy: The container client for the user container.
    """
    return MainDBProxy.get_container_client(os.environ["UserContainer"])


def get_quizzes_container() -> ContainerProxy:
    """
    Retrieves the container client for the quizzes container.

    Returns:
        ContainerProxy: The container client for the quizzes container.
    """
    return MainDBProxy.get_container_client(os.environ["QuizzesContainer"])
