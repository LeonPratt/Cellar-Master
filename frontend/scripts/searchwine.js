
const API_URL = "/wines";

const wineList = document.querySelector(".wine-list");
const searchBox = document.querySelector(".search-box");
const searchButton = document.querySelector(".search-btn");


let homeButton = document.querySelector(".nav-btn");

homeButton.addEventListener("click", () => {
    window.location.href = "/";
})


let wines = [];

async function fetchWines() {

    try {

        const response = await fetch(API_URL);

        if (!response.ok) {
            throw new Error("Failed to fetch wines");
        }

        const data = await response.json();
        console.log(data);
        wines = data.wines;


        renderWines(wines);

    }
    catch (error) {

        console.error(error);

        wineList.innerHTML = `
            <div class="wine-card">
                <div class="wine-info">
                    <div class="wine-name">
                        Failed to load wines
                    </div>

                    <div class="wine-details">
                        Please check server connection
                    </div>
                </div>
            </div>
        `;
    }
}


function renderWines(wineArray) {

    wineList.innerHTML = "";

    if (wineArray.length === 0) {

        wineList.innerHTML = `
            <div class="wine-card">
                <div class="wine-info">
                    <div class="wine-name">
                        No wines found
                    </div>
                </div>
            </div>
        `;

        return;
    }

    wineArray.forEach((wine) => {

        const wineCard = document.createElement("div");

        wineCard.className = "wine-card";

        wineCard.innerHTML = `
            <div class="wine-info">

                <div class="wine-name">
                    ${wine.name}
                </div>

                <div class="wine-details">
                    ${capitalize(wine.grapes[0])}
                    •
                    ${wine.region}
                    •
                    ${wine.year}
                </div>

            </div>

            <div class="wine-actions">

                <button class="action-btn view-btn">
                    View
                </button>

                <button class="action-btn delete-btn">
                    Remove
                </button>

            </div>
        `;

        const viewButton = wineCard.querySelector(".view-btn");

        viewButton.addEventListener("click", () => {

            console.log("Viewing wine:", wine);

            // Example:
            // window.location.href = `/wine.html?id=${wine.id}`;
        });


        const removeButton = wineCard.querySelector(".delete-btn");

        removeButton.addEventListener("click", () => {

            removeWine(wine.name);
        });

        wineList.appendChild(wineCard);

    });
}

function searchWines() {

    const query = searchBox.value.toLowerCase().trim();

    const filteredWines = wines.filter((wine) => {

        return (

            wine.name.toLowerCase().includes(query) ||

            wine.main_grape.toLowerCase().includes(query) ||

            wine.region.toLowerCase().includes(query) ||

            wine.year.toString().includes(query)

        );
    });

    renderWines(filteredWines);
}

async function removeWine(wineName) {

    try {

        const response = await fetch(

            `${API_URL}/${encodeURIComponent(wineName)}`,

            {
                method: "DELETE"
            }
        );

        if (!response.ok) {
            throw new Error("Failed to remove wine");
        }

        wines = wines.filter((wine) => wine.name !== wineName);

        renderWines(wines);

    }
    catch (error) {

        console.error(error);

        alert("Failed to remove wine");
    }
}

function capitalize(text) {

    return text
        .split(" ")
        .map(word =>
            word.charAt(0).toUpperCase() +
            word.slice(1)
        )
        .join(" ");
}

searchButton.addEventListener("click", searchWines);

searchBox.addEventListener("input", searchWines);

fetchWines();