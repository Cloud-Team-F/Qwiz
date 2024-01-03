import json
import logging

from azure.cosmos.exceptions import CosmosHttpResponseError
from azure.functions import HttpRequest, HttpResponse
from utils import create_error_response, get_quizzes_container, get_user_container

# Proxy to CosmosDB
UserContainerProxy = get_user_container()
QuizContainerProxy = get_quizzes_container()


def main(req: HttpRequest) -> HttpResponse:
    logging.info("Getting all quizzes by user")

    # get user id from request query
    user_id = req.params.get("id")

    if not user_id:
        return create_error_response("Missing user id query.", 400)

    try:
        # Get user from database
        user = UserContainerProxy.read_item(item=user_id, partition_key=user_id)
    except Exception as e:
        return create_error_response(f"User with id {user_id} not found.", 404)

    try:
        # Get quizzes from database
        own_quizzes = QuizContainerProxy.query_items(
            query="SELECT c.id, c.name, c.num_questions as question_count, c.processed, c.errored, c.created_at, TimestampToDateTime(c._ts*1000) AS last_modified FROM c WHERE c.user_id = @filter",
            parameters=[dict(name="@filter", value=user_id)],
            enable_cross_partition_query=True,
        )

        shared_quizzes = QuizContainerProxy.query_items(
            query="SELECT c.id, c.name, c.num_questions as question_count, c.processed, c.errored, c.created_at, TimestampToDateTime(c._ts*1000) AS last_modified FROM c WHERE ARRAY_CONTAINS(c.shared_with, @filter)",
            parameters=[dict(name="@filter", value=user_id)],
            enable_cross_partition_query=True,
        )

        return HttpResponse(
            body=json.dumps(
                {
                    "own_quizzes": list(own_quizzes),
                    "shared_quizzes": list(shared_quizzes),
                }
            ),
            status_code=200,
            mimetype="application/json",
        )
    except CosmosHttpResponseError:
        return create_error_response("Something went wrong with getting quizzes.", 500)
