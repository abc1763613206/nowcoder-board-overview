import os
from flask import Flask, request, jsonify
from spider.spiders.nowcoder import NowCoder

app = Flask(__name__)

HOST = os.getenv("HOST", "0.0.0.0")
PORT = os.getenv("PORT", 5000)


@app.route("/index.html")
def index():
    return app.send_static_file("index.html")


@app.route("/api/nowcoder/<int:contest_id>")
def nowcoder(contest_id):
    args = request.args
    if "searchName" in args:
        spider = NowCoder(contest_id, searchUserName=args["searchName"])
    else:
        spider = NowCoder(contest_id)
    try:
        spider.init_basic_info().fetch_problems().fetch().parse_teams().parse_runs()
    except Exception as e:
        spider.init_basic_info()
    return jsonify(spider.to_dict())


@app.route("/")
def frontend():
    args = request.args
    if "contestId" in args:
        return app.send_static_file("index.html")
    else:
        return app.send_static_file("helper.html")


if __name__ == "__main__":
    app.run(host=HOST, port=PORT)
