const currentCellarBox = document.querySelector(".current-cellar");
const logo = document.getElementById("logo");
const home = document.getElementById("home")

logo.addEventListener("click", () => {
    window.location.href = "/home";
});

home.addEventListener("click", () => {
    window.location.href = "/home";
});


function loadCurrentCellar(){
    let cellar = localStorage.getItem("cellarmaster-selected-cellar") || "";

    currentCellarBox.textContent = cellar;
    return cellar
}
loadCurrentCellar()

currentCellarBox.addEventListener("click",function(){
    window.location.href="/"
})

document.getElementById("add").addEventListener("click", () =>{
    window.location.href=`/camera?qry=add`
});

document.getElementById("remove").addEventListener("click", () =>{
    window.location.href=`/camera?qry=remove`
});