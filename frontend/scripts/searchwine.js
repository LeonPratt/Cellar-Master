const API_URL = "/wines";

const wineList = document.querySelector(".wine-list");
const searchBox = document.querySelector(".search-box");
const inCellarOnly = document.querySelector(".in-cellar-only");
const homeButton = document.querySelector(".nav-btn");
const logo = document.getElementById("home");
home.addEventListener("click", () => {
    window.location.href = "/";
});
let wines = [];

homeButton.addEventListener("click", () => {
    window.location.href = "/";
});

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function capitalize(text) {
    return String(text ?? "")
        .split(" ")
        .filter(Boolean)
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" ");
}

function renderMessage(title, detail = "") {
    wineList.innerHTML = `
        <div class="wine-card">
            <div class="wine-info">
                <div class="wine-name">${escapeHtml(title)}</div>
                ${detail ? `<div class="wine-details">${escapeHtml(detail)}</div>` : ""}
            </div>
        </div>
    `;
}

async function fetchWines() {
    try {
        const response = await fetch(API_URL);

        if (!response.ok) {
            throw new Error("Failed to fetch wines");
        }

        const data = await response.json();
        wines = data.wines || [];
        renderWines(wines);
    }
    catch (error) {
        console.error(error);
        renderMessage("Failed to load wines", "Please check server connection.");
    }
}

function renderWines(wineArray) {
    wineList.innerHTML = "";

    if (wineArray.length === 0) {
        renderMessage("No wines found");
        return;
    }

    wineArray.forEach((wine) => {
        if (inCellarOnly.checked && (!wine.quantity || wine.quantity <= 0)) {
            return;
        }
        const grapes = Array.isArray(wine.grapes) && wine.grapes.length > 0
            ? wine.grapes.map(capitalize).join(" / ")
            : "Grape unknown";

        const wineCard = document.createElement("div");
        wineCard.className = "wine-card";

        wineCard.innerHTML = `
            <div class="wine-info">
                <div class="wine-name">${escapeHtml(wine.name)}</div>
                <div class="wine-details">
                    ${escapeHtml(grapes)}
                    &bull;
                    ${escapeHtml(wine.region || "Region unknown")}
                    &bull;
                    ${escapeHtml(wine.year || "Year unknown")}
                </div>
            </div>

            <div class="wine-actions">
                <button class="action-btn view-btn" type="button">View</button>
                <button class="action-btn delete-btn" type="button">Remove</button>
            </div>
        `;

        wineCard.querySelector(".view-btn").addEventListener("click", () => {
            window.location.href = `/view?wineid=${encodeURIComponent(wine.wineid)}`;
        });

        wineCard.querySelector(".delete-btn").addEventListener("click", () => {
            removeWine(wine.wineid);
        });

        wineList.appendChild(wineCard);
    });
}

function searchWines() {
    const query = searchBox.value.toLowerCase().trim();

    const filteredWines = wines.filter((wine) => {
        const grapes = Array.isArray(wine.grapes) ? wine.grapes : [];

        return (
            String(wine.name ?? "").toLowerCase().includes(query) ||
            grapes.some((grape) => String(grape).toLowerCase().includes(query)) ||
            String(wine.region ?? "").toLowerCase().includes(query) ||
            String(wine.year ?? "").includes(query)
        );
    });

    renderWines(filteredWines);
}

async function removeWine(wineId) {
    try {
        console.log(`Removing wine with ID: ${wineId}`);
        const response = await fetch(
            `${API_URL}/${encodeURIComponent(parseInt(wineId))}`,
            { method: "DELETE" }
        );
        console.log(response);
        if (!response.ok) {
            throw new Error("Failed to remove wine");
        }

        wines = wines.filter((wine) => wine.wineid !== wineId);
        renderWines(wines);
    }
    catch (error) {
        console.error(error);
        alert("Failed to remove wine");
    }
}
searchBox.addEventListener("input", searchWines);
inCellarOnly.addEventListener("change", searchWines);

fetchWines();
