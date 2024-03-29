$(document).ready(function() {

  // Variables
  var $nav = $('.navbar'),
      $popoverLink = $('[data-popover]'),
      $document = $(document)

  function init() {
    $popoverLink.on('click', openPopover)
    $document.on('click', closePopover)
  }

  function openPopover(e) {
    e.preventDefault()
    closePopover();
    var popover = $($(this).data('popover'));
    popover.toggleClass('open')
    e.stopImmediatePropagation();
  }

  function closePopover(e) {
    if($('.popover.open').length > 0) {
      $('.popover').removeClass('open')
    }
  }

  init();
});

var navmenu =
'<ul class="navbar-list">' +
  '<li class="navbar-item"><a class="navbar-link" href="https://home.bearloves.rocks">Home</a></li>' +
  '<li class="navbar-item"><a class="navbar-link" href="/">web-salad</a></li>' +
  '<li class="navbar-item">' +
    '<a class="navbar-link" href="#" data-popover="#aboutPopover">About</a>' +
    '<div id="aboutPopover" class="popover">' +
      '<ul class="popover-list">' +
        '<li class="popover-item">' +
          '<a class="popover-link" href="/rules.html">Rules</a>' +
        '</li>' +
        '<li class="popover-item">' +
          '<a class="popover-link" href="/about.html#">Overview</a>' +
        '</li>' +
        '<li class="popover-item">' +
          '<a class="popover-link" href="/about.html#flow">Flow</a>' +
        '</li>' +
        '<li class="popover-item">' +
          '<a class="popover-link" href="/about.html#database">Database</a>' +
        '</li>' +
        '<li class="popover-item">' +
          '<a class="popover-link" href="/about.html#backend">Backend</a>' +
        '</li>' +
        '<li class="popover-item">' +
          '<a class="popover-link" href="/about.html#frontend">Frontend</a>' +
        '</li>' +
        '<li class="popover-item">' +
          '<a class="popover-link" href="/about.html#hosting">Hosting</a>' +
        '</li>' +
        '<li class="popover-item">' +
          '<a class="popover-link" href="https://github.com/pdav5883/web-salad">Github</a>' +
        '</li>' +
      '</ul>' +
    '</div>' +
  '</li>' +

'</ul>';
