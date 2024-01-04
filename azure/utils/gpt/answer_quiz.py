from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import logging
import re
from collections import defaultdict
from openai import OpenAI


def answer_quiz(myLists):

    #convert myLists into appropriate sublists
    #sublists = 
    
    # Grouping the dictionaries by 'type'
    grouped_by_type = {}
    for item in myLists:
        item_type = item['type']
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

    results = flatten_and_sort_list(results)

    return results

def answer_quiz_2(answer_body: list[dict]) -> list[dict]:
    client = OpenAI()
    """Answer a quiz using OpenAI's API.

    Args:
        answer_body (list[dict]): The body of the request.
            Example:

            [{
                "question": "___________ is used for creating interactive and real-time web-based applications.",
                "user_answer": "Python",
                "type": "fill-gaps",
                "question_id": 2
            },
            {
                "question": "What is the benefit of using containers in Google App Engine?",
                "options": [
                    "They allow for easier deployment of applications",
                    "They provide a way to scale traffic and manage instances",
                    "They allow for real-time communication between client and server",
                    "They package up code and its dependencies for quick and reliable execution"
                ],
                "user_answer": "They allow for real-time communication between client and server",
                "type": "multi-choice",
                "question_id": 3
            },
            {
                "question": "How can you install and use libraries and frameworks when using NodeJS?",
                "options": [],
                "user_answer": "yarn or other package managers",
                "type": "short-answer",
                "question_id": 4
            }]

    Returns:
        list[dict]: The answers to the quiz.
    """



    question_list = group_by_type(answer_body)

    listOfResponses = []

    for questionGroup in question_list:

        if questionGroup[0]["type"] == "fill-gaps":

            message =  'You are a quiz answer-checking bot. Do not decide for yourself if you belive the student is correct/incorrect, use the provided JSON and look at is_correct. For each object, you must provide feedback. You should provide the response in JSON, in a list of objects (with fields question_id, is_correct, correct_answer, feedback).\nFor example:\n[{ "correct_answer": "(given in input)", "is_correct": (given in input, but covert to true or false), "question_id": (given in input), "feedback":"Some feedback about the answer"},{"correct_answer": (given in input), "is_correct": (given in input, but convert to true or false), "question_id": (given in input),"feedback":"Some feedback about the answer"},{"correct_answer": "(given in input)","is_correct": (given in input, but convert to true or false),"question_id": (given in input), "feedback":"Some feedback about the answer"}]'

        if questionGroup[0]["type"] == "multi-choice":

             message =  'You are a quiz answer-checking bot. Check the following list of JSON objects to see if the student was correct or incorrect for each question. Do not decide for yourself wether or not you deem the answer correct; you must go by what the input says for that question. For each object, you must provide feedback. You should provide the response in JSON, in a list of objects (with fields question_id, is_correct, correct_answer, feedback).\nFor example:\n[{"correct_answer": "(given in input)","is_correct": (given in input, but put true or false),"question_id": (given in input), "feedback":"Some feedback about the answer"},{"correct_answer": (given in input),"is_correct": (given in input, but put true or false),"question_id": (given in input),"feedback":"Some feedback about the answer"},{"correct_answer": "(given in input)","is_correct": (given in input, but put true or false),"question_id": (given in input),"feedback":"Some feedback about the answer"}]'

        if questionGroup[0]["type"] == "short-answer":    

             message =  'You are a quiz answer-checking bot. For each object in the input, determine if you think the user_answer is correct and you must provide feedback. Be generous in your marking. If you think the student\'s answer is wrong you should fill the "correct answer" field with a model answer of your own creation. If you deem the student\'s answer correct, then you should fill the "correct answer" field with the student\'s answer. You should provide the response in JSON, in a list of objects (with fields question_id, is_correct, correct_answer, feedback).\nFor example:\n[{"correct_answer": "fill as instructed","is_correct": "put true or false","question_id": (given in input),"feedback":"Some feedback about the answer"},{"correct_answer": "fill as instructed","is_correct": "true or false","question_id": (given in input),"feedback":"Some feedback about the answer"},{"correct_answer": "fill as instructed","is_correct": "True or false","question_id": (given in input),"feedback":"Some feedback about the answer"}]'

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": message
                },
                {
                    "role": "user",
                    "content": json.dumps(questionGroup),
                },
            ],
        )

        #clean response (test if it's good/expected)
        #print(response.choices[0].message.content)

        listOfResponses.append((response.choices[0].message.content)[1:-1])


    #logging.info("GPT-3 response: %s", response.choices[0].message.content)
        
    #print("----List of Responses1-----")
    #print(listOfResponses)    

    #combine all 3 lists inside listOfResponses
    #listOfResponses = [s[1:-1] for s in listOfResponses if len(s) > 1]
    listOfResponses = fix_combined_dicts(listOfResponses)


    #print("----List of Response2-----")
    #print(listOfResponses)

    listOfResponses = sorted(listOfResponses, key=lambda x: x['question_id'])

    #data_dicts = [json.loads(s) for s in listOfResponses]

    return listOfResponses

def group_by_type(question_list):
    grouped = defaultdict(list)
    for question in question_list:
        grouped[question['type']].append(question)
    
    return list(grouped.values())

def fix_combined_dicts(lst):
    combined_str = ','.join(lst)  # Combine into a single string
    # Use a regex to properly separate the dictionaries
    separated_strs = re.findall(r'\{.*?}', combined_str)
    # Convert each string back to a dictionary
    return [json.loads(s) for s in separated_strs]

def flatten_and_sort_list(nested_list):
    flattened_list = []
    for sublist in nested_list:
        for item in sublist:
            flattened_list.append(item)
    # Sorting the flattened list by 'question_id'
    sorted_list = sorted(flattened_list, key=lambda x: x['question_id'])
    return sorted_list
