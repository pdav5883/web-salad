
$(document).ready( function() {
  $("#game-id-text").html($("#game-id-text").html().replace("__", sessionStorage.getItem("gid")))
  
  $.ajax({
    type: "GET",
    url: api_url_getendgame,
    data: {"gid": sessionStorage.getItem("gid"), "pid": sessionStorage.getItem("pid")},
    crossDomain: true,

    success: function(data) {
      $("#statustext").html("")
      if (!data.complete) {
	window.location.href = "scoreboard.html"
      }

      $("#winner_str").html(data.winner_str)

      $("#team-a-score").append($("<td>" + data.scores.r1a + "</td>"))
      $("#team-a-score").append($("<td>" + data.scores.r2a + "</td>"))
      $("#team-a-score").append($("<td>" + data.scores.r3a + "</td>"))
      $("#team-a-score").append($("<td>" + data.scores.totala + "</td>"))
      $("#team-b-score").append($("<td>" + data.scores.r1b + "</td>"))
      $("#team-b-score").append($("<td>" + data.scores.r2b + "</td>"))
      $("#team-b-score").append($("<td>" + data.scores.r3b + "</td>"))
      $("#team-b-score").append($("<td>" + data.scores.totalb + "</td>"))
      
      $("#mvp_name").html($("#mvp_name").html().replace("__", data.stats.mvp_name))
      $("#hardest_word").html($("#hardest_word").html().replace("__", data.stats.hardest_word))
      $("#easiest_word").html($("#easiest_word").html().replace("__", data.stats.easiest_word))

      var row
      for (var i = 0; i < data.stats.teama.length; i++) {
	row = $("<tr></tr>")
	row.append($("<td>" + data.stats.teama[i][0] + "</td>"))
	row.append($("<td>" + data.stats.teama[i][1] + "</td>"))
	row.append($("<td>" + data.stats.teama[i][2] + "</td>"))
	row.append($("<td>" + data.stats.teama[i][3] + "</td>"))
	row.append($("<td>" + data.stats.teama[i][4] + "</td>"))
	$("#box-score-table-a").append(row)
      }

      for (var i = 0; i < data.stats.teamb.length; i++) {
	row = $("<tr></tr>")
	row.append($("<td>" + data.stats.teamb[i][0] + "</td>"))
	row.append($("<td>" + data.stats.teamb[i][1] + "</td>"))
	row.append($("<td>" + data.stats.teamb[i][2] + "</td>"))
	row.append($("<td>" + data.stats.teamb[i][3] + "</td>"))
	row.append($("<td>" + data.stats.teamb[i][4] + "</td>"))
	$("#box-score-table-b").append(row)
      }

      for (var i = 0; i < data.stats.words.length; i++) {
	row = $("<tr></tr>")
	row.append($("<td>" + data.stats.words[i][0] + "</td>"))
	row.append($("<td>" + data.stats.words[i][1] + "</td>"))
	row.append($("<td>" + data.stats.words[i][2] + "</td>"))
	row.append($("<td>" + data.stats.words[i][3] + "</td>"))
	row.append($("<td>" + data.stats.words[i][4] + "</td>"))
	$("#box-score-table-words").append(row)
      }
    },
      
    error: function(err) {
      const message = JSON.parse(err.responseText).message
      $("#statustext").html(message)
    }
  })
})

