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

    print("results")
    print(results)

    print("Thingys:")
    for thingy in results:
        print(thingy)   
        print(type(thingy))     

    print("flatting:-----------------------")
    results = flatten_list_of_json_strings(results)

    results = sort_by_question_id(results)

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

        correctQuestionGroup = ''

        if questionGroup[0]["type"] == "fill-gaps":
            
            questionGroup = update_question_list(questionGroup)
            message =  'You are a quiz answer-checking bot. Do not decide for yourself if you belive the student is correct/incorrect, use the provided JSON and look at is_correct. For each object, you must provide feedback. You should provide the response in JSON, in a list of objects (with fields question_id, is_correct, correct_answer, feedback).\nFor example:\n[{ "correct_answer": "(given in input)", "is_correct": (given in input, but covert to true or false), "question_id": (given in input), "feedback":"Some feedback about the answer"},{"correct_answer": (given in input), "is_correct": (given in input, but convert to true or false), "question_id": (given in input),"feedback":"Some feedback about the answer"},{"correct_answer": "(given in input)","is_correct": (given in input, but convert to true or false),"question_id": (given in input), "feedback":"Some feedback about the answer"}]'
            correctQuestionGroup = alterQuestionGroup(questionGroup,"correct")
            questionGroup = alterQuestionGroup(questionGroup,"incorrect")

            correctQuestionGroup = (alterCorrectMultis(correctQuestionGroup))

            print("---correct qs---")
            print(correctQuestionGroup)

            print(type(alterCorrectMultis(correctQuestionGroup)))

            correctQuestionGroup = json.dumps(alterCorrectMultis(correctQuestionGroup))[1:-1] + "," #maybe add a comma

        if questionGroup[0]["type"] == "multi-choice":

            questionGroup = update_question_list(questionGroup)
            message =  'You are a quiz answer-checking bot. Check the following list of JSON objects. The student has got all the following questions wrong. For each object, you must provide helpful feedback for the student. You should provide the response in JSON, in a list of objects (with fields question_id, is_correct, correct_answer, feedback).\nFor example:\n[{"correct_answer": "(given in input)","is_correct": (given in input, but put true or false),"question_id": (given in input), "feedback":"Some feedback about the answer"},{"correct_answer": (given in input),"is_correct": (given in input, but put true or false),"question_id": (given in input),"feedback":"Some feedback about the answer"},{"correct_answer": "(given in input)","is_correct": (given in input, but put true or false),"question_id": (given in input),"feedback":"Some feedback about the answer"}]'
            correctQuestionGroup = alterQuestionGroup(questionGroup,"correct")
            questionGroup = alterQuestionGroup(questionGroup,"incorrect")


            correctQuestionGroup = (alterCorrectMultis(correctQuestionGroup))

            print("---correct qs---")
            print(correctQuestionGroup)

            print(type(alterCorrectMultis(correctQuestionGroup)))

            correctQuestionGroup = json.dumps(alterCorrectMultis(correctQuestionGroup))[1:-1] + "," #maybe add a comma

            #listOfResponses.append(json.dumps(alterCorrectMultis(correctQuestionGroup))[1:-1])
            #print("---List of responses---")
            #print(listOfResponses)

        if questionGroup[0]["type"] == "short-answer":    

           
           message = "You are a quiz answer-checking bot tasked with evaluating short-answer questions. Your role is to assess the student's responses and decide whether they are correct. Focus on the understanding demonstrated in each response. If a student's answer shows a good understanding of the topic, it should be marked as correct. However, if a part of the answer is distinctly incorrect or demonstrates a significant misunderstanding, that portion should be marked as incorrect. Be generous yet discerning in your assessment, appreciating the student's grasp of the subject matter while also identifying inaccuracies or misconceptions. Feedback is crucial for answers that are incorrect or show significant misunderstandings. Format your response as a list of comma-separated JSON objects, each representing an individual question's evaluation, with fields for question_id, is_correct, correct_answer, and feedback (only for the parts of answers that are incorrect or demonstrate significant misunderstanding)."
             

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

        print("--Incorrect qs--")
        print(type((response.choices[0].message.content)[1:-1]))
        print(((response.choices[0].message.content)[1:-1]))

        print(type(correctQuestionGroup))
        print(correctQuestionGroup)

        combined = correctQuestionGroup + ((response.choices[0].message.content)[1:-1])

        #listOfResponses.append((response.choices[0].message.content)[1:-1])
        listOfResponses.append(combined)


    #logging.info("GPT-3 response: %s", response.choices[0].message.content)
        
    #print("----List of Responses1-----")
    #print(listOfResponses)    

    #combine all 3 lists inside listOfResponses

    #listOfResponses = fix_combined_dicts(listOfResponses)


    #print("----List of Response2-----")
    #print(listOfResponses)

    #listOfResponses = sorted(listOfResponses, key=lambda x: x['question_id'])


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

def flatten_list_of_json_strings(nested_list):
    flattened_list = []

    # Iterating over each sublist
    for sublist in nested_list:
        for json_string in sublist:
            # Splitting the string by '},' to handle multiple JSON objects in a single string
            split_strings = json_string.split('},')
            for index, s in enumerate(split_strings):
                # Adding the missing '}' back except for the last item
                if index != len(split_strings) - 1:
                    s += '}'
                # Converting the string to a dictionary and appending to the list
                print(s)
                dict_item = json.loads(s)
                flattened_list.append(dict_item)

    return flattened_list

def alterQuestionGroup(question_list, correct_status):
    # Filtering the list based on the 'is_correct' attribute matching the given string
    filtered_list = [question for question in question_list if str(question.get('is_correct')).lower() == correct_status.lower()]
    return filtered_list

def update_question_list(question_list):
    for question in question_list:
        if question["user_answer"] == question["correct_answer"]:
            question["is_correct"] = "correct"
        else:
            question["is_correct"] = "incorrect"
    return question_list

def alterCorrectMultis(question_list):
    altered_list = []
    for question in question_list:
        if question["is_correct"] == "correct" or question["is_correct"] == True:
            myMsg = True
        else:
            myMsg = False    
        new_question = {
            'correct_answer': question['correct_answer'],
            'is_correct': myMsg,
            'question_id': question['question_id'],
            'feedback': ''
        }
        altered_list.append(new_question)
    return altered_list

def sort_by_question_id(question_list):
    # Sorting the list by 'question_id'
    sorted_list = sorted(question_list, key=lambda x: x['question_id'])
    return sorted_list
