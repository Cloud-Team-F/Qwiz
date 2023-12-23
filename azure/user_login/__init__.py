import json
import logging

from azure.functions import HttpRequest, HttpResponse
from models.user import InvalidField, MissingField, User
from utils import create_error_response, get_user_container

# Proxy to CosmosDB
UserContainerProxy = get_user_container()


def main(req: HttpRequest) -> HttpResponse:
    logging.info("Processing user login request.")

    try:
        req_body = req.get_json()
    except ValueError:
        return create_error_response("Request body must be JSON.", 400)

    try:
        username = req_body["username"].strip().lower()
        password = req_body["password"].strip()

        # validate username and password
        User.is_valid(username, password)

        # check if user exists
        users = list(
            UserContainerProxy.query_items(
                query="SELECT * FROM c WHERE c.username = @username",
                parameters=[
                    {"name": "@username", "value": username},
                ],
                enable_cross_partition_query=True,
            )
        )

        # if no user found
        if len(users) == 0:
            return create_error_response("User not found.", 404)

        # if user found, check password matches
        user = User.from_dict(users[0])
        if user.check_password(password):
            return HttpResponse(
                body=json.dumps(
                    {
                        "id": user.id,
                        "username": user.username,
                    }
                ),
                status_code=200,
                mimetype="application/json",
            )
        return create_error_response("Incorrect password.", 401)

    except KeyError:
        return create_error_response("Missing field(s).", 400)
    except MissingField as e:
        return create_error_response(str(e), 400)
    except InvalidField as e:
        return create_error_response(str(e), 400)
    except Exception as e:
        logging.error("Login error: ", e)
        return create_error_response("An error occurred.", 500)
