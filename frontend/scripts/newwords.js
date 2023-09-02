var wordList = []

$(document).ready( function() {
  $("#game-id-text").html($("#game-id-text").html().replace("__", sessionStorage.getItem("gid")))

  $.ajax({
    type: "GET",
    url: api_url_getgame,
    data: {"gid": sessionStorage.getItem("gid")},
    crossDomain: true,

    success: function(data) {
      $("#statustext").html("")

      var elem = null
      for (var i = 0; i < data.numwords; i++) {
	elem = document.createElement("input")
	elem.setAttribute("type", "text")
	elem.setAttribute("name", "words")
	$("#main-block").prepend(document.createElement("br"))
	$("#main-block").prepend(elem)
	wordList.push(elem)
      }
    },

    error: function(err) {
      const message = JSON.parse(err.responseText).message
      $("#statustext").html(message)
    }
  })
})

function submitWords() {
  
  // retrieve all words inputs and make sure they're filled
  words = []
  for (const wordElem of wordList) {
    if (wordElem.value == "") {
      $("#statustext").html("Missing words")
      return
    }

    words.push(wordElem.value)
  }

  const gid = sessionStorage.getItem("gid")
  const pid = sessionStorage.getItem("pid")

  $.ajax({
    type: "GET",
    url: api_url_submitwords,
    data: {"gid": gid, "pid": pid, "words": words},
    crossDomain: true,

    success: function(data) {
      $("#statustext").html("")
      window.location.href = "roster.html"
    },

    error: function(err) {
      const message = JSON.parse(err.responseText).message
      $("#statustext").html(message)
    }
  })
}
