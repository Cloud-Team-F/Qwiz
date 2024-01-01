import json
import logging

from openai import OpenAI

client = OpenAI()


def answer_quiz(answer_body: list[dict]) -> list[dict]:
    """Answer a quiz using OpenAI's API.

    Args:
        answer_body (list[dict]): The body of the request.
            Example:

    Returns:
        list[dict]: The answers to the quiz.
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": 'You are a quiz answer-checking bot. You provide short and concise feedback when the user is wrong, consisting of why their answer is wrong, and what it should instead of. Explain why. You should mark the user as correct if they are very close to the actual answer. The input will contain a JSON, with a list of question objects (with fields question_id, question, options, user_answer and type). You should provide the response in JSON, in a list of objects (with fields question_id, is_correct, correct_answer, feedback).\nFor example:\n[\n{\n    "correct_answer": "JavaScript",\n    "is_correct": true,\n    "question_id": 1\n},\n{\n    "correct_answer": "They package up code and its dependencies for quick and reliable execution",\n    "is_correct": false,\n    "question_id": 2\n},\n{\n    "correct_answer": "npm",\n    "is_correct": true,\n    "question_id": 3\n},\n]',
            },
            {
                "role": "user",
                "content": json.dumps(answer_body),
            },
        ],
    )

    logging.info("GPT-3 response: %s", response.choices[0].message.content)

    return json.loads(response.choices[0].message.content)
