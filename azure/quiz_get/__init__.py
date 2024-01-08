import json
import logging
from datetime import datetime

from azure.cosmos.exceptions import CosmosHttpResponseError
from azure.functions import HttpRequest, HttpResponse
from utils import create_error_response, get_quizzes_container, get_user_container

# Proxy to CosmosDB
UserContainerProxy = get_user_container()
QuizContainerProxy = get_quizzes_container()


def main(req: HttpRequest) -> HttpResponse:
    logging.info("Getting quiz by id")

    # get quiz id from request query
    user_id = req.params.get("user_id")
    quiz_id = req.params.get("quiz_id")

    if not quiz_id:
        return create_error_response("Missing quiz id query.", 400)
    if not user_id:
        return create_error_response("Missing user id query.", 400)

    try:
        # Get quiz from database
        quiz = QuizContainerProxy.read_item(item=quiz_id, partition_key=quiz_id)
    except CosmosHttpResponseError:
        return create_error_response(f"Quiz with id {quiz_id} not found.", 404)

    try:
        # Get user from database
        user = UserContainerProxy.read_item(item=quiz["user_id"], partition_key=quiz["user_id"])
    except CosmosHttpResponseError:
        # Owner not found
        user = "Unknown"

    try:
        # Get users in shared_with from database
        shared_with_users = list(
            UserContainerProxy.query_items(
                query="SELECT c.id, c.username FROM c WHERE ARRAY_CONTAINS(@filter, c.id)",
                parameters=[dict(name="@filter", value=quiz["shared_with"])],
                enable_cross_partition_query=True,
            )
        )
        shared_with_ids = map(lambda x: x["id"], shared_with_users)
        shared_with_usernames = map(lambda x: x.get("username", "Unknown"), shared_with_users)

        # Check if user_id is in shared_with_users id or user_id is owner
        if (user_id not in shared_with_ids) and user_id != quiz["user_id"]:
            return create_error_response("User not authorized to view this quiz.", 403)

        # Get top sorted scores
        seen_user_ids = set()
        sorted_scores = [
            score
            for score in sorted(quiz.get("scores", []), key=lambda s: s["score"], reverse=True)
            if not (score["user_id"] in seen_user_ids or seen_user_ids.add(score["user_id"]))
        ]

        # if len(sorted_scores) > 5:
        #     sorted_scores = sorted_scores[:5]

        # Create a dictionary mapping user IDs to usernames
        usernames = {quiz.get("user_id"): user.get("username", "Unknown")} | {
            sharedUser["id"]: sharedUser.get("username", "Unknown")
            for sharedUser in shared_with_users
        }

        # Get leaderboard with usernames
        leaderboard = [
            {
                "username": usernames.get(score["user_id"], "Unknown"),
                "score": score["score"],
                "date": datetime.strptime(score["date"], "%Y-%m-%dT%H:%M:%S.%f").strftime(
                    "%H:%M %d/%m/%Y"
                ),  # convert date to string
            }
            for score in sorted_scores
        ]

        # http success response
        return HttpResponse(
            body=json.dumps(
                {
                    "quiz_id": quiz_id,
                    "owner_name": user.get("username", "Unknown"),
                    "is_owner": user_id == quiz.get("user_id", ""),
                    "quiz_name": quiz.get("name", "Unknown"),
                    "total_questions": quiz.get("num_questions", 0),
                    "questions": quiz.get("questions", []),
                    "processed": quiz.get("processed", False),
                    "errored": quiz.get("errored", False),
                    "invite_code": quiz.get("invite_code", "Unknown"),
                    "people": list(shared_with_usernames),
                    "top_score": sorted_scores[0]["score"] if sorted_scores else 0,
                    "leaderboard": leaderboard,
                }
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(e)
        return create_error_response("Something went wrong with getting quiz.", 500)
