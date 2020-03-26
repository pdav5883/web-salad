let start_button = document.getElementById("start_button")
let yes_button = document.getElementById("yes_button")
let no_button = document.getElementById("no_button")
let current_word = document.getElementById("current_word")
let next_word = words.pop()
let next_wid = wids.pop()

let correct_words = []
let correct_wids = []
let miss_words = []
let miss_wids = []

yes_button.style.visibility = "hidden"
no_button.style.visibility = "hidden"

function start_round() {
    start_button.style.visibility = "hidden"
    yes_button.style.visibility = "visible"
    no_button.style.visibility = "visible"
    current_word.textContent = next_word
}

function correct() {
    correct_words.push(next_word)
    correct_wids.push(next_wid)
}

function miss() {
    miss_words.push(next_word)
    miss_wids.push(next_wid)
}

function next() {
    next_word = words.pop()
    next_wid = wids.pop()
    current_word.textContent = next_word
}

start_button.onclick = function() {
    start_round()
}

yes_button.onclick = function() {
    correct()
    next()
}

no_button.onclick = function() {
    miss()
    next()
}



