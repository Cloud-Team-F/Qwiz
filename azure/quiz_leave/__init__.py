import json
import logging

from azure.cosmos.exceptions import CosmosHttpResponseError
from azure.functions import HttpRequest, HttpResponse
from utils import create_error_response, get_quizzes_container, get_user_container

# Proxy to CosmosDB
UserContainerProxy = get_user_container()
QuizContainerProxy = get_quizzes_container()


def main(req: HttpRequest) -> HttpResponse:
    logging.info("Leaving quiz")

    try:
        req_body = req.get_json()
    except ValueError:
        return create_error_response("Request body must be JSON.", 400)

    # Get quiz_id from body
    try:
        quiz_id = req_body["quiz_id"]
    except Exception:
        return create_error_response("No quiz id provided", 400)

    # Get user id from body
    try:
        user_id = req_body["user_id"]
    except Exception:
        return create_error_response("No user id provided", 400)

    try:
        quiz = QuizContainerProxy.read_item(item=quiz_id, partition_key=quiz_id)

        if user_id == quiz["user_id"]:
            return create_error_response("User cannot leave their own quiz.", 400)

        if not quiz.get("shared_with") or user_id not in quiz["shared_with"]:
            return create_error_response("User is not in quiz.", 400)

        # Remove the user from shared_with
        quiz["shared_with"].remove(user_id)
        QuizContainerProxy.replace_item(item=quiz, body=quiz)

        return HttpResponse(
            body=json.dumps(
                {
                    "quiz_id": quiz_id,
                    "user_id": user_id,
                }
            ),
            status_code=200,
            mimetype="application/json",
        )
    except CosmosHttpResponseError:
        return create_error_response("Quiz not found.", 404)
    except Exception:
        return create_error_response("Error leaving quiz.", 500)
