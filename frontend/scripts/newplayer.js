
$(document).ready( function() {
  $("#game-id-text").html(sessionStorage.getItem("gid"))
})

function submitPlayer() {
  const gid = sessionStorage.getItem("gid")
  const pname = $("#pname").val()

  $.ajax({
    type: "GET",
    url: api_url_submitplayer,
    data: {"gid": gid, "pname": pname},
    crossDomain: true,

    success: function(data) {
      $("#statustext").html("")
      sessionStorage.setItem("pid", data.pid)
      window.location.href = "newwords.html"
    },

    error: function(err) {
      const message = JSON.parse(err.responseText).message
      $("#statustext").html(message)
    }
  })
}
