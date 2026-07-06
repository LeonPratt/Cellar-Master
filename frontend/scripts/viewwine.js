const params = new URLSearchParams(window.location.search);
const wineId = params.get("wineid");

const nameEl = document.querySelector("[data-wine-name]");
const summaryEl = document.querySelector("[data-wine-summary]");
const regionEl = document.querySelector("[data-wine-region]");
const grapesEl = document.querySelector("[data-wine-grapes]");
const yearEl = document.querySelector("[data-wine-year]");
const quantityEl = document.querySelector("[data-wine-quantity]");
const drinkstartEl = document.querySelector("[data-wine-drink-start]");
const drinkendEl = document.querySelector("[data-wine-drink-end]");
const tastingNotesEl = document.querySelector("[data-wine-tasting-notes]");
const tastingNoteForm = document.querySelector("[data-tasting-note-form]");
const tastingNoteInput = document.querySelector("[data-tasting-note-input]");
const tastingNoteStatus = document.querySelector("[data-tasting-note-status]");
const pairingsEl = document.querySelector("[data-wine-pairings]");
const pairingForm = document.querySelector("[data-pairing-form]");
const pairingInput = document.querySelector("[data-pairing-input]");
const pairingStatus = document.querySelector("[data-pairing-status]");
const imageEl = document.querySelector("[data-wine-image]");
const backButton = document.querySelector("[data-back-button]");
const homeButton = document.querySelector("[data-home-button]");

let currentTastingNotes = [];
let currentPairings = [];

backButton.addEventListener("click", () => {
    window.location.href = "/search";
});

homeButton.addEventListener("click", () => {
    window.location.href = "/";
});

function capitalize(text) {
    return String(text ?? "")
        .split(" ")
        .filter(Boolean)
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" ");
}

function formatList(items, fallback) {
    if (!Array.isArray(items) || items.length === 0) {
        return fallback;
    }

    return items.map(capitalize).join(" / ");
}

function formatTastingNotes(value) {
    if (Array.isArray(value)) {
        return value
            .map((note) => String(note ?? "").trim())
            .filter(Boolean);
    }

    const notes = String(value ?? "")
        .split("|")
        .map((note) => note.trim())
        .filter(Boolean);

    return notes;
}

function setTastingNoteStatus(message, isError = false) {
    tastingNoteStatus.textContent = message;
    tastingNoteStatus.classList.toggle("is-error", isError);
}

function setPairingStatus(message, isError = false) {
    pairingStatus.textContent = message;
    pairingStatus.classList.toggle("is-error", isError);
}

function renderPairings(pairings) {
    pairingsEl.innerHTML = "";
    currentPairings = Array.isArray(pairings) ? pairings : [];

    if (currentPairings.length === 0) {
        const empty = document.createElement("span");
        empty.className = "detail-empty";
        empty.textContent = "No pairings saved yet.";
        pairingsEl.appendChild(empty);
        return;
    }

    currentPairings.forEach((pairing) => {
        const tag = document.createElement("span");
        tag.className = "pairing-tag";

        const text = document.createElement("span");
        text.textContent = capitalize(pairing);

        const removeButton = document.createElement("button");
        removeButton.className = "pairing-remove";
        removeButton.type = "button";
        removeButton.dataset.pairing = pairing;
        removeButton.setAttribute("aria-label", `Remove ${pairing}`);

        const removeIcon = document.createElement("img");
        removeIcon.className = "tasting-note-remove-icon";
        removeIcon.setAttribute("src", "/assets/icons/remove.svg");
        removeButton.appendChild(removeIcon);

        tag.append(text, removeButton);
        pairingsEl.appendChild(tag);
    });
}

function renderTastingNotes(notes) {
    tastingNotesEl.innerHTML = "";
    currentTastingNotes = Array.isArray(notes) ? notes : [];

    if (currentTastingNotes.length === 0) {
        const empty = document.createElement("span");
        empty.className = "detail-empty";
        empty.textContent = "No notes saved yet.";
        tastingNotesEl.appendChild(empty);
        return;
    }

    currentTastingNotes.forEach((note) => {
        const tag = document.createElement("span");
        tag.className = "tasting-note-tag";

        const text = document.createElement("span");
        text.textContent = capitalize(note);

        const removeButton = document.createElement("button");
        removeButton.className = "tasting-note-remove";
        removeButton.type = "button";
        removeButton.dataset.note = note;
        removeButton.setAttribute("aria-label", `Remove ${note}`);
        const removeIcon = document.createElement("img");
        removeIcon.className = "tasting-note-remove-icon";
        removeIcon.setAttribute("src", "/assets/icons/remove.svg");
        removeButton.appendChild(removeIcon);

        tag.append(text, removeButton);
        tastingNotesEl.appendChild(tag);
    });
}

function setTastingNoteControlsDisabled(disabled) {
    tastingNoteInput.disabled = disabled;
    tastingNoteForm.querySelector("button").disabled = disabled;
    tastingNotesEl
        .querySelectorAll("button")
        .forEach((button) => {
            button.disabled = disabled;
        });
}

function setPairingControlsDisabled(disabled) {
    pairingInput.disabled = disabled;
    pairingForm.querySelector("button").disabled = disabled;
    pairingsEl
        .querySelectorAll("button")
        .forEach((button) => {
            button.disabled = disabled;
        });
}

async function saveTastingNote(note) {
    const response = await fetch(`/wine/${encodeURIComponent(wineId)}/tasting-notes`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ note })
    });

    if (!response.ok) {
        throw new Error("Failed to add tasting note");
    }

    return response.json();
}

