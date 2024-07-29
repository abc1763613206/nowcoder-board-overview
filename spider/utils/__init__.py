import time
from spider.type import Contest, Submissions, constants


def frozen_fallback(contest: Contest, submissions: Submissions):
    for s in submissions:
        if s.timestamp >= contest.end_time - contest.start_time - contest.frozen_time:
            s.status = constants.RESULT_PENDING

    return submissions


def get_timestamp_second(dt):
    if str(dt).isdigit():
        return dt

    time_array = time.strptime(dt, "%Y-%m-%d %H:%M:%S")
    timestamp = time.mktime(time_array)

    return int(timestamp)


def get_timestamp_from_iso8601(dt):
    from datetime import datetime

    datetime_obj = datetime.fromisoformat(dt)
    timestamp = datetime_obj.timestamp()

    return int(timestamp)


def get_now_timestamp_second():
    return int(time.time())
