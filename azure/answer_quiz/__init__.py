import json
import logging

from azure.cosmos.exceptions import CosmosHttpResponseError
from azure.functions import HttpRequest, HttpResponse
from utils import create_error_response, get_quizzes_container, get_user_container
from utils.gpt import answer_quiz
from datetime import datetime

# Proxy to CosmosDB
UserContainerProxy = get_user_container()
QuizContainerProxy = get_quizzes_container()


def main(req: HttpRequest) -> HttpResponse:
    logging.info("Answering quiz...")

    # Get request body
    try:
        req_body = req.get_json()
    except ValueError:
        return create_error_response("Invalid request body", 400)

    # Check if request body is valid
    if not all(key in req_body for key in ("quiz_id", "answers", "user_id")):
        return create_error_response(
            "Invalid request body. Missing 'quiz_id' or 'answers' or 'user_id'", 400
        )

    quiz_id = req_body["quiz_id"]
    user_id = req_body["user_id"]
    answers = req_body["answers"]

    if not isinstance(answers, dict):
        return create_error_response("'answers' should be a dictionary", 400)

    # Validate answers
    for question_id, answer in answers.items():
        # Strip answer if string
        if isinstance(answer, str):
            answers[question_id] = answer.strip()
        if len(answer) > 200:
            return create_error_response(
                f"Your answer for question {question_id} is too long!", 400
            )

    # Get quiz from database
    try:
        quiz = QuizContainerProxy.read_item(item=quiz_id, partition_key=quiz_id)
        # Make sure quiz is processed and no errors
        if not quiz["processed"] or quiz["errored"]:
            return create_error_response("Quiz is not active", 400)

        # Check number of questions
        if len(quiz["questions"]) != len(answers):
            return create_error_response(
                f"Invalid number of answers. Expected {len(quiz['questions'])} but got {len(req_body['answers'])}",
                400,
            )

        # Check user is owner or in shared_with list
        if user_id != quiz["user_id"] and user_id not in quiz["shared_with"]:
            return create_error_response("User is not allowed to answer this quiz", 403)
    except CosmosHttpResponseError:
        return create_error_response("Quiz not found", 404)

    # Join the answers with the questions
    answer_body = []
    for question in quiz["questions"]:
        question_id_str = str(question["question_id"])
        question_type = question.get("type", "any")
        if question_id_str not in answers:
            return create_error_response(
                f"Missing answer for question {question['question_id']}", 400
            )

        answer_body.append(
            {
                "question_id": question["question_id"],
                "question": question["question"],
                "user_answer": answers[question_id_str],
                "type": question_type,
                "correct_answer": question.get("correct_answer", ""),
            }
            | (
                {"options": question.get("options", [])}
                if "options" in question and question_type == "multi-choice"
                else {}
            )
        )

    logging.info(answer_body)

    # Answer quiz using GPT
    try:
        correct_answers = answer_quiz(answer_body)

        current_scores = quiz.get("scores", [])

        total_score = sum([1 for answer in correct_answers if answer["is_correct"]])

        # Check if top_score
        is_top_score = False
        if current_scores:
            top_score = max([score["score"] for score in current_scores])
            if total_score > top_score:
                is_top_score = True
        else:
            is_top_score = True

        # Add user score to quiz
        score_obj = {
            "user_id": user_id,
            "score": total_score,
            "date": datetime.now().isoformat(),
        }

        if current_scores:
            quiz["scores"].append(score_obj)
        else:
            quiz["scores"] = [score_obj]

        # Update quiz in database
        QuizContainerProxy.replace_item(item=quiz_id, body=quiz)

        return HttpResponse(
            json.dumps(
                {
                    "answers": correct_answers,
                    "score": score_obj["score"],
                    "is_top_score": is_top_score,
                }
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(e)
        return create_error_response("Error answering quiz", 500)
