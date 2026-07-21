const params = new URLSearchParams(window.location.search);
const filename = params.get("img");

console.log("filename: " + filename);
if (filename) {
  const container = document.getElementById("bgimage");
  container.style.backgroundImage = `url(/uploads/${filename}.png)`;
}


document.querySelector('input[name="name"]').value = params.get("name") || "";
document.querySelector('input[name="producer"]').value = params.get("producer") || "";
console.log(params.get("producer"));
document.querySelector('input[name="grape_variety"]').value = params.get("grape_variety") || "";
document.querySelector('input[name="region"]').value = params.get("region") || "";
const add_remove = params.get("qry") || "add";
let confirmation_route = "/add-to-cellar";
const confirmButton = document.getElementById("confirm");

if (add_remove === "remove") {
  confirmation_route = "/remove-from-cellar";
  confirmButton.textContent = "Remove from cellar";
} else {
  confirmButton.textContent = "Add to cellar";
}

if(params.get("year") == "0"){
  document.querySelector('input[name="year"]').value = "";
}
else{
  document.querySelector('input[name="year"]').value = params.get("year") || "";
}
function loadCurrentCellar(){
    let cellar = localStorage.getItem("cellarmaster-selected-cellar") || "";
    return cellar
}
loadCurrentCellar()


const form = document.getElementById("wine-form");
console.log(form);
function getFormData() {
  return Object.fromEntries(new FormData(form));
}

confirmButton.addEventListener("click", async (e) => {
  e.preventDefault();
  let data = getFormData();
  const cellar = loadCurrentCellar();
  if (!cellar) {
    window.location.href = "/";
    return;
  }
  data.imgpath = params.get("img");
  console.log("data: " + JSON.stringify(data));
  data.cellar = cellar;
  console.log()
  const res = await fetch(`${confirmation_route}?c=${encodeURIComponent(cellar)}`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(data)
  });

  const result = await res.json();
  console.log(result);
  if (!res.ok) {
    return;
  }

  window.location.href = ("/home")
  });
