const params = new URLSearchParams(window.location.search);
const filename = params.get("img");

console.log("filename: " + filename);
if (filename) {
  const container = document.getElementById("bgimage");
  container.style.backgroundImage = `url(/uploads/${filename}.png)`;
}

document.querySelector('input[name="name"]').value = params.get("name") || "";
document.querySelector('input[name="grape_variety"]').value = params.get("grape_variety") || "";
document.querySelector('input[name="region"]').value = params.get("region") || "";
if(params.get("year") == "0"){
  document.querySelector('input[name="year"]').value = "Year unknown";
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

document.getElementById("add").addEventListener("click", async (e) => {
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
  const res = await fetch(`/add-to-cellar?c=${encodeURIComponent(cellar)}`, {
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

document.getElementById("remove").addEventListener("click", async (e) => {
  e.preventDefault();
  const data = getFormData();
  const cellar = loadCurrentCellar();
  if (!cellar) {
    window.location.href = "/";
    return;
  }
  data.cellar = cellar;
  const res = await fetch(`/remove-from-cellar?c=${encodeURIComponent(cellar)}`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(data)
  });

  console.log(await res.json());
  window.location.href = ("/home")

});
