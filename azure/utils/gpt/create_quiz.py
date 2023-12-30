import logging
from openai import OpenAI

import re


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

    #gather the types and question count, write a function that splits the question count evenly. EG if count = 5, typesCount = {"multi-choice":2,"fill-gaps":2,"short-answer":1}
    # remeber to only use the types the user has asked for.
    typesCount = generateTypesCount(num_questions,question_types)

    completionMulti=""
    completionBlanks=""
    completionShort=""

    for info in file_contents:
        text_content = text_content + info

    if "multi-choice" in typesCount:
        completionMulti = messageMultiChoice(typesCount["multi-choice"],text_content) 
        quizMulti = parse_multi_quiz(completionMulti.choices[0].message.content)

    if "fill-gaps" in typesCount:
        completionBlanks = messageFillBlanks(typesCount["fill-gaps"],text_content)
        #print(completionBlanks.choices[0].message.content)
        quizFill = parse_fill_blanks(completionBlanks.choices[0].message.content)
        #print(quizFill.questions[0].__dict__)
        #print(quizFill.questions[1].__dict__)
        #print(quizFill.questions[2].__dict__)
        questions2fingers = []
        for question in quizFill.questions:
            newQuestion = messageFillBlanks2(question.question)
            newQuestion = parse_fill_blanks2(newQuestion.choices[0].message.content,question.question) #returns a question
            questions2fingers.append(newQuestion)

        quizFill = Quiz(questions2fingers) 
        #print(quizFill)
        #print(quizFill.questions[0].__dict__)
        #print(quizFill.questions[1].__dict__)
        #print(quizFill.questions[2].__dict__)

    if "short-answer" in typesCount:
        completionShort = messageShortAnswer(typesCount["short-answer"],text_content)
        quizShort = parse_short_quiz(completionShort.choices[0].message.content)
    

    

    quizzes = [quizMulti,quizFill,quizShort] 
    finalQuiz = combine_quizzes(quizzes)

    finalQuiz = add_sequential_quiz_id(finalQuiz)

    return finalQuiz
    

    # todo:: gpt stuff

    # Example response (this is what the response should look like)
    return [
        {
            "question_id": "1",
            "question": "What is the capital of France?",
            "type": "multi-choice",
            "options": ["Paris", "London", "Berlin", "Madrid"],
            "correct-answer" : "Paris",
        },
        {
            "question_id": "2",
            "question": "____ is the capital of Spain.",
            "type": "fill-gaps",
            "correct-answer": "Madrid",
        },
        {
            "question_id": "3",
            "question": "What is the capital of Germany?",
            "type": "short-answer",
        },
    ]



'''
Notes to read before implementing:
Each function only makes quizes of ONE question type.
It's likly my class implementations don't match what we already have.so a little code will need editing in the parse functions.
As our quizzes will be a mix of questions, we might want to make algorithms that combine the quizes my code makes.

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
'''



class Question:
    def __init__(self, question, options, correct_answer,type):
        self.question = question
        self.options = options
        self.correct_answer = correct_answer
        self.type = type

class Quiz:
    def __init__(self, questions):
        self.questions = questions

class Submission:
    def __init__(self, mark, feedback):
        self.mark = mark #either correct or incorrect
        self.feedback = feedback   #feedback from the AI as to why the user is wrong/right.     

def add_sequential_quiz_id(quiz):
    for i, question in enumerate(quiz.questions):
        question.quizID = i
    return quiz        

def combine_quizzes(quizzes):
    combined_questions = []
    for quiz in quizzes:
        combined_questions.extend(quiz.questions)
    return Quiz(combined_questions)        

