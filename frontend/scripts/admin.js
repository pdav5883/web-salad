
function submitGame() {
  $.ajax({
    type: "GET",
    url: api_url_submitgame,
    data: {"new_gid": $("#new_gid").val(),
      "num_words": $("#num_words").val(),
      "t1": $("#t1").val(),
      "t2": $("#t2").val(),
      "t3": $("#t3").val(),
    },
    crossDomain: true,

    success: function(data) {
      window.location.href = "/"
    },

    error: function(err) {
      const message = JSON.parse(err.responseText).message
      $("#statustext").html(message)
    }
  })
}
