let beep_button = document.getElementById("beep_button")
let audioCtx = new (window.AudioContext || window.webkitAudioContext || window.audioContext);
let start_button = document.getElementById("start_button")
let name_list = document.getElementsByClassName("pair-name")
let group_list = document.getElementsByClassName("pair-group")

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

function start_game() {
    let form = document.createElement("form");
    form.setAttribute("method", "post");
    form.setAttribute("action", "/preparegame");

    let addField = function( key, value ){
        let hiddenField = document.createElement("input");
        hiddenField.setAttribute("type", "hidden");
        hiddenField.setAttribute("name", key);
        hiddenField.setAttribute("value", value );

        form.appendChild(hiddenField);
    };

    for(let i=0; i < name_list.length; i++){
        addField("name_list", name_list[i].textContent)
    }

    for(let i=0; i < group_list.length; i++){
        addField("group_list", group_list[i].value)
    }

    document.body.appendChild(form)
    form.submit()
};

beep_button.onclick = function() {
    beep(100, 500, 0.5, "sine")
};

start_button.onclick = function () {
    start_game()
};
