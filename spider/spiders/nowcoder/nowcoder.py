import json
import requests
import re
from bs4 import BeautifulSoup

# noinspection PyUnresolvedReferences
import lxml  # dependency of BeautifulSoup
from spider.type import (
    Contest,
    Team,
    Teams,
    Submission,
    Submissions,
    constants,
    Problem,
    Problems,
)
from spider.utils import *


class NowCoder:
    # Special thanks https://github.com/xcpcio/board-spider
    CONSTANT_RANK_URL = (
        "https://ac.nowcoder.com/acm-heavy/acm/contest/real-time-rank-data"
    )

    # CONSTANT_RANK_URL = "http://127.0.0.1:5000/testapi"
    CONSTANT_SUBMISSIONS_URL = (
        "https://ac.nowcoder.com/acm-heavy/acm/contest/status-list"
    )
    CONSTANT_PROBLEMS_URL = "https://ac.nowcoder.com/acm/contest/problem-list"

    def __init__(self, contest_id: int, **kwargs):
        self.contest = Contest()
        self.contest_id = contest_id

        self.fetch_res_list = []
        self.teams = Teams()
        self.submissions = Submissions()
        self.runs = Submissions()
        self.kwargs = kwargs

    def init_basic_info(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        }
        r = requests.get(
            f"https://ac.nowcoder.com/acm/contest/{self.contest_id}", headers=headers
        )
        soup = BeautifulSoup(r.text, "lxml")

        jsons = soup.find_all(
            "script", type="text/javascript", string=re.compile("window.pageInfo")
        )  # 获取 HTML 中的 JSON 数据

        if len(jsons) == 0:
            raise RuntimeError("fetch contest info failed.")

        json_raw = jsons[0].string
        json_raw = re.search(r"window.pageInfo = (.*);", json_raw).group(1)
        json_data = json.loads(json_raw)

        self.contest.contest_name = json_data["name"]
        self.contest.start_time = int(json_data["startTime"]) // 1000
        self.contest.end_time = int(json_data["endTime"]) // 1000
        self.contest.organization = json_data["settingInfo"]["organizerName"]
        return self

    def fetch_problems(self):
        headers = {}
        params = (
            ("token", ""),
            ("id", self.contest_id),
            ("_", get_now_timestamp_second()),
        )

        res = self.req(self.CONSTANT_PROBLEMS_URL, headers, params)
        res = res["data"]

        self.contest.problem_quantity = int(res["basicInfo"]["problemCount"])
        self.contest.problem = Problems()

        for i in res["data"]:
            p = Problem()
            p.idx = ord(i["index"]) - ord("A")
            p.index = i["index"]
            p.title = i["title"]
            p.problem_id = i["problemId"]
            p.accepted = i["acceptedCount"]
            p.submission = i["submitCount"]
            p.score = i["score"]
            self.contest.problem.append(p)

        return self

    def get_basic_info(self):
        headers = {}
        params = (
            ("token", ""),
            ("id", self.contest_id),
            ("_", get_now_timestamp_second()),
            ("pageSize", 1),
        )

        res = self.req(self.CONSTANT_RANK_URL, headers, params)
        return res["data"]["basicInfo"]

    def get_time_diff(self, l, r):
        return int(r - l)

    def req(self, url, headers, params):
        params_kwargs = params + tuple(self.kwargs.items())
        resp = requests.get(url, headers=headers, params=params_kwargs)
        if resp.status_code != 200:
            raise RuntimeError(
                "fetch data failed. [status_code={}]".format(resp.status_code)
            )

        res = json.loads(resp.content)
        if res["code"] != 0:
            raise RuntimeError("fetch data failed. [code={}]".format(res["code"]))

        return res

    def fetch(self):
        total = 0
        headers = {}

        params = (
            ("token", ""),
            ("id", self.contest_id),
            ("limit", "0"),
            ("_", get_now_timestamp_second()),
            ("pageSize", 200),
        )

        res = self.req(self.CONSTANT_RANK_URL, headers, params)

        total = res["data"]["basicInfo"]["pageCount"]

        res_list = []

        res_list.append(res)
        # for i in range(1, total + 1):
        #    params = (
        #        ("token", ""),
        #        ("id", self.contest_id),
        #        ("limit", "0"),
        #        ("_", get_now_timestamp_second()),
        #        ("page", str(i)),
        #        ("pageSize", 500),
        #    )
        #
        #    res = self.req(self.CONSTANT_RANK_URL, headers, params)
        #
        #    res_list.append(res)

        self.fetch_res_list = res_list

        return self

    def fetch_single_team_submissions(self, team: Team):
        runs = Submissions()

        page_ix = 1

        while True:
            params = (
                ("token", ""),
                ("id", self.contest_id),
                ("page", page_ix),
                ("pageSize", 1000),
                ("searchUserName", team.name),
                ("_", get_now_timestamp_second()),
            )
            headers = {}

            res = self.req(self.CONSTANT_SUBMISSIONS_URL, headers, params)

            res = res["data"]

            for r in res["data"]:
                run = Submission()

                team_name = r["userName"]
                if team_name != team.name:
                    continue

                timestamp = int(r["submitTime"]) // 1000
                if timestamp > self.contest.end_time:
                    continue

                status = r["statusMessage"]

                if status == "编译错误":
                    continue

                run.submission_id = str(r["submissionId"])
                run.timestamp = timestamp - self.contest.start_time
                run.team_id = str(r["userId"])
                run.problem_id = str(r["index"])

                if status == "答案正确":
                    run.status = constants.RESULT_CORRECT
                else:
                    run.status = constants.RESULT_INCORRECT

                runs.append(run)

            if page_ix == int(res["basicInfo"]["pageCount"]):
                break

            page_ix += 1

        return runs

    def fetch_submissions(self):
        runs = Submissions()
        for t in self.teams.values():
            r = self.fetch_single_team_submissions(t)
            runs.extend(r)

        self.runs = runs
        return self

    def parse_teams(self):
        teams = Teams()

        for res in self.fetch_res_list:
            item = res["data"]

            for raw_team in item["rankData"]:
                team_id = str(raw_team["uid"])
                team_name = raw_team["userName"].strip()
                team_organization = "---"

                if "school" in raw_team.keys():
                    team_organization = raw_team["school"]

                team = Team()
                team.team_id = team_id
                team.name = team_name
                team.organization = team_organization
                team.extra = {"real_rank": raw_team["ranking"]}
                teams[team_id] = team

        self.teams = teams
        return self

    def parse_runs(self):
        runs = Submissions()

        for res in self.fetch_res_list:
            item = res["data"]

            for raw_team in item["rankData"]:
                team_id = raw_team["uid"]
                i = -1
                for problem in raw_team["scoreList"]:
                    i += 1

                    status = constants.RESULT_INCORRECT
                    timestamp = self.get_time_diff(
                        self.contest.start_time,
                        min(self.contest.end_time, get_now_timestamp_second()),
                    )
                    if problem["accepted"]:
                        status = constants.RESULT_CORRECT
                        timestamp = self.get_time_diff(
                            self.contest.start_time,
                            int(problem["acceptedTime"]) // 1000,
                        )
                    timestamp = timestamp * 1000

                    for j in range(0, problem["failedCount"]):
                        run = Submission()
                        run.team_id = team_id
                        run.timestamp = max(0, timestamp - 1)
                        run.problem_id = chr(ord("A") + i)
                        run.status = constants.RESULT_INCORRECT

                        runs.append(run)

                    for j in range(0, problem["waitingJudgeCount"]):
                        run = Submission()
                        run.team_id = team_id
                        run.timestamp = max(0, timestamp - 1)
                        run.problem_id = chr(ord("A") + i)
                        run.status = constants.RESULT_PENDING

                        runs.append(run)

                    if status == constants.RESULT_CORRECT:
                        run = Submission()
                        run.team_id = team_id
                        run.timestamp = timestamp
                        run.problem_id = chr(ord("A") + i)
                        run.status = constants.RESULT_CORRECT
                        # run.first_blood = problem["firstBlood"]
                        runs.append(run)
        runs.sort(key=lambda x: x.timestamp)
        # self.runs = runs
        self.runs = Submissions()
        return self

    def to_dict(self):
        return {
            "code": 0,
            "message": "success",
            "contest_id": self.contest_id,
            "contest": self.contest.get_dict,
            "teams": self.teams.get_dict,
            "runs": self.runs.get_dict,
        }
