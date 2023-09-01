
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
    xhrFields: {withCredentials: true},

    success: function() {
      // go to new page
      // TODO: cookie is not setting
    },

    error: function(err) {
      const message = JSON.parse(err.responseText).message
      // display error message
    }
  })
}
