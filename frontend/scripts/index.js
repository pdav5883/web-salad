
$(document).ready( function() {
  $.get(api_url_getversion, function(data) {
    $("#version").html($("#version").html().replace("__", data.version))
  })
})

function joingame() {
  const gid = $("#gid").val()

  $.ajax({
    type: "GET",
    url: api_url_getgame,
    data: {"gid": gid},
    crossDomain: true,

    success: function(data) {
      $("#statustext").html("")
      sessionStorage.setItem("gid", gid)
      window.location.href = "newplayer.html"
    },

    error: function(err) {
      const message = JSON.parse(err.responseText).message
      $("#statustext").html(message)
    }
  })
}
