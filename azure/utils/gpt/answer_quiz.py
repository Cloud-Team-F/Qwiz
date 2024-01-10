import json
import logging
import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import OpenAI


def answer_quiz(answer_body: list[dict]) -> list[dict]:
    """Answer a quiz using OpenAI's API.

    Args:
        answer_body (list[dict]): The body of the request.

    Returns:
        list[dict]: The answers to the quiz.
    """
    logging.info("answer_quiz")

    # Grouping the dictionaries by 'type'
    grouped_by_type = {}
    for item in answer_body:
        item_type = item["type"]
        if item_type not in grouped_by_type:
            grouped_by_type[item_type] = []
        grouped_by_type[item_type].append(item)

    # Converting the grouped dictionary to a list of lists
    sublists = list(grouped_by_type.values())

    func = answer_quiz_2
    results = []
    with ThreadPoolExecutor() as executor:
        # Use a future for each sublist
        futures = {executor.submit(func, sublist): sublist for sublist in sublists}

        for future in as_completed(futures):
            # Get the result of the completed future
            result = future.result()
            results.append(result)

    # Debugging:
    # logging.info("Results:")
    # logging.info(results)
    # logging.info("Result items:")
    # for item in results:
    #     logging.info(item)
    #     logging.info(type(item))
    # logging.info("Flattening list:-----------------------")

    results = flatten_list_of_json_strings(results)
    results = sort_by_question_id(results)
    return results


def answer_quiz_2(answer_body: list[dict]) -> list[dict]:
    """Answer a quiz using OpenAI's API.

    Args:
        answer_body (list[dict]): The body of the request.

    Returns:
        list[dict]: The answers to the quiz.
    """
    client = OpenAI()

    question_list = group_by_type(answer_body)
    listOfResponses = []

    # Loop through each question group
    for questionGroup in question_list:
        correctQuestionGroup = ""

        # Check what type of question it is
        if questionGroup[0]["type"] == "fill-gaps":
            questionGroup = update_question_list(questionGroup)
            message = 'You are a quiz answer-checking bot. Do not decide for yourself if you belive the student is correct/incorrect, use the provided JSON and look at is_correct. For each object, you must provide feedback. You should provide the response in JSON, in a list of objects (with fields question_id, is_correct, correct_answer, feedback).\nFor example:\n[{ "correct_answer": "(given in input)", "is_correct": (given in input, but covert to true or false), "question_id": (given in input), "feedback":"Some feedback about the answer"},{"correct_answer": (given in input), "is_correct": (given in input, but convert to true or false), "question_id": (given in input),"feedback":"Some feedback about the answer"},{"correct_answer": "(given in input)","is_correct": (given in input, but convert to true or false),"question_id": (given in input), "feedback":"Some feedback about the answer"}]'
            correctQuestionGroup = alterQuestionGroup(questionGroup, "correct")
            questionGroup = alterQuestionGroup(questionGroup, "incorrect")

            correctQuestionGroup = alterCorrectMultis(correctQuestionGroup)

            # Debugging:
            # logging.info("---correct qs---")
            # logging.info(correctQuestionGroup)
            # logging.info(type(alterCorrectMultis(correctQuestionGroup)))

            correctQuestionGroup = (
                json.dumps(alterCorrectMultis(correctQuestionGroup))[1:-1] + ","
            )  # maybe add a comma

        elif questionGroup[0]["type"] == "multi-choice":
            questionGroup = update_question_list(questionGroup)
            message = 'You are a quiz answer-checking bot. Check the following list of JSON objects. The student has got all the following questions wrong. For each object, you must provide helpful feedback for the student. You should provide the response in JSON, in a list of objects (with fields question_id, is_correct, correct_answer, feedback).\nFor example:\n[{"correct_answer": "(given in input)","is_correct": (given in input, but put true or false),"question_id": (given in input), "feedback":"Some feedback about the answer"},{"correct_answer": (given in input),"is_correct": (given in input, but put true or false),"question_id": (given in input),"feedback":"Some feedback about the answer"},{"correct_answer": "(given in input)","is_correct": (given in input, but put true or false),"question_id": (given in input),"feedback":"Some feedback about the answer"}]'
            correctQuestionGroup = alterQuestionGroup(questionGroup, "correct")
            questionGroup = alterQuestionGroup(questionGroup, "incorrect")

            correctQuestionGroup = alterCorrectMultis(correctQuestionGroup)

            # Debugging:
            # logging.info("---correct qs---")
            # logging.info(correctQuestionGroup)
            # logging.info(type(alterCorrectMultis(correctQuestionGroup)))

            correctQuestionGroup = (
                json.dumps(alterCorrectMultis(correctQuestionGroup))[1:-1] + ","
            )  # maybe add a comma

        elif questionGroup[0]["type"] == "short-answer":
            message = "You are a quiz answer-checking bot tasked with evaluating short-answer questions. Your role is to assess the student's responses and decide whether they are correct. Focus on the understanding demonstrated in each response. If a student's answer shows a good understanding of the topic, it should be marked as correct. However, if a part of the answer is distinctly incorrect or demonstrates a significant misunderstanding, that portion should be marked as incorrect. Be generous yet discerning in your assessment, appreciating the student's grasp of the subject matter while also identifying inaccuracies or misconceptions. Feedback is crucial for answers that are incorrect or show significant misunderstandings. Format your response as a list of comma-separated JSON objects, each representing an individual question's evaluation, with fields for question_id, is_correct, correct_answer, and feedback (only for the parts of answers that are incorrect or demonstrate significant misunderstanding). You may not use the internet to search for the answer."

        response = ""
        if questionGroup != []:
            response = client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[
                    {"role": "system", "content": message},
                    {"role": "user", "content": json.dumps(questionGroup)},
                ],
            )
            response = clean_json_string(response.choices[0].message.content)

            # Debugging:
            # logging.info(response.choices[0].message.content)
            # logging.info("--Incorrect qs--")
            # logging.info(type((response.choices[0].message.content)[1:-1]))
            # logging.info(((response.choices[0].message.content)[1:-1]))

        # Debugging:
        # logging.info(type(correctQuestionGroup))
        logging.info(correctQuestionGroup)

        # Check if there are no correct questions or no incorrect questions
        if correctQuestionGroup == "," and questionGroup == []:
            return []
        elif correctQuestionGroup == ",":
            logging.info("no correct qs")
            combined = (response)[1:-1]
        elif questionGroup == []:
            logging.info("no incorrect qs")
            combined = correctQuestionGroup[:-1]
        else:
            logging.info("both q types exist")
            combined = correctQuestionGroup + ((response)[1:-1])

        listOfResponses.append(combined)

    return listOfResponses


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


