let add_remove = document.getElementById("add_remove")
let search_wine = document.getElementById("search_wine")
let search_pairing = document.getElementById("search_pairing")
const currentCellarBox = document.querySelector(".current-cellar");

console.log("loaded")

function loadCurrentCellar(){
    let cellar = localStorage.getItem("cellarmaster-selected-cellar") || "";

    currentCellarBox.textContent = cellar;
    return cellar
}
loadCurrentCellar()

currentCellarBox.addEventListener("click",function(){
    window.location.href="/"
})

add_remove.addEventListener("click",function(){
    window.location.href = "/camera"
})


search_pairing.addEventListener("click",function(){
    window.location.href = "/pairings"
})


search_wine.addEventListener("click",function(){
    window.location.href = "/search"
})