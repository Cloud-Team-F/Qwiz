import logging
import random
import re
import json

from openai import OpenAI


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
    logging.info(f"Creating quiz")

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
        if "multi-choice" in questionTypesCount:
            completionMulti = messageMultiChoice(
                questionTypesCount["multi-choice"], text_content
            )

            print("completion Multi 1")
            print(completionMulti)

            completionMulti = completionMulti.choices[0].message.content

            print("completion Multi 2")
            print(completionMulti)

            completionMulti = clean_json_string(completionMulti)

            print("completion Multi 3")
            print(completionMulti)

            quizMulti = parse_multi_quiz(completionMulti)

            print("completion Multi 4")
            print(quizMulti)

            quizQuestions.append(quizMulti)

            logging.info(f"Creating quiz - completionMulti: {completionMulti}")

        # Fill in the blanks questions
        if "fill-gaps" in questionTypesCount:
            completionBlanks = messageFillBlanks(questionTypesCount["fill-gaps"], text_content)
            quizFill = parse_fill_blanks(completionBlanks.choices[0].message.content)

            questions2fingers = []
            for question in quizFill.questions:

                newQuestion = messageFillBlanks2(question["question"])

                newQuestion = newQuestion.choices[0].message.content

                newQuestion = clean_json_string(newQuestion)

                newQuestion = parse_fill_blanks2(newQuestion, question["question"])  # returns a question

                questions2fingers.append(newQuestion[0])

            newQuiz2 = Quiz(questions2fingers)    

            #quizFill = Quiz(questions2fingers)
            quizQuestions.append(newQuiz2)

            logging.info(f"Creating quiz - completionBlanks: {completionBlanks}")

        # Short answer questions
        if "short-answer" in questionTypesCount:
            completionShort = messageShortAnswer(
                questionTypesCount["short-answer"], text_content
            )

            completionShort = completionShort.choices[0].message.content
            completionShort = clean_json_string(completionShort)

            quizShort = parse_short_quiz(completionShort)
            quizQuestions.append(quizShort)

            logging.info(f"Creating quiz - completionShort: {completionShort}")


        # Combine the quizzes into one
        finalQuiz = combine_quizzes(quizQuestions)

        # Randomize the order of the quiz questions
        random.shuffle(finalQuiz.questions)

        # Add Ids to the questions
        finalQuiz = add_sequential_quiz_id(finalQuiz.questions)
        logging.info(f"Creating quiz - finalQuiz: {finalQuiz}")

        # Return the final quiz list[dict]
        logging.info(f"Creating quiz - finalQuiz: {finalQuiz}")
        return finalQuiz

    except Exception as e:
        logging.error("Error creating quiz: %s", e, exc_info=True)
        raise e


"""
------------------------How to setup the APIkey.------------------------
    Either make a .env file and paste the line below into it. 
    OPENAI_API_KEY=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

------------------------------OR------------------------------

    set the key up permanently by changing your env variables:
    1) Open Command Prompt:

    2) type this command: setx OPENAI_API_KEY "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"
    This command will set the OPENAI_API_KEY environment variable for the current session.

    Permanent setup: To make the setup permanent, add the variable through the system properties as follows:

    Right-click on 'This PC' or 'My Computer' and select 'Properties'.
    Click on 'Advanced system settings'.
    Click the 'Environment Variables' button.
    In the 'System variables' section, click 'New...' and enter OPENAI_API_KEY as the variable name and your API key as the variable value.
    Verification: To verify the setup, reopen the command prompt and type the command below. It should display your API key: echo %OPENAI_API_KEY%
"""


class Question:
    def __init__(self, question, options, correct_answer, type, question_id):
        self.question = question
        self.options = options
        self.correct_answer = correct_answer
        self.type = type
        self.question_id = question_id


class Quiz:
    def __init__(self, questions):
        self.questions = questions


class Submission:
    def __init__(self, mark, feedback):
        self.mark = mark  # either correct or incorrect
        self.feedback = feedback

def insertBlankOnPhraseUsed(phraseUsed, phrase):
    # Calculate the number of underscores needed
    underscores = '_' * len(phrase)

    # Define the regular expression pattern for a whole word match, with word boundaries
    pattern = r'\b' + re.escape(phrase) + r'\b'

    # Replace the first instance of the phrase with underscores, case-insensitive
    return re.sub(pattern, underscores, phraseUsed, count=1, flags=re.IGNORECASE)



def clean_json_string(json_string):
    # Check if the string starts with '''json and ends with '''
    if json_string.startswith("```json"):
        # Remove '''json from the start and ''' from the end
        return json_string[7:-3].strip()
    else:
        # If the string does not have these patterns, return it as is
        return json_string

