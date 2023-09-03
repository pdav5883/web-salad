//let start_button = document.getElementById("start_button")
//let start_box = document.getElementById("start_box")
//let submit_button = document.getElementById("submit_button")
//let submit_box = document.getElementById("submit_box")
//let yes_button = document.getElementById("yes_button")
//let no_button = document.getElementById("no_button")
//let yes_no_box = document.getElementById("yes_no_box")
//let current_word = document.getElementById("current_word")
//let time_remaining = document.getElementById("time_remaining")
//let word_table = document.getElementById("word_table")
let audioCtx = new (window.AudioContext || window.webkitAudioContext || window.audioContext);

var words
var wids
var counter
var next_word
var next_wid
var attempt_start
var timer

var attempt_words = []
var attempt_wids = []
var attempt_point = [] // true if someone got a point
var attempt_success = [] // true if guessing team got point
var attempt_durs = [] // the counter value when this attempt ends

const mark_corr = "\u2713"
const mark_miss = "\u2717"
const color_corr = "#33C433"
const color_miss = "#FF1B09"


$(document).ready( function() {
  $("#game-id-text").html($("#game-id-text").html().replace("__", sessionStorage.getItem("gid")))
  
  $.ajax({
    type: "GET",
    url: api_url_prepareturn,
    data: {"gid": sessionStorage.getItem("gid"), "pid": sessionStorage.getItem("pid")},
    crossDomain: true,

    success: function(data) {
      $("#statustext").html("")
      if (!data.myturn) {
	window.location.href = "scoreboard.html"
      }

      words = data.words
      wids = data.wids
      counter = data.time_remaining

      next_word = words.pop()
      next_wid = wids.pop()
      attempt_start = counter

      $("#time_remaining").html(counter)
      $("#yes_button").hide()
      $("#no_button").hide()
      $("#yes_no_box").hide()
      $("#submit_button").hide()
      $("#submit_box").hide()
      $("#word_table").hide()

      $("#start_button").on("click", function() {
	startTurn()
	audioCtx.resume()
      })

      $("#yes_button").on("click", function() {
	correct()
	next()
      })

      $("#no_button").on("click", function() {
	miss()
	next()
      })

      $("#submit_button").on("click", function() {
	submitTurn()
      })   
    },
    
    error: function(err) {
      const message = JSON.parse(err.responseText).message
      $("#statustext").html(message)
    }
  })
})


function startTurn() {
  start_button.style.visibility = "hidden"
  start_box.style.visibility = "hidden"
  yes_button.style.visibility = "visible"
  no_button.style.visibility = "visible"
  yes_no_box.style.visibility = "visible"
  current_word.textContent = next_word

  $("#start_button").show()
  $("#start_box").hide()
  $("#yes_button").show()
  $("#no_button").show()
  $("#yes_no_box").show()
  $("#current_word").html(next_word)

  timer = setInterval(cycle_timer, 1000)
}


function stopTurn() {
  clearInterval(timer)
  $("#yes_button").hide()
  $("#no_button").hide()
  $("#yes_no_box").hide()
  $("#submit_button").show()
  $("#submit_box").show()
  $("#current_word").html("")

  // display correct/missed words
  var addItem = function (word, mark, mark_color) {
    var row = $("<tr></tr>")
    row.append($("<td></td>").text(word))
    row.append($("<td></td>").text(mark).css("color", mark_color))
    $("#word_table_body").append(row)
  }

  for(var i=0; i < attempt_words.length; i++){
    if(attempt_success[i] == true) {
      addItem(attempt_words[i], mark_corr, color_corr)
    }
    else if(attempt_success[i] == false) {
      addItem(attempt_words[i], mark_miss, color_miss)
    }
  }
  $("#word_table").show()
}


function submitTurn() {
  $.ajax({
    type: "POST",
    url: api_url_submitturn,
    contentType: "application/json",
    data: JSON.stringify({
      "gid": sessionStorage.getItem("gid"),
      "pid": sessionStorage.getItem("pid"),
      "attempt_wids": attempt_wids,
      "attempt_point": attempt_point,
      "attempt_success": attempt_success,
      "attempt_durs": attempt_durs,
      "time_remaining": counter
    }),

    crossDomain: true,

    success: function(data) {
      $("#statustext").html("")
      window.location.href = "scoreboard.html"
    },

    error: function(err) {
      const message = JSON.parse(err.responseText).message
      $("#statustext").html(message)
    }
  })
}


function correct() {
    attempt_words.push(next_word)
    attempt_wids.push(next_wid)
    attempt_point.push(true)
    attempt_success.push(true)
    attempt_durs.push(attempt_start - counter)
}


function miss() {
    attempt_words.push(next_word)
    attempt_wids.push(next_wid)
    attempt_point.push(true)
    attempt_success.push(false)
    attempt_durs.push(attempt_start - counter)
}


function next() {
  if (words.length == 0) {
    stopTurn()
  }
  else {
      next_word = words.pop()
      next_wid = wids.pop()
      attempt_start = counter
      $("#current_word").html(next_word)
  }
}


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

function cycle_timer() {
  counter--
  $("#time_remaining").html(counter)

  if (counter == 0) { // or no time remaining
    beep(500, 300, 0.5, "triangle")
    attempt_words.push(next_word)
    attempt_wids.push(next_wid)
    attempt_point.push(false)
    attempt_success.push(false)
    attempt_durs.push(attempt_start - counter)
    stopTurn()
  }
  else if (counter == 5) { // beep for five second warning
    beep(100, 500, 0.5, "sine")
  }
}

