import json
import os

import bcrypt
from models import Question
from datetime import datetime


class InvalidField(ValueError):
    pass


class MissingField(ValueError):
    pass


class Quiz:
    def __init__(self, title, description, questions, owner_id, users_id, creation_date=None, quiz_id=None):
        self.quiz_id = quiz_id or self.generateQuizId
        self.title = title
        self.description = description
        self.setQuestions(questions)
        self.owner_id = owner_id
        self.users_id = users_id
        self.creation_date = creation_date or datetime.now().isoformat()

    @staticmethod
    def generateQuizId():
        return os.urandom(8).hex()

    def setQuestions(self, questions):
        if not all(isinstance(question, Question) for question in questions):
            raise TypeError(
                "Items of the questions list must be instance of Question class")
        self.questions = questions

    def addQuestion(self, question):
        if not isinstance(question, Question):
            raise TypeError(
                "Items of questin list must be instance of Question class")
        self.questions.append(questoin)

    def to_dict(self):
        return {
            "quiz_id": self.quiz_id,
            "title": self.title,
            "description": self.description,
            "questions": self.questions,
            "owner_id": self.owner_id,
            "users_id": self.user_id,
            "creation_date": self.creation_date
        }

    @staticmethod
    def from_dict(source):
        # check if all fields are present
        if not all(field in source for field in ["title", "description", "questions", "owner_id", "users_id"]):
            raise MissingField("Missing field(s)")

        # strip
        source["title"] = source["title"].strip()
        source["description"] = source["description"].strip()
        if not isinstance(source["questions"], list) or not isinstance(source["users_id"], list):
            raise InvalidField("questions and users_ids must be lists")

        return Quiz(**source)

    @staticmethod
    def from_json(source):
        json_dict = json.loads(source)
        return Quiz.from_dict(json_dict)

    def __str__(self):
        return f"Quiz(quiz_id={self.quiz_id}, title={self.title}, description={self.description},"\
            f"questions={self.questions}, owner_id={self.owner_id}, users_id={self.users_id},"\
            f"creation_date={self.creation_date})"

    def __repr__(self):
        return self.__str__()
