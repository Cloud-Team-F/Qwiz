import json
import logging

from azure.cosmos.exceptions import CosmosHttpResponseError
from azure.functions import HttpRequest, HttpResponse
from utils import create_error_response, get_user_container

# Proxy to CosmosDB
UserContainerProxy = get_user_container()


def main(req: HttpRequest) -> HttpResponse:
    logging.info("Processing user get request.")

    # get user id from request query
    user_id = req.params.get("id")

    if not user_id:
        return create_error_response("Missing user id query.", 400)

    try:
        # get user from database
        user = UserContainerProxy.read_item(item=user_id, partition_key=user_id)
        return HttpResponse(
            body=json.dumps(
                {
                    "id": user["id"],
                    "username": user["username"],
                }
            ),
            status_code=200,
            mimetype="application/json",
        )
    except CosmosHttpResponseError:
        return create_error_response(f"User with id {user_id} not found.", 404)
    except Exception as e:
        logging.error("Get user error: ", e)
        return create_error_response("An error occurred.", 500)