async function deleteTastingNote(note) {
    const response = await fetch(`/wine/${encodeURIComponent(wineId)}/tasting-notes`, {
        method: "DELETE",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ note })
    });

    if (!response.ok) {
        throw new Error("Failed to remove tasting note");
    }

    return response.json();
}

async function savePairing(pairing) {
    const response = await fetch(`/wine/${encodeURIComponent(wineId)}/pairings`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ pairing })
    });

    if (!response.ok) {
        throw new Error("Failed to add pairing");
    }

    return response.json();
}

async function deletePairing(pairing) {
    const response = await fetch(`/wine/${encodeURIComponent(wineId)}/pairings`, {
        method: "DELETE",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ pairing })
    });

    if (!response.ok) {
        throw new Error("Failed to remove pairing");
    }

    return response.json();
}

tastingNoteForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const note = tastingNoteInput.value.trim();
    if (!note) {
        setTastingNoteStatus("Enter a tasting note before adding it.", true);
        return;
    }

    setTastingNoteControlsDisabled(true);
    setTastingNoteStatus("Saving note...");

    try {
        const data = await saveTastingNote(note);
        tastingNoteInput.value = "";
        renderTastingNotes(data.tasting_notes);
        setTastingNoteStatus("Note saved.");
    }
    catch (error) {
        console.error(error);
        setTastingNoteStatus("The note could not be saved.", true);
    }
    finally {
        setTastingNoteControlsDisabled(false);
        tastingNoteInput.focus();
    }
});

pairingForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const pairing = pairingInput.value.trim();
    if (!pairing) {
        setPairingStatus("Enter a pairing before adding it.", true);
        return;
    }

    setPairingControlsDisabled(true);
    setPairingStatus("Saving pairing...");

    try {
        const data = await savePairing(pairing);
        pairingInput.value = "";
        renderPairings(data.pairings);
        setPairingStatus("Pairing saved.");
    }
    catch (error) {
        console.error(error);
        setPairingStatus("The pairing could not be saved.", true);
    }
    finally {
        setPairingControlsDisabled(false);
        pairingInput.focus();
    }
});

tastingNotesEl.addEventListener("click", async (event) => {
    const removeButton = event.target.closest("[data-note]");

    if (!removeButton) {
        return;
    }

    const note = removeButton.dataset.note;
    setTastingNoteControlsDisabled(true);
    setTastingNoteStatus("Removing note...");

    try {
        const data = await deleteTastingNote(note);
        renderTastingNotes(data.tasting_notes);
        setTastingNoteStatus("Note removed.");
    }
    catch (error) {
        console.error(error);
        setTastingNoteStatus("The note could not be removed.", true);
    }
    finally {
        setTastingNoteControlsDisabled(false);
    }
});

pairingsEl.addEventListener("click", async (event) => {
    const removeButton = event.target.closest("[data-pairing]");

    if (!removeButton) {
        return;
    }

    const pairing = removeButton.dataset.pairing;
    setPairingControlsDisabled(true);
    setPairingStatus("Removing pairing...");

    try {
        const data = await deletePairing(pairing);
        renderPairings(data.pairings);
        setPairingStatus("Pairing removed.");
    }
    catch (error) {
        console.error(error);
        setPairingStatus("The pairing could not be removed.", true);
    }
    finally {
        setPairingControlsDisabled(false);
    }
});

function getImageSrc(imgpath) {
    const path = String(imgpath ?? "").trim();

    if (!path) {
        return "";
    }

    if (path.startsWith("http://") || path.startsWith("https://") || path.startsWith("/")) {
        return path;
    }

    return `/uploads/${path}`;
}

function renderImage(wine) {
    const src = getImageSrc(wine.imgpath);

    if (!src) {
        imageEl.hidden = true;
        imageEl.removeAttribute("src");
        imageEl.alt = "";
        return;
    }

    imageEl.src = src;
    imageEl.alt = `${wine.name || "Wine"} bottle`;
    imageEl.hidden = false;
}

function renderError(title, detail) {
    nameEl.textContent = title;
    summaryEl.textContent = detail;
    regionEl.textContent = "Unknown";
    grapesEl.textContent = "Unknown";
    yearEl.textContent = "Unknown";
    quantityEl.textContent = "Unknown";
    drinkstartEl.textContent = "Unknown";
    drinkendEl.textContent = "Unknown";
    renderImage({});
    renderPairings([]);
    renderTastingNotes([]);
}

function renderWine(wine) {
    const grapes = formatList(wine.grapes, "Grape unknown");
    const region = wine.region || "Region unknown";
    const year = wine.year || "Year unknown";
    const quantity = wine.quantity || "Quantity unknown";
    const drinkStart = wine.drink_window_start || "Unknown";
    const drinkEnd = wine.drink_window_end || "Unknown";
    document.title = `${wine.name} | CellarMaster`;
    nameEl.textContent = wine.name || "Unnamed wine";
    summaryEl.textContent = `${grapes} from ${region}`;
    regionEl.textContent = region;
    grapesEl.textContent = grapes;
    yearEl.textContent = year;
    quantityEl.textContent = quantity;
    drinkstartEl.textContent = drinkStart;
    drinkendEl.textContent = drinkEnd;
    renderImage(wine);
    renderPairings(wine.pairings);
    renderTastingNotes(formatTastingNotes(wine.tasting_notes));
}

async function loadWine() {
    if (!wineId) {
        renderError("No wine selected", "Open a wine from the search page to view its details.");
        return;
    }

    try {
        const response = await fetch(`/wine/${encodeURIComponent(wineId)}`);

        if (!response.ok) {
            throw new Error("Wine not found");
        }

        const data = await response.json();
        renderWine(data.wine);
    }
    catch (error) {
        console.error(error);
        renderError("Wine not found", "This bottle could not be loaded from the database.");
    }
}

loadWine();
