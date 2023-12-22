import json
import logging
import os

from azure.cosmos.exceptions import CosmosHttpResponseError
from azure.functions import HttpRequest, HttpResponse
from models.user import InvalidField, MissingField, User
from utils import create_error_response, get_user_container

# Proxy to CosmosDB
UserContainerProxy = get_user_container()


def main(req: HttpRequest) -> HttpResponse:
    logging.info("Processing user registration request.")

    # Get the request body
    try:
        req_body = req.get_json()
    except ValueError:
        return create_error_response("Request body must be JSON.", 400)

    try:
        # Create a new user
        new_user = User.from_dict(req_body)

        # Check if user is valid
        User.is_valid(new_user.username, new_user.password)
        new_user.hash_password()

        # check if user already exists
        query_result = list(
            UserContainerProxy.query_items(
                query="SELECT * FROM c WHERE c.username = @filter",
                parameters=[dict(name="@filter", value=new_user.username)],
                enable_cross_partition_query=True,
            )
        )
        if len(query_result) != 0:
            return create_error_response(
                f"User with username {new_user.username} already exists.", 409
            )

        # add user to database
        created_user = UserContainerProxy.create_item(
            new_user.to_dict(), enable_automatic_id_generation=True
        )

        # http success response
        return HttpResponse(
            body=json.dumps(
                {
                    "id": created_user["id"],
                    "username": created_user["username"],
                }
            ),
            status_code=201,
            mimetype="application/json",
        )

    except MissingField as e:
        return create_error_response(str(e), 400)
    except InvalidField as e:
        return create_error_response(str(e), 400)
    except CosmosHttpResponseError:
        return create_error_response("Unexpected error occurred with Cosmos DB.", 500)
