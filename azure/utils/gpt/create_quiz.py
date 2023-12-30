import logging


def create_quiz(
    num_questions: int,
    question_types: list[str],
    topic: str = "",
    text_content: str = "",
    file_contents: list[str] = [],
) -> list[dict]:
    """
    Create a quiz from the given content using gpt.

    Args:
        num_questions (int): The number of questions to generate for the quiz.
        question_types (list[str]): A list of question types to include in the quiz. Possible values are: ["multi-choice", "fill-gaps", "short-answer"]
        topic (str, optional): The topic of the quiz. Defaults to "".
        text_content (str, optional): The text content from which to create the quiz. Defaults to "".
        file_contents (list[str], optional): A list of file contents from which to create the quiz. Defaults to [].

    Returns:
        list[dict]: A list of dictionaries representing the quiz questions.
            Each dictionary contains the following keys:
            - 'questionID': The ID of the question.
            - 'question': The question text.
            - 'type': The type of question (e.g., 'multi-choice', 'true-false', etc.).
            - 'options': A list of options for the question (applicable for 'multi-choice' type).
            todo
    """
    logging.info(f"Creating quiz")

    # todo:: gpt stuff

    # Example response (this is what the response should look like)
    return [
        {
            "question_id": "1",
            "question": "What is the capital of France?",
            "type": "multi-choice",
            "options": ["Paris", "London", "Berlin", "Madrid"],
        },
        {
            "question_id": "2",
            "question": "____ is the capital of Spain.",
            "type": "fill-gaps",
        },
        {
            "question_id": "3",
            "question": "What is the capital of Germany?",
            "type": "short-answer",
        },
    ]