def group_by_type(question_list):
    """
    Groups a list of questions by their type.

    Args:
        question_list (list): A list of dictionaries representing questions.

    Returns:
        list: A list of lists, where each inner list contains questions of the same type.
    """
    grouped = defaultdict(list)
    for question in question_list:
        grouped[question["type"]].append(question)

    return list(grouped.values())


def flatten_list_of_json_strings(nested_list):
    """
    Flattens a nested list of JSON strings into a single list of dictionaries.

    Args:
        nested_list (list): A nested list of JSON strings.

    Returns:
        list: A flattened list of dictionaries.
    """
    flattened_list = []

    # Iterating over each sublist
    for sublist in nested_list:
        for json_string in sublist:
            # Splitting the string by '},' to handle multiple JSON objects in a single string
            split_strings = json_string.split("},")
            for index, s in enumerate(split_strings):
                # Adding the missing '}' back except for the last item
                if index != len(split_strings) - 1:
                    s += "}"
                # Converting the string to a dictionary and appending to the list
                logging.info(s)
                dict_item = json.loads(s)
                flattened_list.append(dict_item)

    return flattened_list


def alterQuestionGroup(question_list, correct_status):
    """
    Filters a list of questions based on the 'is_correct' attribute matching the given status.

    Parameters:
    question_list (list): A list of dictionaries representing questions.
    correct_status (str): The desired status of the questions ('True' or 'False').

    Returns:
    list: A filtered list of questions with the specified correct status.
    """
    filtered_list = [
        question
        for question in question_list
        if str(question.get("is_correct")).lower() == correct_status.lower()
    ]
    return filtered_list


def update_question_list(question_list):
    """
    Updates the question list by checking each question's user answer against the local correct answer.
    If the user answer matches the correct answer, the question is marked as "correct".
    Otherwise, it is marked as "incorrect".

    Args:
        question_list (list): A list of dictionaries representing the questions.

    Returns:
        list: The updated question list with the "is_correct" field added/updated to each question.
    """
    for question in question_list:
        if question["user_answer"] == question["correct_answer"]:
            question["is_correct"] = "correct"
        else:
            question["is_correct"] = "incorrect"
    return question_list


def alterCorrectMultis(question_list):
    """
    Modifies the 'is_correct' field of each question in the given list.
    If the 'is_correct' field is 'correct' or True, it is changed to True.
    Otherwise, it is changed to False.

    Args:
        question_list (list): A list of dictionaries representing questions.

    Returns:
        list: A new list of dictionaries with modified 'is_correct' fields.
    """
    altered_list = []
    for question in question_list:
        if question["is_correct"] == "correct" or question["is_correct"] == True:
            myMsg = True
        else:
            myMsg = False
        new_question = {
            "correct_answer": question["correct_answer"],
            "is_correct": myMsg,
            "question_id": question["question_id"],
            "feedback": "",
        }
        altered_list.append(new_question)
    return altered_list


def sort_by_question_id(question_list):
    """
    Sorts a list of questions by 'question_id'.

    Args:
        question_list (list): The list of questions to be sorted.

    Returns:
        list: The sorted list of questions.
    """
    sorted_list = sorted(question_list, key=lambda x: x["question_id"])
    return sorted_list
