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
const pairingsEl = document.querySelector("[data-wine-pairings]");
const imageEl = document.querySelector("[data-wine-image]");
const backButton = document.querySelector("[data-back-button]");
const homeButton = document.querySelector("[data-home-button]");

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
    const notes = String(value ?? "")
        .split("|")
        .map((note) => note.trim())
        .filter(Boolean);

    if (notes.length === 0) {
        return "No tasting notes saved yet.";
    }

    return notes.map(capitalize).join(", ");
}

function renderPairings(pairings) {
    pairingsEl.innerHTML = "";

    if (!Array.isArray(pairings) || pairings.length === 0) {
        const empty = document.createElement("span");
        empty.className = "detail-empty";
        empty.textContent = "No pairings saved yet.";
        pairingsEl.appendChild(empty);
        return;
    }

    pairings.forEach((pairing) => {
        const tag = document.createElement("span");
        tag.className = "pairing-tag";
        tag.textContent = capitalize(pairing);
        pairingsEl.appendChild(tag);
    });
}

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
    tastingNotesEl.textContent = "No tasting notes available.";
    renderImage({});
    renderPairings([]);
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
    tastingNotesEl.textContent = formatTastingNotes(wine.tasting_notes);
    renderImage(wine);
    renderPairings(wine.pairings);
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
        console.log("Wine data:", data);
        renderWine(data.wine);
    }
    catch (error) {
        console.error(error);
        renderError("Wine not found", "This bottle could not be loaded from the database.");
    }
}

loadWine();
