import json
import logging

from azure.cosmos.exceptions import CosmosHttpResponseError
from azure.functions import HttpRequest, HttpResponse
from utils import create_error_response, get_quizzes_container, get_user_container

# Proxy to CosmosDB
UserContainerProxy = get_user_container()
QuizContainerProxy = get_quizzes_container()


def main(req: HttpRequest) -> HttpResponse:
    logging.info("Joining quiz")

    try:
        req_body = req.get_json()
    except ValueError:
        return create_error_response("Request body must be JSON.", 400)

    # Get invite_code from body
    try:
        invite_code = req_body["invite_code"]
    except Exception:
        return create_error_response("No invite code provided", 400)

    # Get user id from body
    try:
        user_id = req_body["user_id"]
    except Exception:
        return create_error_response("No user id provided", 400)

    # Get user from the database with the user id
    try:
        user = UserContainerProxy.read_item(item=user_id, partition_key=user_id)
    except CosmosHttpResponseError:
        return create_error_response("User not found.", 404)

    # Get the quiz from the database with the invite code
    try:
        quizzes = list(
            QuizContainerProxy.query_items(
                query="SELECT * FROM c WHERE c.invite_code = @invite_code",
                parameters=[dict(name="@invite_code", value=invite_code)],
                enable_cross_partition_query=True,
            )
        )

        logging.info("Quizzes: %s", quizzes)

        if len(quizzes) == 0:
            return create_error_response(f"Quiz with invite code {invite_code} not found.", 404)

        # Get invited quiz
        quiz = quizzes[0]

        # User should not be able to join their own quiz
        if user_id == quiz["user_id"]:
            return create_error_response("You cannot join your own quiz.", 400)

        # Check if user is already in quiz
        if user_id in quiz.get("shared_with", []):
            return create_error_response("You are already in this quiz.", 400)

        # Check if quiz is not processed
        if not quiz.get("processed", False):
            return create_error_response("Quiz is not processed yet.", 400)

        # Add user to quiz shared_with
        if "shared_with" not in quiz:
            quiz["shared_with"] = [user_id]
        else:
            quiz["shared_with"].append(user_id)

        # Update quiz in database
        QuizContainerProxy.replace_item(item=quiz["id"], body=quiz)

        # Send response
        return HttpResponse(
            body=json.dumps(
                {
                    "quiz_id": quiz.get("id"),
                    "quiz_name": quiz.get("name", "Unknown"),
                    "user_id": user_id,
                }
            ),
            status_code=200,
            mimetype="application/json",
        )
    except Exception as e:
        return create_error_response("Something went wrong.", 500)
