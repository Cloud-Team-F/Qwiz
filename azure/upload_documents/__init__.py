import asyncio
import base64
import json
import logging
import secrets
from datetime import datetime

import filetype
from azure.functions import HttpRequest, HttpResponse
from azure.storage.blob import ContentSettings
from utils import (
    create_error_response,
    get_async_blob_client,
    get_queue_client,
    get_quizzes_container,
    get_user_container,
)

supported_filetypes = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
]
max_file_size = 30 * 1024 * 1024  # 30MB

# Proxy to CosmosDB
UserContainerProxy = get_user_container()
QuizContainerProxy = get_quizzes_container()
QueueProxy = get_queue_client()


async def upload_blob_async(file: dict) -> dict:
    """Uploads a file to blob storage and returns a dict with the url"""
    try:
        blob_client = get_async_blob_client(filetype=file["extension"])
        await blob_client.upload_blob(
            file["content"],
            blob_type="BlockBlob",
            overwrite=True,
            content_settings=ContentSettings(content_type=file["mime"]),
        )
        file["blob_name"] = blob_client.blob_name
        file["url"] = blob_client.url
        del file["content"]
        return file
    finally:
        await blob_client.close()


async def upload_files_to_blob_storage(files: list) -> list:
    """Uploads files to blob storage and returns a list of urls"""
    tasks = []
    for file in files:
        tasks.append(upload_blob_async(file))
    return await asyncio.gather(*tasks)


def main(req: HttpRequest) -> HttpResponse:
    files = req.files.getlist("files[]")
    file_contents = []

    # Get quiz_name, user_id from from form data
    quiz_name = req.form.get("quiz_name", "").strip()
    user_id = req.form.get("user_id")
    content = req.form.get("content", "").strip()
    topic = req.form.get("topic", "")
    num_questions = req.form.get("num_questions")
    question_types = req.form.get("question_types", [])
    # ["multi-choice", "fill-gaps", "short-answer"]

    # Check missing form data
    if not quiz_name or not user_id:
        logging.error(f"Form data: {req.form}")
        return create_error_response("Missing quiz name or user id", 400)
    if not num_questions or not question_types:
        logging.error(f"Form data: {req.form}")
        return create_error_response("Missing num_questions or question_types", 400)
    if not files and not content:
        return create_error_response("Must upload files or provide text content", 400)
    if len(files) > 3:
        return create_error_response("Max 3 files", 400)
    logging.info(f"Received {len(files)} files")

    # Convert question_types to list
    try:
        logging.info(f"Question types: {question_types}")
        question_types = question_types.split(",")
    except:
        return create_error_response("Invalid question types", 400)

    # Validate
    if len(quiz_name) > 50:
        return create_error_response("Quiz name too long (max 50 characters)", 400)
    if content and not (400 <= len(content) <= 2000):
        return create_error_response("Content must be between 400 and 2000 characters", 400)
    if len(topic) > 100:
        return create_error_response("Topic too long (max 100 characters)", 400)
    if not num_questions.isdigit():
        return create_error_response("Number of questions must be an integer", 400)

    num_questions = int(num_questions)
    if num_questions < 3 or num_questions > 30:
        return create_error_response("Number of questions must be between 3 and 30", 400)
    if not (set(question_types) <= set(["multi-choice", "fill-gaps", "short-answer"])):
        return create_error_response(
            "Invalid question types. Must be one of: 'multi-choice', 'fill-gaps', 'short-answer'",
            400,
        )
    if len(question_types) == 0:
        return create_error_response("Must select at least one question type", 400)

    # Validate if user exists
    try:
        user = UserContainerProxy.read_item(item=user_id, partition_key=user_id)
    except:
        return create_error_response(f"User with id {user_id} not found.", 404)

    if files:
        # Validate each file
        for file in files:
            # Ensure file is not empty and is a supported file type
            if not file:
                return create_error_response("No files uploaded", 400)
            if file.mimetype not in supported_filetypes:
                return create_error_response(f"Unsupported file type: {file.mimetype}", 415)

            # Ensure file binary is correct (magic number check)
            try:
                file_type = filetype.guess(file.read())
            except Exception as e:
                logging.error("Error guessing filetype: ", e)
                return create_error_response("Error guessing filetype", 415)

            if file_type.mime != file.mimetype:
                return create_error_response(
                    f"File '{file.filename}' is not a {file.mimetype} file", 415
                )

            # Ensure file size is not too large
            file.seek(0)
            if len(file.read()) > max_file_size:
                return create_error_response(f"File '{file.filename}' is too large (max 30MB)", 400)

            # Add file to file_contents
            file.seek(0)
            file_contents.append(
                {
                    "filename": file.filename,
                    "content": file.read(),
                    "mime": file_type.mime,
                    "extension": file_type.extension,
                }
            )

        # Store files in blob storage
        asyncio.run(upload_files_to_blob_storage(file_contents))
    else:
        files = []

    # Save document to database
    process_body = {
        "user_id": user_id,
        "shared_with": [],
        "name": quiz_name,
        "topic": topic,
        "num_questions": num_questions,
        "question_types": question_types,
        "files": file_contents,
        "content": content,
        "processed": False,
        "errored": False,
        "invite_code": secrets.token_hex(3),
        "scores": [],
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    try:
        created_quiz = QuizContainerProxy.create_item(
            body=process_body,
            enable_automatic_id_generation=True,
        )
    except Exception as e:
        logging.error("Error saving document to database: ", e)
        return create_error_response("Error saving document to database", 500)

    # Add processing job to queue as json
    QueueProxy.send_message(
        base64.b64encode(
            json.dumps(
                {
                    "quiz_id": created_quiz["id"],
                    "user_id": user_id,
                    "files": file_contents,
                }
            ).encode("utf-8")
        ).decode("utf-8")
    )

    # json response
    return HttpResponse(
        body=json.dumps(
            {
                "id": created_quiz["id"],
                "name": created_quiz["name"],
            }
        ),
        status_code=200,
        mimetype="application/json",
    )
