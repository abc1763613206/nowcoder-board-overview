var raw_data = {};
var records = {};
var probs = {};
var problemNum = 0;
var sorted = [];
var teams = {};

let timer = null;

function escapeHtml(text) {
  var map = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  };
  return text.replace(/[&<>"']/g, function (m) {
    return map[m];
  });
}

function getQueryString(name) {
  let reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)", "i");
  let r = window.location.search.substr(1).match(reg);
  if (r != null) {
    return decodeURIComponent(r[2]);
  }
  return null;
}

function doTimeElapsed() {
  var timeElapsed = $("#time_elapsed").attr("sec");
  timeElapsed++;
  $("#time_elapsed").attr("sec", timeElapsed);
  $("#time_elapsed").text("Time Elapsed: " + secondsToTime(timeElapsed));

  var timeLeft = $("#time_left").attr("sec");
  timeLeft--;
  $("#time_left").attr("sec", timeLeft);
  $("#time_left").text("Time Left: " + secondsToTime(timeLeft));
  if (timeLeft <= 0) {
    $("time_elapsed").text("");
    $("#time_left").text("Contest Ended");
    clearInterval(timer);
  }

  var totalTime = timeElapsed + timeLeft;

  $("#progress-bar").css("width", (timeElapsed / totalTime) * 100 + "%");
  if (timeLeft <= 0) {
    $("#progress-bar").text("ENDED");
  } else if (timeLeft <= 3600) {
    $("#progress-bar").text("FROZEN");
    $("#progress-bar").css("background-color", "#e0e0ff");
  } else {
    $("#progress-bar").text("RUNNING");
    $("#progress-bar").css("background-color", "#4ad64a");
  }
}

function fetchData() {
  query = {};
  var contestId = getQueryString("contestId");
  var searchName = getQueryString("searchName");
  if (searchName) {
    query.searchName = searchName;
  }
  if (contestId == null) {
    return;
  }
  $.ajax({
    url: "/api/nowcoder/" + contestId,
    type: "GET",
    data: query,
    success: function (data) {
      raw_data = data;
      renderBoard();
    },
  });
}

