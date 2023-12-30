import logging
from openai import OpenAI

import re

#This function takes 2 strings: a question and an answer, it then returns a Submission object which contains a mark (incorrect, correct, unknown) and feedback.

class Submission:
    def __init__(self, mark, feedback):
        self.mark = mark #either correct or incorrect
        self.feedback = feedback   #feedback from the AI as to why the user is wrong/right.

def answer_quiz(
    myQuestion: str,
    myAnswer: str = "",
) -> dict:
    
    #This code will ask you to enter a question and an answer, chatGPT will mark you and the submission object will be created and printed.
    completion = markShortAnswer(myQuestion,myAnswer)

    response_text = completion.choices[0].message.content

    submission = parseMarking(response_text)

    print(submission)

    return submission # a dictionary
    

def markShortAnswer(question,answer): #gives chatGPT a question and the student's answer and asks chatGPT to give a mark (correct/incorrect) and feedback.
    client = OpenAI()
    myMessageSystem = "You are a teacher, look at the short-answer question provided and the student's answer. You must respond in the following way: say either Correct or Incorrect. Then explain why the student was right/wrong."
    
    completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": myMessageSystem},
        {"role": "user", "content": "Question: " + question + "\n Answer: " + answer}
    ]
    )

    return completion

def parseMarking(response_text): #takes chatGPT's marking and formats it into a Submission object.

    if response_text.startswith("Correct"):
        mark = "Correct"
    elif response_text.startswith("Incorrect"):
        mark = "Incorrect"
    else:
        mark = "unknown"

    # The feedback is the rest of the response after the mark
    feedback = response_text.partition(". ")[2]

    submission = Submission(mark, feedback)
    return submission

#This code will ask you to enter a question and an answer, chatGPT will mark you and the submission object will be created and printed.
#myQuestion = input("enter a question: ")
#myAnswer = input("enter the answer: ")
#completion = answer_quiz(myQuestion,myAnswer)

#print(completion.__dict__)