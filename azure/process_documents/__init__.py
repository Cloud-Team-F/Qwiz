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


def setQuizErrored(quiz_id: str) -> None:
    """
    Set quiz errored field to true

    Args:
        quiz_id (str): quiz id
    """
    try:
        quiz = QuizContainerProxy.read_item(item=quiz_id, partition_key=quiz_id)
        quiz["processed"] = True
        quiz["errored"] = True
        QuizContainerProxy.replace_item(
            item=quiz_id,
            body=quiz,
        )
    except Exception as e:
        logging.error("Error setting quiz errored field: %s", e, exc_info=True)


def sendPubSubMessage(user_id: str, quiz_id: str, message_type: str) -> None:
    """
    Sends a Pub/Sub message to a user for a specific quiz.

    Args:
        user_id (str): The ID of the user to send the message to.
        quiz_id (str): The ID of the quiz associated with the message.
        message_type (str): The type of the message. This can be one of: quiz_processed, quiz_errored.

    Returns:
        None: This function does not return anything.
    """
    try:
        pubsub.send_to_user(
            user_id=user_id,
            message={
                "type": message_type,
                "quiz_id": quiz_id,
            },
        )
    except Exception as e:
        logging.error("Error sending quiz pubsub message: %s", e, exc_info=True)
        return


def main(msg: QueueMessage) -> None:
    logging.info("Python queue trigger function processed a queue item")

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

    logging.info("Quiz ID: %s", quiz_id)

    # Get the quiz from the database
    try:
        quiz = QuizContainerProxy.read_item(item=quiz_id, partition_key=quiz_id)
    except Exception as e:
        logging.error("Error getting quiz from database: %s", e, exc_info=True)
        return

    user_id = quiz["user_id"]
    topic = quiz.get("topic", "")
    num_questions = quiz.get("num_questions", 3)
    question_types = quiz.get("question_types", ["multi-choice"])
    files = quiz.get("files", [])
    text_content = quiz.get("content", "")

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

    try:
        # Create quiz from text
        created_quiz = create_quiz(
            num_questions=num_questions,
            question_types=question_types,
            topic=topic,
            text_content=text_content,
            file_contents=all_content,
        )

        # Add sample questions to quiz
        quiz["questions"] = created_quiz

        # Update processed flag
        quiz["processed"] = True

        # Update quiz with new questions
        QuizContainerProxy.replace_item(
            item=message["quiz_id"],
            body=quiz,
        )

        # Notify the user that the quiz has been processed
        sendPubSubMessage(user_id, quiz_id, "quiz_processed")
    except Exception as e:
        logging.error("Error creating quiz (main func): %s", e, exc_info=True)
        setQuizErrored(quiz_id)

        # Notify the user that the quiz has errored
        sendPubSubMessage(user_id, quiz_id, "quiz_errored")
        return
