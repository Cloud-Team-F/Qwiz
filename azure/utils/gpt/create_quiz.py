import json
import logging
import random
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import OpenAI


class Quiz:
    def __init__(self, questions):
        self.questions = questions


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
            - 'question_id': The ID of the question.
            - 'question': The question text.
            - 'type': The type of question (e.g., 'multi-choice', 'true-false', etc.).
            - 'options': A list of options for the question (applicable for 'multi-choice' type).
    """
    logging.info("create_quiz")

    # Create a list of sublists of question types
    questionTypesCount = generateTypesCount(num_questions, question_types)
    func = create_quiz_2
    results = []

    with ThreadPoolExecutor() as executor:
        # Use a future for each sublist
        futures = {
            executor.submit(func, key, value, question_types, topic, text_content, file_contents): (
                key,
                value,
            )
            for key, value in questionTypesCount.items()
        }

        for future in as_completed(futures):
            # Get the result of the completed future
            result = future.result()
            results.append(result)

    # Combine the results into one list
    results = [question for quiz in results for question in quiz.questions]
    logging.info(f"Creating quiz - results: {results}")

    # Randomize the order of the quiz questions
    random.shuffle(results)

    # Add Ids to the questions
    results = add_sequential_quiz_id(results)

    results = filter_questions(results,num_questions)
    return results


def create_quiz_2(
    key: str,
    num_questions: int,
    question_types: list[str],
    topic: str = "",
    text_content: str = "",
    file_contents: list[str] = [],
) -> list[dict]:
    """
    Create a quiz based on the specified parameters.

    Args:
        key (str): The type of quiz to create. Valid options are "multi-choice", "fill-gaps", and "short-answer".
        num_questions (int): The number of questions to include in the quiz.
        question_types (list[str]): A list of question types to include in the quiz. Valid options are "multi-choice", "fill-gaps", and "short-answer".
        topic (str, optional): The topic of the quiz. Defaults to an empty string.
        text_content (str, optional): The text content to include in the quiz. Defaults to an empty string.
        file_contents (list[str], optional): A list of file contents to include in the quiz. Defaults to an empty list.

    Returns:
        list[dict]: A list of dictionaries representing the quiz questions.

    Raises:
        Exception: If an error occurs while creating the quiz.
    """
    logging.info("Creating quiz - helper function")

    try:
        # List of quiz questions
        quizQuestions = []

        # Generate the question type counts (e.g., {"multi-choice": 2, "fill-gaps": 2, "short-answer": 1})
        questionTypesCount = generateTypesCount(num_questions, question_types)
        logging.info(f"Creating quiz - typesCount: {questionTypesCount}")

        # Combine the text content and file contents
        for content in file_contents:
            text_content = text_content + content

        # Create the quiz for each question type
        # Multiple-choice questions
        if key == "multi-choice":
            completionMulti = messageMultiChoice(num_questions, text_content)
            # logging.info("completion Multi 1")
            # logging.info(completionMulti)

            completionMulti = completionMulti.choices[0].message.content
            # logging.info("completion Multi 2")
            # logging.info(completionMulti)

            completionMulti = clean_json_string(completionMulti)
            # logging.info("completion Multi 3")
            # logging.info(completionMulti)

            quizMulti = parse_multi_quiz(completionMulti)
            # logging.info("completion Multi 4")
            # logging.info(quizMulti)

            quizQuestions.append(quizMulti)
            logging.info(f"Creating quiz - completionMulti: {completionMulti}")

        # Fill in the blanks questions
        if key == "fill-gaps":
            completionBlanks = messageFillBlanks(num_questions, text_content)
            quizFill = parse_fill_blanks(completionBlanks.choices[0].message.content)

            # Loop through the questions and create a new question for each
            questions2fingers = []
            for question in quizFill.questions:
                newQuestion = messageFillBlanks2(question["question"])
                newQuestion = newQuestion.choices[0].message.content
                newQuestion = clean_json_string(newQuestion)
                newQuestion = parse_fill_blanks2(
                    newQuestion, question["question"]
                )  # returns a question

                questions2fingers.append(newQuestion[0])

            newQuiz2 = Quiz(questions2fingers)
            quizQuestions.append(newQuiz2)

            logging.info(f"Creating quiz - completionBlanks: {completionBlanks}")

        # Short answer questions
        if key == "short-answer":
            completionShort = messageShortAnswer(num_questions, text_content)

            completionShort = completionShort.choices[0].message.content
            completionShort = clean_json_string(completionShort)

            quizShort = parse_short_quiz(completionShort)
            quizQuestions.append(quizShort)

            logging.info(f"Creating quiz - completionShort: {completionShort}")

        # Combine the quizzes into one
        finalQuiz = combine_quizzes(quizQuestions)

        # Return the final quiz list[dict]
        logging.info(f"Creating quiz - finalQuiz: {finalQuiz}")
        return finalQuiz

    except Exception as e:
        logging.error("Error creating quiz: %s", e, exc_info=True)
        raise e

def filter_questions(questions, max_id):
    """
    Removes entries from the list where the question_id is greater than max_id.

    :param questions: List of dictionaries containing question details.
    :param max_id: The maximum allowed question_id.
    :return: Filtered list of dictionaries.
    """
    return [question for question in questions if question.get('question_id', 0) <= max_id]

def insertBlankOnPhraseUsed(phraseUsed, phrase):
    """
    Replaces the first instance of a given phrase with underscores in a given string.

    Args:
        phraseUsed (str): The string in which the replacement will be made.
        phrase (str): The phrase to be replaced.

    Returns:
        str: The modified string with the first instance of the phrase replaced by underscores.
    """
    # Calculate the number of underscores needed
    underscores = "_" * len(phrase)

    # Replace the first instance of the phrase with underscores, case-insensitive
    return re.sub(re.escape(phrase), underscores, phraseUsed, count=1, flags=re.IGNORECASE)


def clean_json_string(json_string):
    """
    Cleans a JSON string by removing the surrounding triple backticks and 'json' tag.

    Args:
        json_string (str): The JSON string to be cleaned.

    Returns:
        str: The cleaned JSON string.
    """
    # Check if the string starts with '''json and ends with '''
    if json_string.startswith("```json"):
        # Remove '''json from the start and ''' from the end
        return json_string[7:-3].strip()
    else:
        # If the string does not have these patterns, return it as is
        return json_string


def add_sequential_quiz_id(quiz):
    """
    Adds a sequential question ID to each question in the quiz.

    Args:
        quiz (list): The list of questions in the quiz.

    Returns:
        list: The updated quiz with question IDs.
    """
    for i, question in enumerate(quiz):
        question["question_id"] = i + 1
    return quiz


def combine_quizzes(quizzes):
    """
    Combines a list of quizzes into a single quiz.

    Args:
        quizzes (list): A list of Quiz objects.

    Returns:
        Quiz: A new Quiz object containing all the questions from the input quizzes.
    """
    combined_questions = []
    for quiz in quizzes:
        combined_questions.extend(quiz.questions)
    return Quiz(combined_questions)


def generateTypesCount(num_questions, question_types):
    """
    Generate a dictionary with the count of each question type.

    Args:
        num_questions (int): The total number of questions.
        question_types (list): A list of question types.

    Returns:
        dict: A dictionary with the count of each question type.
    """
    # Calculate the base count for each question type
    base_count = num_questions // len(question_types)

    # Calculate the remainder to distribute
    remainder = num_questions % len(question_types)

    # Initialize the result dictionary with base count for each question type
    result = {question_type: base_count for question_type in question_types}

    # Distribute the remainder among the question types
    for i in range(remainder):
        result[question_types[i]] += 1

    return result


def parse_multi_quiz(json_string):
    """
    Parses a multi-choice quiz from a JSON string.

    Args:
        json_string (str): The JSON string containing the quiz data.

    Returns:
        Quiz: The parsed Quiz object.
    """
    # Assuming each JSON object is separated by newlines
    json_objects = json_string.split("\n")

    python_dicts = []
    for obj in json_objects:
        try:
            python_dict = json.loads(obj)
            python_dict["type"] = "multi-choice"  # Add the 'type' attribute
            python_dict["question_id"] = 0  # Add the 'question_id' attribute
            python_dicts.append(python_dict)
        except json.JSONDecodeError as e:
            logging.info(f"Error decoding JSON pmq: {e}")
            # Handle the error or ignore the faulty JSON object

    return Quiz(python_dicts)


def parse_short_quiz(json_string):
    """
    Parses a JSON string containing short quiz questions and returns a Quiz object.

    Args:
        json_string (str): The JSON string containing the quiz questions.

    Returns:
        Quiz: A Quiz object containing the parsed quiz questions.
    """
    # Assuming each JSON object is separated by newlines
    json_objects = json_string.split("\n")

    python_dicts = []
    for obj in json_objects:
        try:
            python_dict = json.loads(obj)
            python_dict["options"] = []  # Add the 'options' attribute
            python_dict["correct_answer"] = ""  # Add the 'correct answer' attribute
            python_dict["type"] = "short-answer"  # Add the 'type' attribute
            python_dict["question_id"] = 0  # Add the 'question_id' attribute
            python_dicts.append(python_dict)
        except json.JSONDecodeError as e:
            logging.info(f"Error decoding JSON psq: {e}")
            # Handle the error or ignore the faulty JSON object

    return Quiz(python_dicts)


def parse_fill_blanks(json_string):
    """
    Parses a JSON string containing fill-in-the-blanks quiz questions and returns a Quiz object.

    Args:
        json_string (str): The JSON string containing the quiz questions.

    Returns:
        Quiz: A Quiz object containing the parsed quiz questions.
    """
    # Assuming each JSON object is separated by newlines
    json_objects = json_string.split("\n")

    python_dicts = []
    for obj in json_objects:
        try:
            python_dict = json.loads(obj)
            python_dict["question"] = python_dict[
                "fact"
            ]  # these 2 lines rename the dictionary to question from fact. the reason it is "fact" in the first place is to encourage better gpt responces
            del python_dict["fact"]
            python_dict["options"] = []  # Add the 'options' attribute
            python_dict["correct_answer"] = ""  # Add the 'correct answer' attribute
            python_dict["type"] = "fill-gaps"  # Add the 'type' attribute
            python_dict["question_id"] = 0  # Add the 'question_id' attribute
            python_dicts.append(python_dict)
        except json.JSONDecodeError as e:
            logging.info(f"Error decoding JSON pfb: {e}")
            # Handle the error or ignore the faulty JSON object

    return Quiz(python_dicts)


def parse_fill_blanks2(quiz_text, phraseUsed):
    """
    Parses the quiz text and creates a list of dictionaries representing fill-gaps questions.

    Args:
        quiz_text (str): The quiz text in JSON format.
        phraseUsed (str): The phrase used in the question.

    Returns:
        list: A list of dictionaries representing fill-gaps questions.
    """
    python_dicts = []
    try:
        python_dict = json.loads(quiz_text)
        phraseUsed = insertBlankOnPhraseUsed(phraseUsed, python_dict["correct_answer"])
        python_dict["question"] = phraseUsed
        python_dict["type"] = "fill-gaps"  # Add the 'type' attribute
        python_dict["question_id"] = 0  # Add the 'question_id' attribute
        python_dicts.append(python_dict)
    except json.JSONDecodeError as e:
        logging.info(f"Error decoding JSON in pfb2: {e}")
        # Handle the error or ignore the faulty JSON object

    return python_dicts


def messageMultiChoice(count, text):
    """
    Asks chatGPT to make a multiple-choice quiz based on the provided text.

    Args:
        count (int): The length of the quiz, i.e., the number of questions.
        text (str): The text to base the quiz questions on.

    Returns:
        completion: The completion object returned by the OpenAI API.
    """
    client = OpenAI()
    myMessageSystem = (
        "Generate a "
        + str(count)
        + '-question long multiple-choice quiz based on the provided text. Make it so each question has 4 possible options. Format each question as a JSON object like so {"question":"","options":["option1","option2","option3","option4"],"correct_answer":"the correct answer"}. Each JSON object should be separated by only a newLine.'
    )
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": myMessageSystem},
            {"role": "user", "content": text},
        ],
    )

    return completion


def messageShortAnswer(count, text):
    """
    Asks chatGPT to make a short answer quiz of length "count" based on the provided "text".

    Args:
        count (int): The number of questions to generate for the quiz.
        text (str): The text used as the basis for generating the quiz.

    Returns:
        completion: The completion object returned by the OpenAI API.
    """
    client = OpenAI()
    myMessageSystem = (
        "Generate a "
        + str(count)
        + '-question short answer quiz based on the provided text. Format each question as a JSON object like so {"question":""}'
    )

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": myMessageSystem},
            {"role": "user", "content": text},
        ],
    )

    return completion


def messageFillBlanks(count, text):
    """
    Sends a message to the OpenAI chat API to fill in the blanks in a given text.

    Args:
        count (int): The number of facts to be filled in.
        text (str): The text containing the blanks to be filled.

    Returns:
        completion (object): The completion object returned by the OpenAI chat API.
    """
    client = OpenAI()
    myMessageSystem = (
        "Give me exactly "
        + str(count)
        + ' facts about the topic below. Format each fact as a JSON object like so {"fact":""}. Do not use the ``` symbol to format your answer. Each JSON should be separated only by a newLine'
    )

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": myMessageSystem},
            {"role": "user", "content": text},
        ],
    )

    return completion


def messageFillBlanks2(text):
    """
    Generates a fill-in-the-blanks question based on the given text.

    Args:
        text (str): The fact to be used in the question.

    Returns:
        completion: The completion object generated by the OpenAI chat API.
    """
    client = OpenAI()
    completion = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {
                "role": "system",
                "content": 'Using the following fact, create a list of four words suitable for a fill-in-the-blank question. One of the 4 words you pick must come directly from the fact. Format your answer as a single JSON object like this: {"options":["option1","option2","option3","option4"],"correct_answer":"the correct answer"}',
            },
            {"role": "user", "content": "The fact: " + text},
        ],
    )

    return completion
