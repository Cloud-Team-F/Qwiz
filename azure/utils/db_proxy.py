import os

from azure.cosmos import CosmosClient

MyCosmos = CosmosClient.from_connection_string(
    os.environ["AzureCosmosDBConnectionString"]
)
MainDBProxy = MyCosmos.get_database_client(os.environ["Database"])


def get_user_container():
    return MainDBProxy.get_container_client(os.environ["UserContainer"])
