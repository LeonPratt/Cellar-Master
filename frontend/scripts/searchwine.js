const API_URL = "/wines";

const wineList = document.querySelector(".wine-list");
const searchBox = document.querySelector(".search-box");
const inCellarOnly = document.querySelector(".in-cellar-only");
const sortControl = document.querySelector(".wine-sort");
const sortSelect = document.querySelector(".wine-sort-select");
const sortMenu = document.querySelector(".wine-sort-menu");
const sortLabel = document.querySelector("[data-sort-label]");
const sortOptions = document.querySelectorAll("[data-sort-value]");
const sortDirectionButton = document.querySelector(".sort-direction-btn");
const homeButton = document.querySelector(".nav-btn");
const logo = document.getElementById("home");
const currentCellarBox = document.querySelector(".current-cellar");
const wineDeleteConfirmation = document.querySelector("[data-wine-delete-confirmation]");
const wineDeleteConfirmationMessage = document.querySelector("[data-wine-delete-confirmation-message]");
const wineDeleteCancelButton = document.querySelector("[data-wine-delete-cancel]");
const wineDeleteConfirmButton = document.querySelector("[data-wine-delete-confirm]");

logo.addEventListener("click", () => {
    window.location.href = "/home";
});
let wines = [];
let sortDirection = "asc";
let sortField = "name";
let winePendingDeletion = null;

homeButton.addEventListener("click", () => {
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

async function fetchWines(searchterm = "", inCellarOnlyFlag = false) {
    const cellar = loadCurrentCellar();
    if (!cellar) {
        window.location.href = "/";
        return;
    }

    try {
        const response = await fetch(`${API_URL}?q=${encodeURIComponent(searchterm)}&in_cellar_only=${inCellarOnlyFlag ? 1 : 0}&c=${encodeURIComponent(cellar)}`,
        {method: "GET"
        });

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
    const sortedWines = sortWines(wineArray);
    console.log("Rendering wines:", sortedWines);
    if (sortedWines.length === 0) {
        renderMessage("No wines found");
        return;
    }

    sortedWines.forEach((wine) => {
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
                ${wine.quantity >0 ? '<button class="action-btn delete-btn" type="button">Remove wine</button>': '<div class="out-of-stock-label">Not in cellar</div>'}
            </div>
        `;

        wineCard.querySelector(".view-btn").addEventListener("click", () => {
            window.location.href = `/view?wineid=${encodeURIComponent(wine.wineid)}&c=${encodeURIComponent(loadCurrentCellar())}`;
        });
        if (wine.quantity == 0) {
            wineCard.style.backgroundColor = "#c0c0c0";
        }
        else{
        wineCard.querySelector(".delete-btn").addEventListener("click", () => {
            showWineDeleteConfirmation(wine);
        });
        }


        wineList.appendChild(wineCard);
    });
}

function sortWines(wineArray) {
    const direction = sortDirection === "asc" ? 1 : -1;

    return wineArray
        .map((wine, index) => ({ wine, index }))
        .sort((first, second) => {
            const firstValue = first.wine[sortField];
            const secondValue = second.wine[sortField];

            if (sortField === "name") {
                const comparison = String(firstValue || "").localeCompare(String(secondValue || ""), undefined, {
                    sensitivity: "base",
                    numeric: true,
                });
                return comparison * direction || first.index - second.index;
            }

            const firstNumber = Number.parseInt(firstValue, 10);
            const secondNumber = Number.parseInt(secondValue, 10);
            const firstIsUnknown = Number.isNaN(firstNumber);
            const secondIsUnknown = Number.isNaN(secondNumber);

            if (firstIsUnknown || secondIsUnknown) {
                if (firstIsUnknown && secondIsUnknown) return first.index - second.index;
                return firstIsUnknown ? 1 : -1;
            }

            return (firstNumber - secondNumber) * direction || first.index - second.index;
        })
        .map(({ wine }) => wine);
}

function toggleSortDirection() {
    sortDirection = sortDirection === "asc" ? "desc" : "asc";
    const isAscending = sortDirection === "asc";
    sortDirectionButton.textContent = isAscending ? "Ascending" : "Descending";
    sortDirectionButton.setAttribute("aria-label", `Sort ${sortDirection}`);
    renderWines(wines);
}

function closeSortMenu() {
    sortMenu.hidden = true;
    sortSelect.setAttribute("aria-expanded", "false");
}

function applySelectedSort(event) {
    const option = event.currentTarget;
    sortField = option.dataset.sortValue;
    sortLabel.textContent = option.textContent;
    sortOptions.forEach((sortOption) => {
        sortOption.setAttribute("aria-selected", String(sortOption === option));
    });
    closeSortMenu();
    renderWines(wines);
}

async function searchWines() {
    const query = searchBox.value.toLowerCase().trim();
    filteredwines = await fetchWines(query, inCellarOnly.checked);
}

function showWineDeleteConfirmation(wine) {
    winePendingDeletion = wine;
    wineDeleteConfirmationMessage.textContent = `Are you sure you want to remove ${wine.name} from this cellar?`;
    wineDeleteConfirmation.style.visibility = "visible";
    wineDeleteConfirmButton.focus();
}

function hideWineDeleteConfirmation() {
    wineDeleteConfirmation.style.visibility = "hidden";
    winePendingDeletion = null;
}

async function removeWine(wine) {
    const cellar = loadCurrentCellar();
    if (!cellar) {
        window.location.href = "/";
        return;
    }

    try {
        console.log(`Removing wine with ID: ${wine.wineid}`);
        const response = await fetch(
            `${API_URL}/${encodeURIComponent(parseInt(wine.wineid))}?c=${encodeURIComponent(cellar)}`,
            { method: "DELETE" }
        );
        console.log(response);
        if (!response.ok) {
            throw new Error("Failed to remove wine");
        }

        console.log(wine);
        wine.quantity = 0;
        renderWines(wines);


    }
    catch (error) {
        console.error(error);
        alert("Failed to remove wine");
    }
}
searchBox.addEventListener("input", searchWines);
inCellarOnly.addEventListener("change", searchWines);
sortSelect.addEventListener("click", () => {
    const isOpen = !sortMenu.hidden;
    sortMenu.hidden = isOpen;
    sortSelect.setAttribute("aria-expanded", String(!isOpen));
});
sortOptions.forEach((option) => option.addEventListener("click", applySelectedSort));
document.addEventListener("click", (event) => {
    if (!sortControl.contains(event.target)) {
        closeSortMenu();
    }
});
document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        closeSortMenu();
    }
    if (event.key === "Escape" && wineDeleteConfirmation.style.visibility === "visible") {
        hideWineDeleteConfirmation();
    }
});
sortDirectionButton.addEventListener("click", toggleSortDirection);

wineDeleteCancelButton.addEventListener("click", hideWineDeleteConfirmation);
wineDeleteConfirmButton.addEventListener("click", async () => {
    if (!winePendingDeletion) {
        return;
    }

    const wine = winePendingDeletion;
    hideWineDeleteConfirmation();
    await removeWine(wine);
});
wineDeleteConfirmation.addEventListener("click", (event) => {
    if (event.target === wineDeleteConfirmation) {
        hideWineDeleteConfirmation();
    }
});

fetchWines();
