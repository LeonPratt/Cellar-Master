const cellarList = document.querySelector("[data-cellar-list]");
const createButton = document.querySelector("[data-create-button]");
const createForm = document.querySelector("[data-create-form]");
const cellarNameInput = document.querySelector("#cellar-name");
const cancelButton = document.querySelector("[data-cancel-button]");
const status = document.querySelector("[data-status]");

async function loadCellars() {
    try {
      const response = await fetch(`/cellars`,
      {method: "GET"
      });

      if (!response.ok) {
          throw new Error("Failed to fetch cellars");
      }

      const data = await response.json();
      console.log(data);
      renderCellars(data.cellars || []);
  }
  catch (error) {
      console.error(error);
  }
}

async function saveCellar(name) {
    try {
      const response = await fetch(`/cellars/new`,
      {method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({name})
      });

      if (!response.ok) {
          throw new Error("Failed to save cellar");
      }

      const data = await response.json();
      return data.cellar;
  }
  catch (error) {
      console.error(error);
  }
}

async function removeCellar(id, name){
    try {
      const response = await fetch(`/cellars/delete`,
      {method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({id})
      });

      if (!response.ok) {
          throw new Error("Failed to delete cellar");
      }

      if (localStorage.getItem("cellarmaster-selected-cellar") === name) {
        localStorage.removeItem("cellarmaster-selected-cellar");
      }
      await loadCellars();
  }
  catch (error) {
      console.error(error);
  }
}

function setStatus(message) {
  status.textContent = message;
}

function selectCellar(name) {
  localStorage.setItem("cellarmaster-selected-cellar", name);
  setStatus(`${name} is selected.`);
  window.location.href = "/home";
}


function renderCellars(cellars) {
  cellarList.replaceChildren();
  console.log(cellars.length)
  if (cellars.length === 0) {
    const emptyState = document.createElement("p");
    emptyState.className = "cellar-empty-state";
    emptyState.textContent = "No cellars yet. Create one to start tracking your wines.";
    cellarList.appendChild(emptyState);
    return;
  }

  for (let c = 0; c < cellars.length; c++) {
    const cellar = cellars[c];
    cellar.num_bottles = cellar.num_bottles || 0;
    const card = document.createElement("article");
    card.className = "cellar-choice-card";
    card.setAttribute("role", "listitem");

    const details = document.createElement("div");
    const name = document.createElement("h4");
    name.textContent = cellar.name;
    name.style.fontSize="25px";
    const bottles = document.createElement("div");
    bottles.className = "tasting-note-tag"
    bottles.textContent = `${cellar.num_bottles} bottles in cellar`
    details.append(name, bottles);

    const selectButton = document.createElement("button");
    selectButton.className = "action-btn view-btn";
    selectButton.type = "button";
    selectButton.textContent = "Select";
    selectButton.style.marginRight="10px";
    selectButton.addEventListener("click", () => selectCellar(cellar.name));

    const removeButton = document.createElement("button");
    removeButton.className = "action-btn delete-btn";
    removeButton.type = "button";
    removeButton.textContent = "Remove";
    removeButton.addEventListener("click", () => removeCellar(cellar.cellarid, cellar.name));


    const buttonDiv = document.createElement("div");
    buttonDiv.style.display = "flex";
    buttonDiv.appendChild(selectButton);
    buttonDiv.appendChild(removeButton);
    card.append(details, buttonDiv);
    cellarList.appendChild(card);
  }
}

function showCreateForm() {
  createForm.hidden = false;
  createButton.hidden = true;
  cellarNameInput.focus();
}

function hideCreateForm() {
  createForm.reset();
  createForm.hidden = true;
  createButton.hidden = false;
}

createButton.addEventListener("click", showCreateForm);
cancelButton.addEventListener("click", hideCreateForm);

createForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const name = cellarNameInput.value.trim();

  if (!name) {
    return;
  }
  const cellar = await saveCellar(name);
  if (!cellar) {
    setStatus("Could not create that cellar. Please try a different name.");
    return;
  }

  hideCreateForm();
  selectCellar(cellar.name);
});

document.querySelector("[data-home-button]").addEventListener("click", () => {
  window.location.href = "/";
});

loadCellars();
