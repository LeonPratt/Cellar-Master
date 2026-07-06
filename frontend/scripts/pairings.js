const API_URL = "/pairing-wines";

const wineList = document.querySelector(".wine-list");
const searchBox = document.querySelector(".search-box");
const searchButton = document.querySelector(".search-btn");
const summary = document.querySelector(".pairing-summary");
const homeButton = document.querySelector(".nav-btn");
const logo = document.getElementById("home");
homeButton.addEventListener("click", () => {
    window.location.href = "/";
});

logo.addEventListener("click", () => {
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
                <div class="wine-name">
                    ${escapeHtml(title)}
                </div>
                ${detail ? `
                    <div class="wine-details">
                        ${escapeHtml(detail)}
                    </div>
                ` : ""}
            </div>
        </div>
    `;
}

function renderWines(wines, query) {
    wineList.innerHTML = "";

    if (wines.length === 0) {
        summary.textContent = `No cellar wines found for "${query}".`;
        renderMessage("No pairings found", "Try a broader food, such as beef, fish, chicken or cheese.");
        return;
    }

    summary.textContent = `${wines.length} wine${wines.length === 1 ? "" : "s"} found for "${query}".`;

    wines.forEach((wine) => {
        const grapeList = Array.isArray(wine.grapes) ? wine.grapes : [];
        const matchedPairingList = Array.isArray(wine.matched_pairings) ? wine.matched_pairings : [];

        const grapes = grapeList.length > 0
            ? grapeList.map(capitalize).join(" / ")
            : "Grape unknown";

        const matchedPairings = matchedPairingList.length > 0
            ? matchedPairingList
            : [query];

        const pairingTags = matchedPairings
            .map((pairing) => `<span class="pairing-tag">${escapeHtml(capitalize(pairing))}</span>`)
            .join("");

        const wineCard = document.createElement("div");
        wineCard.className = "wine-card";
        wineCard.innerHTML = `
            <div class="wine-info">
                <div class="wine-name">
                    ${escapeHtml(wine.name)}
                </div>

                <div class="wine-details">
                    ${escapeHtml(grapes)}
                    &bull;
                    ${escapeHtml(wine.region || "Region unknown")}
                    &bull;
                    ${escapeHtml(wine.year || "Year unknown")}
                </div>

                <div class="pairing-tags">
                    ${pairingTags}
                </div>
            </div>

            <div class="quantity-pill">
                ${escapeHtml(wine.quantity)} in cellar
            </div>
        `;

        wineList.appendChild(wineCard);
    });
}

async function searchPairings() {
    const query = searchBox.value.trim();

    if (query === "") {
        summary.textContent = "Search for a food, such as steak, lamb, salmon or cheese.";
        wineList.innerHTML = "";
        return;
    }

    summary.textContent = `Searching for "${query}"...`;
    renderMessage("Searching pairings");

    try {
        const response = await fetch(`${API_URL}?q=${encodeURIComponent(query)}`);

        if (!response.ok) {
            throw new Error("Failed to fetch pairing wines");
        }

        const data = await response.json();
        renderWines(data.wines || [], query);
    }
    catch (error) {
        console.error(error);
        summary.textContent = "Pairing search failed.";
        renderMessage("Failed to load pairings", "Please check the server connection.");
    }
}

searchButton.addEventListener("click", searchPairings);

searchBox.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        searchPairings();
    }
});
