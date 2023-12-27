import base64
import json
import logging

from azure.functions import QueueMessage
from utils import get_quizzes_container

# Proxy to CosmosDB
QuizContainerProxy = get_quizzes_container()


def main(msg: QueueMessage) -> None:
    # Decode the message body from base64 and json
    try:
        # decode with base64
        message = json.loads(msg.get_body().decode("utf-8"))
    except Exception as e:
        logging.error("Messaage: %s", msg.get_body())
        logging.error("Error decoding message body: %s", e, exc_info=True)
        return

    # Check message body has quiz_id, user_id and files
    if not all(key in message for key in ("quiz_id", "user_id", "files")):
        logging.error("Message body missing required keys")
        return

    quiz_id = message["quiz_id"]
    user_id = message["user_id"]
    files = message["files"]

    logging.info("Quiz ID: %s", quiz_id)
    logging.info("User ID: %s", user_id)
    logging.info("Files: %s", files)

    # Check files is a list
    if not isinstance(files, list):
        logging.error("Files is not a list")
        return

    # todo:: convert file to text

    # todo:: gpt stuff

    # Get the quiz from the database
    try:
        quiz = QuizContainerProxy.read_item(item=quiz_id, partition_key=quiz_id)
    except Exception as e:
        logging.error("Error getting quiz from database: %s", e, exc_info=True)
        return

    # todo:: change this to use the gpt text
    # Add sample questions to quiz
    quiz["questions"] = [
        {
            "questionID": "1",
            "question": "What is the capital of France?",
            "type": "multi-choice",
            "options": ["Paris", "London", "Berlin", "Madrid"],
        },
        {
            "questionID": "2",
            "question": "What is the capital of Spain?",
            "type": "multi-choice",
            "options": ["Paris", "London", "Berlin", "Madrid"],
        },
        {
            "questionID": "3",
            "question": "What is the capital of Germany?",
            "type": "multi-choice",
            "options": ["Paris", "London", "Berlin", "Madrid"],
        },
    ]

    # Update processed flag
    quiz["processed"] = True

    # Update quiz with new questions
    QuizContainerProxy.replace_item(
        item=message["quiz_id"],
        body=quiz,
    )

    # todo:: notify user
