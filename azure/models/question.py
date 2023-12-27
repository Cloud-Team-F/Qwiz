import json
import os

import bcrypt
from datetime import datetime


class InvalidField(ValueError):
    pass


class MissingField(ValueError):
    pass


class Question:
    def __init__(self, question_text, question_type, options=None, passage=None, question_id=None):

        self.question_text = question_text
        self.question_type = question_type
        self.question_id = question_id or self.generateQuestionId()

        if question_type == "multi-choice" and not question_type == "fill-blanks":
            raise MissingField("options required for multi-choice questions")

        if question_type == "fill-blank" and not question_type == "multi-choice":
            raise MissingField("passage required for fill the gaps questions")

        self.options = options or []
        self.passage = self.passage

    @staticmethod
    def generateQuestionId():
        return os.urandom(8).hex()

    def to_dict(self):
        return {
            "question_id": self.question_id,
            "question_text": self.question_text,
            "description": self.description,
            "question_type": self.question_type,
            "options": self.options,
            "passage": self.passage

        }

    @staticmethod
    def from_dict(source):
        # check if all fields are present
        if not all(field in source for field in ["question_text", "question_type"]):
            raise MissingField("Missing field(s)")

        if source["question_type"] not in ["multi-choice", "fill-blanks", ["short-ans"]]:
            raise InvalidField("Invalid question type")

        return Question(**source)

    @staticmethod
    def from_json(source):
        json_dict = json.loads(source)
        return Question.from_dict(json_dict)

    def __str__(self):
        return f"Quiz(question_id={self.question_id}, question_text={self.question_text},"\
            f"question_type={self.question_type}, options={self.options}, passage={self.passage})"

    def __repr__(self):
        return self.__str__()