def add_sequential_quiz_id(quiz):
    for i, question in enumerate(quiz):
        question["question_id"] = i + 1  
    return quiz


def combine_quizzes(quizzes):
    combined_questions = []
    for quiz in quizzes:
        combined_questions.extend(quiz.questions)
    return Quiz(combined_questions)


def generateTypesCount(num_questions, question_types):
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
    # Assuming each JSON object is separated by newlines
    json_objects = json_string.split('\n')

    python_dicts = []
    for obj in json_objects:
        try:
            python_dict = json.loads(obj)
            python_dict["type"] = "multi-choice"  # Add the 'type' attribute
            python_dict["question_id"] = 0  # Add the 'question_id' attribute
            python_dicts.append(python_dict)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON pmq: {e}")
            # Handle the error or ignore the faulty JSON object

    return Quiz(python_dicts)


def parse_short_quiz(json_string):  
    # Assuming each JSON object is separated by newlines
    json_objects = json_string.split('\n')

    python_dicts = []
    for obj in json_objects:
        try:
            python_dict = json.loads(obj)
            python_dict["options"] = []  # Add the 'options' attribute
            python_dict["correct_answer"] = ''  # Add the 'correct answer' attribute
            python_dict["type"] = "short-answer"  # Add the 'type' attribute
            python_dict["question_id"] = 0  # Add the 'question_id' attribute
            python_dicts.append(python_dict)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON psq: {e}")
            # Handle the error or ignore the faulty JSON object

    return Quiz(python_dicts)


def parse_fill_blanks(json_string):
    # Assuming each JSON object is separated by newlines
    json_objects = json_string.split('\n')

    python_dicts = []
    for obj in json_objects:
        try:
            python_dict = json.loads(obj)
            python_dict["question"] = python_dict["fact"] #these 2 lines rename the dictionary to question from fact. the reason it is "fact" in the first place is to encourage better gpt responces
            del python_dict["fact"]
            python_dict["options"] = []  # Add the 'options' attribute
            python_dict["correct_answer"] = ''  # Add the 'correct answer' attribute
            python_dict["type"] = "fill-gaps"  # Add the 'type' attribute
            python_dict["question_id"] = 0  # Add the 'question_id' attribute
            python_dicts.append(python_dict)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON pfb: {e}")
            # Handle the error or ignore the faulty JSON object

    return Quiz(python_dicts)


def parse_fill_blanks2(quiz_text, phraseUsed):

    python_dicts = []
    try:
        python_dict = json.loads(quiz_text)
        phraseUsed = insertBlankOnPhraseUsed(phraseUsed,python_dict["correct_answer"])
        python_dict["question"] = phraseUsed
        python_dict["type"] = "fill-gaps"  # Add the 'type' attribute
        python_dict["question_id"] = 0  # Add the 'question_id' attribute
        python_dicts.append(python_dict)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in pfb2: {e}")
        # Handle the error or ignore the faulty JSON object


    return python_dicts


def messageMultiChoice(count, text):  # asks chatGPT to make a multichoce quiz of length "count" based off of the "text"
    client = OpenAI()
    myMessageSystem = (
        "Generate a "
        + str(count)
        + "-question long multiple-choice quiz based on the provided text. Make it so each question has 4 possible options. Format each question as a JSON object like so {\"question\":\"\",\"options\":[\"option1\",\"option2\",\"option3\",\"option4\"],\"correct_answer\":\"the correct answer\"}. Each JSON object should be separated by only a newLine."
    )
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": myMessageSystem},
            {"role": "user", "content": text},
        ],
    )
    

    return completion


def messageShortAnswer(count, text):  # asks chatGPT to make a short answer quiz of length "count" based off of the "text"
    client = OpenAI()
    myMessageSystem = (
        "Generate a "
        + str(count)
        + "-question short answer quiz based on the provided text. Format each question as a JSON object like so {\"question\":\"\"}"
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
    client = OpenAI()
    myMessageSystem = (
        "Give me exactly "
        + str(count)
        + " facts about the topic below. Format each fact as a JSON object like so {\"fact\":\"\"}. Do not use the ``` symbol to format your answer. Each JSON should be separated only by a newLine"
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
    client = OpenAI()
    # myMessageSystem = ""
    completion = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {
                "role": "system",
                "content": "Using the following fact, create a list of four words suitable for a fill-in-the-blank question. One of the 4 words you pick must come directly from the fact. Format your answer as a single JSON object like this: {\"options\":[\"option1\",\"option2\",\"option3\",\"option4\"],\"correct_answer\":\"the correct answer\"}",
            },
            {"role": "user", "content": "The fact: " + text},
        ],
    )

    return completion
