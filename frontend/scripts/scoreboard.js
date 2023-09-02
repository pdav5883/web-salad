
$(document).ready( function() {
  $("#game-id-text").html($("#game-id-text").html().replace("__", sessionStorage.getItem("gid")))
  
  $.ajax({
    type: "GET",
    url: api_url_getscoreboard,
    data: {"gid": sessionStorage.getItem("gid"), "pid": sessionStorage.getItem("pid")},
    crossDomain: true,

    success: function(data) {
      $("#statustext").html("")
      if (data.complete) {
	window.location.href = "gameover.html"
      }

      $("#round-text").html($("#round-text").html().replace("__", data.status.round))

      $("#team-a-score").append($("<td>" + data.scores.r1a + "</td>"))
      $("#team-a-score").append($("<td>" + data.scores.r2a + "</td>"))
      $("#team-a-score").append($("<td>" + data.scores.r3a + "</td>"))
      $("#team-a-score").append($("<td>" + data.scores.totala + "</td>"))
      $("#team-b-score").append($("<td>" + data.scores.r1b + "</td>"))
      $("#team-b-score").append($("<td>" + data.scores.r2b + "</td>"))
      $("#team-b-score").append($("<td>" + data.scores.r3b + "</td>"))
      $("#team-b-score").append($("<td>" + data.scores.totalb + "</td>"))
      
      if (data.myturn) {
	$("#button-div").append($("<button>Start Turn!</button>")
	  .addClass("button button-primary start-turn-button")
	  .on("click", startTurn))
      }
      else {
	$("#button-div").append($("<button>Update</button>")
	  .addClass("button button-primary update-button")
	  .on("click", updateScoreboard))
      }
      
      $("#words-remaining-text").html($("#words-remaining-text").html().replace("__", data.status.num_words))
      $("#up-now-text").html($("#up-now-text").html().replace("__", data.status.curr_player))
      $("#up-next-text").html($("#up-next-text").html().replace("__", data.status.next_player))

      var row = null
      for (var i = 0; i < data.teams.length; i++) {

	row = $("<tr></tr>")
	row.append($("<td>" + data.teams[i][0] + "</td>"))
	row.append($("<td>" + data.teams[i][1] + "</td>"))
	$("#roster-table").append(row)
      }
    },

    error: function(err) {
      const message = JSON.parse(err.responseText).message
      $("#statustext").html(message)
    }
  })
})


function updateScoreboard() {
  location.reload()
}


function startTurn() {
  window.location.href = "myturn.html"
}

