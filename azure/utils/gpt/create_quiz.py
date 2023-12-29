import logging


def create_quiz(content: str) -> list[dict]:
    """
    Create a quiz from the given content using gpt.

    Args:
        content (str): The text content from which to create the quiz.

    Returns:
        list[dict]: A list of dictionaries representing the quiz questions.
            Each dictionary contains the following keys:
            - 'questionID': The ID of the question.
            - 'question': The question text.
            - 'type': The type of question (e.g., 'multi-choice', 'true-false', etc.).
            - 'options': A list of options for the question (applicable for 'multi-choice' type).
            todo
    """
    logging.info(f"Creating quiz from text: {content}")

    # todo:: gpt stuff

    # Example response (this is what the response should look like)
    return [
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
