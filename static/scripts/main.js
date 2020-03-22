let myHeading = document.querySelector('h1')
let myButton = document.querySelector("button")

function setName() {
    let myName = prompt("Enter name here")
    localStorage.setItem("name",myName)
    myHeading.textContent = "Hello, " + myName
}

myButton.onclick = function() {
    setName()
}



