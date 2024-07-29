import typing
import json

from .type import *
from .constants import *


class Problem:
    def __init__(
        self,
        idx: int = 0,  # 数字idx，从0开始
        index: str = "",
        title: str = "",
        problem_id: str = "",
        accepted: int = 0,
        submission: int = 0,
        score: int = 100,
    ):
        self.idx = idx
        self.index = index
        self.title = title
        self.problem_id = problem_id
        self.accepted = accepted
        self.submission = submission
        self.score = score

    @property
    def get_dict(self):
        obj = {}
        obj["idx"] = self.idx
        obj["index"] = self.index
        obj["title"] = self.title
        obj["problem_id"] = self.problem_id
        obj["accepted"] = self.accepted
        obj["submission"] = self.submission
        obj["score"] = self.score

        return obj

    @property
    def get_json(self):
        return json.dumps(self.get_dict)


IProblems = typing.List[Problem]


class Problems(IProblems):
    def __init__(self):
        return

    @property
    def get_dict(self):
        return [item.get_dict for item in self]

    @property
    def get_json(self):
        return json.dumps(self.get_dict)
