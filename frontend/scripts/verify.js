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
document.querySelector('input[name="year"]').value = params.get("year") || "";



const form = document.getElementById("wine-form");
console.log(form);
function getFormData() {
  return Object.fromEntries(new FormData(form));
}

document.getElementById("add").addEventListener("click", async (e) => {
  e.preventDefault();
  let data = getFormData();
  data.imgpath = params.get("img");

  console.log("data: " + JSON.stringify(data));

  const res = await fetch("/add-to-cellar", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(data)
  });

  console.log(await res.json());

  window.location.href = ("/")
});

document.getElementById("remove").addEventListener("click", async (e) => {
  e.preventDefault();

  const res = await fetch("/remove-from-cellar", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(getFormData())
  });

  console.log(await res.json());
  window.location.href = ("/")

});