function renderBoard() {
  $("#time_elapsed").append(secondsToTime(timeElapsed));
  $("#contest_title").text(raw_data.contest.contest_name);
  $("#contest_time").text(
    "Contest Time: " +
      secondsToDateTime(raw_data.contest.start_time) +
      " - " +
      secondsToDateTime(raw_data.contest.end_time)
  );
  $("#sponsors").text(
    "Brought to you By " + raw_data.contest.organization + "."
  );

  var curTime = parseInt(new Date().getTime() / 1000);
  var timeLeft = raw_data.contest.end_time - curTime;
  //console.log(timeLeft);
  if (timeLeft <= 0) {
    $("#time_left").text("Contest Ended");
  } else {
    $("#time_left").attr("sec", timeLeft);
  }

  timeElapsed =
    parseInt(new Date().getTime() / 1000) - raw_data.contest.start_time;
  $("#time_elapsed").attr("sec", timeElapsed);
  if (
    curTime >= raw_data.contest.start_time &&
    curTime <= raw_data.contest.end_time
  ) {
    timer = setInterval(doTimeElapsed, 1000);
  } else if (curTime < raw_data.contest.start_time) {
    $("#time_elapsed").text("Contest has not started yet");
    $("#time_left").text("");
    $("#progress-bar").css("width", "100%");
    $("#progress-bar").text("PENDING");
  } else {
    $("#time_elapsed").text("");
    $("#progress-bar").css("width", "100%");
    $("#progress-bar").text("ENDED");
  }
  problemNum = raw_data.contest.problem_quantity;
  for (var i = 0; i < problemNum; i++) {
    probs[raw_data.contest.problem[i].index] = {
      ac: raw_data.contest.problem[i].accepted,
      tries: raw_data.contest.problem[i].submission,
      firstblood: 0,
      problem_id: raw_data.contest.problem[i].problem_id,
      title: raw_data.contest.problem[i].title,
    };
  }

  for (var i = 0; i < raw_data.runs.length; i++) {
    var team = raw_data.runs[i].team_id;
    var prob = raw_data.runs[i].problem_id;
    var time = raw_data.runs[i].timestamp;
    var verd = raw_data.runs[i].status;

    if (typeof records[team] === "undefined") {
      records[team] = {
        solved: 0,
        penalty: 0,
      };
    }
    if (typeof records[team][prob] === "undefined") {
      records[team][prob] = {
        status: "",
        tries: 0,
        ac: -1,
        record: "",
      };
    }

    if (verd == "CORRECT") {
      records[team][prob].record += parseInt(time / 1000) + "A";
      if (records[team][prob].ac < 0) {
        records[team][prob].status = "accepted";
        records[team][prob].tries++;
        records[team][prob].ac = parseInt(time / 1000 / 60);

        records[team].solved++;
        records[team].penalty +=
          parseInt(time / 1000 / 60) + (records[team][prob].tries - 1) * 20;
        //console.log(prob);
        //probs[prob].tries++;
        //probs[prob].ac++;
        //console.log(probs[prob].firstblood);
        if (probs[prob].firstblood == 0) {
          probs[prob].firstblood = team;
          records[team][prob].status = "firstblood";
        }
      }
    } else if (verd == "PENDING") {
      records[team][prob].record += parseInt(time / 1000) + "P";
      if (records[team][prob].ac < 0) {
        records[team][prob].status = "pending";
        records[team][prob].tries++;

        //probs[prob].tries++;
      }
    } else if (verd == "INCORRECT") {
      records[team][prob].record += parseInt(time / 1000) + "R";
      if (records[team][prob].ac < 0) {
        records[team][prob].status = "rejected";
        records[team][prob].tries++;
      }
    }
  }

  for (var key in records) {
    sorted.push(key);
  }
  sorted.sort(function (x, y) {
    if (records[x].solved > records[y].solved) {
      return -1;
    } else if (records[x].solved == records[y].solved) {
      if (records[x].penalty < records[y].penalty) {
        return -1;
      } else if (records[x].penalty == records[y].penalty) {
        return 0;
      }
    }
    return 1;
  });

  for (var i = 0; i < problemNum; i++) {
    $("#board thead tr:nth-child(1)").append(
      '<th class="prob_h">' + String.fromCharCode(65 + i) + "</th>"
    );
  }
  for (var i = 0; i < problemNum; i++) {
    var prob = String.fromCharCode(65 + i);
    $("#board thead tr:nth-child(2)").append(
      '<th class="prob_h">' + probs[prob].ac + "/" + probs[prob].tries + "</th>"
    );
  }

  teams = raw_data.teams;

  for (var i = 0; i < sorted.length; i++) {
    var team = sorted[i];
    var tm = teams[team] || {
      type: "unofficial",
      organization: "*",
      members: "*",
      team: "*",
    };
    var node =
      '<tr id="t' +
      team +
      '" class="type1">' +
      '<td class="realrank">' +
      tm.extra["real_rank"] +
      "</td>" +
      '<td class="rank"></td>' +
      '<td class="schoolrank"></td>' +
      '<td class="school">' +
      escapeHtml(tm.organization) +
      "</td>" +
      '<td class="team" members="' +
      tm.team_id +
      '">' +
      escapeHtml(tm.name) +
      "</td>" +
      '<td class="solved">' +
      records[team].solved +
      "</td>" +
      '<td class="penalty">' +
      records[team].penalty +
      "</td>";

    for (var j = 0; j < problemNum; j++) {
      var prob = String.fromCharCode(65 + j);
      if (
        typeof records[team][prob] === "undefined" ||
        records[team][prob].tries == 0
      ) {
        node += '<td class="prob_d untried">.</td>';
      } else {
        node +=
          '<td class="prob_d ' +
          records[team][prob].status +
          '" rec="' +
          records[team][prob].record +
          '">';
        if (records[team][prob].ac < 0) {
          node += records[team][prob].tries + "</td>";
        } else {
          node +=
            records[team][prob].ac + "(" + records[team][prob].tries + ")</td>";
        }
      }
    }

    node += "</tr>";
    $("#board tbody").append(node);
  }
  dorank();
  if (scrollParam != null) {
    scrollPage();
  }

  $("td.untried").each(function (i) {
    $(this).attr("onclick", "popdown()");
  });

  $("td.prob_d")
    .filter(":not(.untried)")
    .each(function (i) {
      $(this).attr("onclick", "showsub(this)");
    });
  $("td.team").each(function (i) {
    $(this).attr("onclick", "showteam(this)");
  });
}
