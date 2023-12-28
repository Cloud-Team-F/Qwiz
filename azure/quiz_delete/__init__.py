import json
import logging

from azure.cosmos.exceptions import CosmosHttpResponseError
from azure.functions import HttpRequest, HttpResponse
from utils import create_error_response, get_quizzes_container, get_user_container

# Proxy to CosmosDB
UserContainerProxy = get_user_container()
QuizContainerProxy = get_quizzes_container()


def main(req: HttpRequest) -> HttpResponse:
    logging.info("Deleting quiz")

    try:
        req_body = req.get_json()
    except ValueError:
        return create_error_response("Request body must be JSON.", 400)

    # Get quiz id from body
    try:
        quiz_id = req_body["quiz_id"]
    except Exception:
        return create_error_response("No quiz id provided", 400)

    # Get user id from body
    try:
        user_id = req_body["user_id"]
    except Exception:
        return create_error_response("No author id provided", 400)

    # Get the quiz from the database
    try:
        quiz = QuizContainerProxy.read_item(item=quiz_id, partition_key=quiz_id)
        logging.info("Quiz found")

        # Check if the user is the author of the quiz
        if quiz["user_id"] != user_id:
            return create_error_response("User is not the author of the quiz", 403)
    except CosmosHttpResponseError:
        return create_error_response(f"Quiz with id {quiz_id} not found.", 404)

    # Delete the quiz from the database
    try:
        QuizContainerProxy.delete_item(item=quiz_id, partition_key=quiz_id)
        logging.info("Quiz deleted")
    except CosmosHttpResponseError:
        return create_error_response("Could not delete quiz", 500)

    # Http success response
    return HttpResponse(status_code=204)
