var playerNames = [] // save this for later when sending prepare request

$(document).ready( function() {
  $("#game-id-text").html($("#game-id-text").html().replace("__", sessionStorage.getItem("gid")))
  $("#beep-button").onclick = function() {
    beep(100, 500, 0.5, "sine")
  }
  
  $.ajax({
    type: "GET",
    url: api_url_getroster,
    data: {"gid": sessionStorage.getItem("gid"), "pid": sessionStorage.getItem("pid")},
    crossDomain: true,

    success: function(data) {
      if (data.started) {
	window.location.href = "scoreboard.html"
	return
      }

      $("#statustext").html("")

      // build table
      var row = null
      var elem = null

      for (var i = 0; i < data.names_ready.length; i++) {
	playerNames.push(data.names_ready[i][0])

	row = document.createElement("tr")
	elem = document.createElement("td")
	elem.setAttribute("class", "pair-name")
	elem.innerHTML = data.names_ready[i][0]
	row.appendChild(elem)

	elem = document.createElement("td")
	if (data.names_ready[i][1]) {
	  elem.innerHTML = "&#10003"
	}
	else {
	  elem.innerHTML = "&#8230"
	}
	row.appendChild(elem)

	if (data.is_captain) {
	  elem = document.createElement("input")
	  elem.setAttribute("type", "text")
	  elem.setAttribute("class", "pair-group")
	  elem.setAttribute("size", "2")
	  row.appendChild(elem)
	}

	$("#waiting-table").append(row)
      }

      // captain section
      if (data.is_captain) {
	var row = document.createElement("div")
	row.setAttribute("class", "row")
	row.innerHTML = "You are the Captain!<br>Enter pair-wise constraints using the same letter per pair."
	$("#captain-div").append(row)

	row = document.createElement("div")
	row.setAttribute("class", "row")
	var button = document.createElement("button")
	button.setAttribute("class", "button button-primary start-game-button")
	button.innerHTML = "Star Game"
	button.onclick = startGame
	
	row.appendChild(button)
	$("#captain-div").append(row)
      }
      else {
	var row = document.createElement("div")
	row.setAttribute("class", "row")
	row.innerHTML = "Waiting for " + data.captain_name + " to start game..."
	$("#captain-div").append(row)
      }
    },

    error: function(err) {
      const message = JSON.parse(err.responseText).message
      $("#statustext").html(message)
    }
  })
})

function updateRoster() {
  location.reload()
}

function startGame() {
  // collect constraint data
  var groupList = []

  $("#waiting-table").children("tr").each(function() {
    groupList.push(this.children[2].value)
  })

  $.ajax({
    type: "POST",
    url: api_url_preparegame,
    contentType: "application/json",
    data: JSON.stringify({"gid": sessionStorage.getItem("gid"),
      "pid": sessionStorage.getItem("pid"),
      "name_list": playerNames,
      "group_list": groupList
    }),

    crossDomain: true,

    success: function(data) {
      if (data.goto == "scoreboard") {
	window.location.href = "scoreboard.html"
      }
      else {
	$("#statustext").html(data.message)
      }
    },

    error: function(err) {
      const message = JSON.parse(err.responseText).message
      $("#statustext").html(message)
    }
  })
}


let audioCtx = new (window.AudioContext || window.webkitAudioContext || window.audioContext);
let name_list = document.getElementsByClassName("pair-name")
let group_list = document.getElementsByClassName("pair-group")


//duration of the tone in milliseconds. Default is 500
//frequency of the tone in hertz. default is 440
//volume of the tone. Default is 1, off is 0.
//type of tone. Possible values are sine, square, sawtooth, triangle, and custom. Default is sine.
//callback to use on end of tone
function beep(duration, frequency, volume, type, callback) {
    var oscillator = audioCtx.createOscillator();
    var gainNode = audioCtx.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioCtx.destination);

    if (volume){gainNode.gain.value = volume;}
    if (frequency){oscillator.frequency.value = frequency;}
    if (type){oscillator.type = type;}
    if (callback){oscillator.onended = callback;}

    oscillator.start(audioCtx.currentTime);
    oscillator.stop(audioCtx.currentTime + ((duration || 500) / 1000));
};


