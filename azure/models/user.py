import json
import os

import bcrypt


class InvalidField(ValueError):
    pass


class MissingField(ValueError):
    pass


class User:
    def __init__(self, username, password, id=None, **kwargs):
        self.id = id
        self.username = username
        self.password = password

    def to_dict(self):
        return {
            "username": self.username,
            "password": self.password,
        }

    def hash_password(self):
        hashed_pass = bcrypt.hashpw(self.password.encode("utf-8"), bcrypt.gensalt())
        self.password = hashed_pass.decode("utf-8")

    def check_password(self, inputPassword):
        return bcrypt.checkpw(
            inputPassword.encode("utf-8"), self.password.encode("utf-8")
        )

    @staticmethod
    def is_valid(username, password):
        # validate username and password
        if not (4 <= len(username) <= 16):
            raise InvalidField("Username must be between 4 and 16 characters")
        if not (9 <= len(password) <= 30):
            raise InvalidField("Password must be between 9 and 30 characters")
        return True

    @staticmethod
    def from_dict(source):
        # check if all fields are present
        if not all(field in source for field in ["username", "password"]):
            raise MissingField("Missing field(s)")

        return User(**source)

    @staticmethod
    def from_json(source):
        json_dict = json.loads(source)
        return User(**json_dict)

    def __str__(self):
        return f"User(username={self.username}, password={self.password}, id={self.id})"

    def __repr__(self):
        return self.__str__()