def generateTypesCount(num_questions, question_types):
    """
    Function to split num_questions amongst question_types as evenly as possible.
    Returns a dictionary with each question type and the corresponding count.
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

           

# Function to parse the response text and create the quiz
def parse_multi_quiz(response_text): #takes what chatGPT says and makes a Quiz object containing multichoice questions
    question_parts = response_text.strip().split('\n\n')
    questions = []

    for part in question_parts:
        lines = part.strip().split('\n')
        question_text = lines[0].strip()
        options_with_labels = lines[1:]
        
        options = []
        correct_answer_text = None
        for option_with_label in options_with_labels:
            is_correct = "(Correct)" in option_with_label
            # Remove the label and "(Correct)" marker to get the clean option text
            option_text = re.sub(r'^[a-d]\)\s+|\s+\(Correct\)$', '', option_with_label).strip()
            options.append(option_text)
            if is_correct:
                correct_answer_text = option_text
        
        questions.append(Question(question_text, options, correct_answer_text, "multiChoice"))

    return Quiz(questions)

def parse_short_quiz(response_text): #parses chatGPT's response, the options field and answer field are left empty.
    
    lines = [line.strip() for line in response_text.split('\n') if line.strip() != ""]
    questions = [Question(q.split('. ', 1)[1] if '. ' in q else q, [], None, "shortAnswer") for q in lines]

    return Quiz(questions)

def parse_fill_blanks(quiz_text):
    lines = [line.strip() for line in quiz_text.split('\n') if line.strip() != ""]
    questions = []

    for line in lines:
        # Remove the number and period at the start of each line
        question_text = re.sub(r'^\d+\.\s+', '', line)

        # Create a question with empty options and no correct answer
        question = Question(question_text, [], "", "blanks")
        questions.append(question)

    return Quiz(questions)

def parse_fill_blanks2(quiz_text,phraseUsed):
    lines = [line.strip() for line in quiz_text.split('\n') if line.strip() != ""]
    options = []
    correct_answer = None

    for line in lines:
        # Remove the question number
        option = re.sub(r'^\d+\.\s+', '', line)

        # Check for the correct answer indicator and remove it
        if '*' in option:
            correct_answer = option.replace('*', '')
            option = correct_answer

        options.append(option)

    # Create a question with the options and the correct answer
    question = Question(phraseUsed, options, correct_answer, "blanks")

    return question

def messageMultiChoice(count,text): #asks chatGPT to make a multichoce quiz of length "count" based off of the "text" 

    client = OpenAI()
    myMessageSystem = "Generate a " + str(count) + "-question multiple-choice quiz based on the provided text. Format each question with a number followed by the question text, and list four answer choices labeled a, b, c, and d. Indicate the correct answer by adding the word Correct in parentheses after the corresponding choice. Do not include any additional text or explanations. Ensure that the structure and formatting are consistent with the following example: 1. What is the capital of France? a) Madrid b) Rome c) Paris (Correct) d) Berlin"
    
    completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": myMessageSystem},
        {"role": "user", "content": text}
    ]
    )

    return completion

def messageShortAnswer(count,text): #asks chatGPT to make a short answer quiz of length "count" based off of the "text" 

    client = OpenAI()
    myMessageSystem = "Generate a " + str(count) + "-question short answer quiz based on the provided text. Format each question with a number followed by the question text"
    
    completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": myMessageSystem},
        {"role": "user", "content": text}
    ]
    )
    
    return completion

def messageFillBlanks(count,text): #asks chatGPT to make a fill_blanks quiz of length "count" based off of the "text" 

    client = OpenAI()
    myMessageSystem = "Give me " + str(count) + "facts about the topic below. Do not say anything else but the " + str(count) + " facts. Make it so that these facts would be educational for someone who is new to the topic."
    
    completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": myMessageSystem},
        {"role": "user", "content": text}
    ]
    )

    return completion

def messageFillBlanks2(text): #asks chatGPT to make a multichoce quiz of length "count" based off of the "text" 
    #print("messageing fill blanks 2! " + text)
    client = OpenAI()
    #myMessageSystem = ""
    completion = client.chat.completions.create(
    model="gpt-4-1106-preview",
    messages=[
        {"role": "system", "content": "Using the following fact, create a list of four words suitable for a fill-in-the-blank question. Exactly one option must be a word directly taken from the fact; the other three should be plausible but incorrect alternatives. The chosen words or phrases should all be contextually relevant to the subject of the fact. Indicate which answer is correct by placing a * after it."},
        {"role": "user", "content": "The fact: " + text}
    ]
    )

    return completion

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
    '''
    myQuestion = input("enter a question: ")
    myAnswer = input("enter the answer: ")
    completion = markShortAnswer(myQuestion,myAnswer)
    print(completion.choices[0].message.content)

    response_text = completion.choices[0].message.content

    submission = parseMarking(response_text)

    print(submission.__dict__)
    '''

    #completion3 = messageFillBlanks2(myMessage) #generates a fill_blanks quiz
    #print(completion3.choices[0].message.content)

    '''
    def create_quiz(
    num_questions: int,
    question_types: list[str],
    topic: str = "",
    text_content: str = "",
    file_contents: list[str] = [],
) -> list[dict]:
    '''

    #-------------------MESSAGING CHATGPT---------------------
    #completion1 = messageMultiChoice(myCount,myMessage) #generates a multichoice quiz 

    #completion2 = messageShortAnswer(myCount,myMessage) #generates a short answer quiz

    #completion3 = messageFillBlanks(myCount,myMessage) #generates a fill_blanks quiz

    #---------------------PARSING CHATGPT--------------------
    #response_text1 = completion1.choices[0].message.content
    #quiz1 = parse_multi_quiz(response_text1)

    #response_text2 = completion2.choices[0].message.content
    #quiz2 = parse_short_quiz(response_text2)

    #response_text3 = completion3.choices[0].message.content
    #quiz3 = parse_fill_blanks(response_text3)


    #-----------------------PRINTING THE QUIZZES-------------------
    #print(quiz1.__dict__)
    #print(quiz2.__dict__)
    #print(quiz3.__dict__)
    '''
     print(quiz1.questions[0].__dict__)
    print(quiz1.questions[1].__dict__)  #These 4 lines are for printing specific questions. If you just
    print(quiz1.questions[2].__dict__)  # print the (quiz1.__dict__) like above you'll just get a bunch of 
    print(quiz1.questions[3].__dict__)  # object references instead of being able to see the actual questions.
    print(quiz1.questions[4].__dict__)

    print(quiz2.questions[0].__dict__)
    print(quiz2.questions[1].__dict__)  
    print(quiz2.questions[2].__dict__) 
    print(quiz2.questions[3].__dict__)  
    print(quiz2.questions[4].__dict__)

    print(quiz3.questions[0].__dict__)
    print(quiz3.questions[1].__dict__)  
    print(quiz3.questions[2].__dict__) 
    print(quiz3.questions[3].__dict__)  
    print(quiz3.questions[4].__dict__)
    '''
