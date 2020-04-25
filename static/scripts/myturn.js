let start_button = document.getElementById("start_button")
let yes_button = document.getElementById("yes_button")
let no_button = document.getElementById("no_button")
let current_word = document.getElementById("current_word")
let time_remaining = document.getElementById("time_remaining")
let correct_heading = document.getElementById("correct_heading")
let miss_heading = document.getElementById("miss_heading")
let audioCtx = new (window.AudioContext || window.webkitAudioContext || window.audioContext);
let timer

let next_word = words.pop()
let next_wid = wids.pop()

let attempt_words = []
let attempt_wids = []
let attempt_correct = [] // true if correct, false if miss, null if no answer
let attempt_durs = [] // the counter value when this attempt ends

let counter = counter_start
let attempt_start = counter

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

    for(let i=0; i < attempt_words.length; i++){
        if(attempt_correct[i] == true) {
            addItem("correct_list", attempt_words[i])
        }
        else if(attempt_correct[i] == false) {
            addItem("miss_list", attempt_words[i])
        }

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

    for(let i=0; i < attempt_wids.length; i++){
        addField("attempt_wids", attempt_wids[i])
    }

    for(let i=0; i < attempt_correct.length; i++){
        addField("attempt_correct", attempt_correct[i])
    }

    for(let i=0; i < attempt_durs.length; i++){
        addField("attempt_durs", attempt_durs[i])
    }

    addField("time_remaining", counter)

    document.body.appendChild(form);
    form.submit();
}

function correct() {
    attempt_words.push(next_word)
    attempt_wids.push(next_wid)
    attempt_correct.push(true)
    attempt_durs.push(attempt_start - counter)
}

function miss() {
    attempt_words.push(next_word)
    attempt_wids.push(next_wid)
    attempt_correct.push(false)
    attempt_durs.push(attempt_start - counter)
}

function next() {
    if (words.length == 0) {
        stop_turn()
    }
    else {
        next_word = words.pop()
        next_wid = wids.pop()
        attempt_start = counter
        current_word.textContent = next_word
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
    time_remaining.textContent = counter

    if (counter == 0) { // or no time remaining
        beep(500, 300, 0.5, "triangle")
        attempt_words.push(next_word)
        attempt_wids.push(next_wid)
        attempt_correct.push(null)
        attempt_durs.push(attempt_start - counter)
        stop_turn()
    } else if (counter == 5) { // beep for five second warning
        beep(100, 500, 0.5, "sine")
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



