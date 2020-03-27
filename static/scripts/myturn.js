let start_button = document.getElementById("start_button")
let yes_button = document.getElementById("yes_button")
let no_button = document.getElementById("no_button")
let current_word = document.getElementById("current_word")
let time_remaining = document.getElementById("time_remaining")
let correct_heading = document.getElementById("correct_heading")
let miss_heading = document.getElementById("miss_heading")
let timer

let next_word = words.pop()
let next_wid = wids.pop()

let correct_words = []
let correct_wids = []
let miss_words = []
let miss_wids = []
let counter = counter_start

yes_button.style.visibility = "hidden"
no_button.style.visibility = "hidden"
submit_button.style.visibility = "hidden"
correct_heading.style.visibility = "hidden"
miss_heading.style.visibility = "hidden"
time_remaining.textContent = counter

function start_turn() {
    start_button.style.visibility = "hidden"
    yes_button.style.visibility = "visible"
    no_button.style.visibility = "visible"
    current_word.textContent = next_word

    timer = setInterval(cycle_timer, 1000)
}

function stop_turn() {
    clearInterval(timer)
    yes_button.style.visibility = "hidden"
    no_button.style.visibility = "hidden"
    submit_button.style.visibility = "visible"
    current_word.textContent = "..."

    // display correct/missed words
    let addItem = function (ul_id, word) {
        let ul = document.getElementById(ul_id)
        let li = document.createElement("li")
        li.appendChild(document.createTextNode(word))
        ul.appendChild(li)
    }

    for(let i=0; i < correct_words.length; i++){
        addItem("correct_list", correct_words[i])
    }

    for(let i=0; i < miss_words.length; i++){
        addItem("miss_list", miss_words[i])
    }

    correct_heading.style.visibility = "visible"
    miss_heading.style.visibility = "visible"

}

function submit_turn() {
    let form = document.createElement("form");
    form.setAttribute("method", "post");
    form.setAttribute("action", "/submitturn");

    let addField = function( key, value ){
        let hiddenField = document.createElement("input");
        hiddenField.setAttribute("type", "hidden");
        hiddenField.setAttribute("name", key);
        hiddenField.setAttribute("value", value );

        form.appendChild(hiddenField);
    };

    for(let i=0; i < correct_wids.length; i++){
        addField("correct_wids", correct_wids[i])
    }

    for(let i=0; i < miss_wids.length; i++){
        addField("miss_wids", miss_wids[i])
    }

    addField("time_remaining", counter)

    document.body.appendChild(form);
    form.submit();
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
    if (words.length == 0) {
        stop_turn()
    }
    else {
        next_word = words.pop()
        next_wid = wids.pop()
        current_word.textContent = next_word
    }

}

function cycle_timer() {
    counter--
    time_remaining.textContent = counter

    if (counter == 0) { // or no words remaining
        stop_turn()
    }
}

start_button.onclick = function() {
    start_turn()
}

yes_button.onclick = function() {
    correct()
    next()
}

no_button.onclick = function() {
    miss()
    next()
}

submit_button.onclick = function() {
    submit_turn()
}



