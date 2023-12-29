import base64
import json
import logging

from azure.functions import QueueMessage
from utils import get_blob_client, get_pubsub_client, get_quizzes_container
from utils.files import convert_to_text
from utils.gpt import create_quiz

# Proxy to CosmosDB
QuizContainerProxy = get_quizzes_container()

# PubSub client
pubsub = get_pubsub_client()


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

    # convert file to text
    all_content = []
    for file in files:
        try:
            content = convert_to_text(file["url"], file["mime"])
            all_content.append(content)
        except Exception as e:
            logging.error("Error converting file to text: %s", e, exc_info=True)
            return

    # Remove files from blob
    for file in files:
        try:
            blob_client = get_blob_client(blob_name=file["blob_name"])
            blob_client.delete_blob(delete_snapshots="include")
        except Exception as e:
            logging.error("Error deleting blob: %s", e, exc_info=True)

    # Create quiz from text
    created_quiz = create_quiz(content="\n".join(all_content))

    # Get the quiz from the database
    try:
        quiz = QuizContainerProxy.read_item(item=quiz_id, partition_key=quiz_id)
    except Exception as e:
        logging.error("Error getting quiz from database: %s", e, exc_info=True)
        return

    # Add sample questions to quiz
    quiz["questions"] = created_quiz

    # Update processed flag
    quiz["processed"] = True

    # Update quiz with new questions
    QuizContainerProxy.replace_item(
        item=message["quiz_id"],
        body=quiz,
    )

    # Notify user that quiz has been processed
    pubsub.send_to_user(
        user_id=user_id,
        message={
            "type": "quiz_processed",
            "quiz_id": quiz_id,
        },
    )
