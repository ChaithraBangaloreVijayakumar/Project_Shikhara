// by-city.js — orchestrates the By City page

let currentPage    = 1;
const PAGE_SIZE    = 5;
let allMapTemples  = [];
let totalTemples   = 0;
let selectedCity   = null;

document.addEventListener('DOMContentLoaded', async () => {
    initMap('map');
    await Promise.all([loadCityTiles(), loadAllTemples()]);
    await loadPage(1);
});


// ── City tiles ────────────────────────────────────────────────────────────────

async function loadCityTiles() {
    try {
        const cities = await fetchCities();
        renderCityTiles(cities);
    } catch (e) {
        console.error('Failed to load cities:', e);
    }
}

function renderCityTiles(cities) {
    const container = document.getElementById('city-tiles');
    container.innerHTML = cities.map(c => `
        <div class="tile" data-city="${c.city}" onclick="selectCity('${c.city.replace(/'/g, "\\'")}')">
            <span>${c.city}</span>
            <span class="tile-count">${c.temple_count}</span>
        </div>
    `).join('');
}

function selectCity(city) {
    if (selectedCity === city) {
        // Deselect — show all
        selectedCity = null;
        document.querySelectorAll('.tile').forEach(t => t.classList.remove('active'));
        document.getElementById('table-heading').textContent = 'All Temples in Germany';
        loadAllTemples();
        loadPage(1);
        fitMapToMarkers();
        return;
    }

    selectedCity = city;
    document.querySelectorAll('.tile').forEach(t => t.classList.remove('active'));
    document.querySelector(`.tile[data-city="${city}"]`)?.classList.add('active');
    document.getElementById('table-heading').textContent = `Temples in ${city}`;
    loadFilteredTemples(city);
    loadPage(1, city);
}


// ── Temple loading ────────────────────────────────────────────────────────────

async function loadAllTemples() {
    try {
        const data = await fetchTemples({ page: 1, page_size: 100 });
        allMapTemples = data.data;
        totalTemples  = data.total;
        addMarkers(allMapTemples, onMarkerClick);
        fitMapToMarkers();
    } catch (e) {
        console.error('Failed to load temples:', e);
    }
}

async function loadFilteredTemples(city) {
    try {
        const data = await fetchTemples({ page: 1, page_size: 100, city });
        allMapTemples = data.data;
        totalTemples  = data.total;
        addMarkers(allMapTemples, onMarkerClick);

        // Zoom map to city temples
        fitMapToMarkers();
    } catch (e) {
        console.error('Failed to load filtered temples:', e);
    }
}


async function loadPage(page, city = selectedCity) {
    currentPage = page;
    closeSidebar();
    try {
        const params = { page, page_size: PAGE_SIZE };
        if (city) params.city = city;

        const data = await fetchTemples(params);
        const pageOffset = (page - 1) * PAGE_SIZE;
        renderTable(data.data, onRowClick, pageOffset);
        renderPagination(data.total, page, PAGE_SIZE, (p) => loadPage(p, city));
        updateTempleCount(data.total, !!city);
    } catch (e) {
        document.getElementById('temple-tbody').innerHTML =
            '<tr><td colspan="6" class="error">Failed to load temples.</td></tr>';
    }
}


// ── Row and marker interaction ────────────────────────────────────────────────

function onRowClick(templeId) {
    closeSidebar();
    setActiveRow(templeId);
    setActiveMarker(templeId, true);
}

async function onMarkerClick(templeId) {
    setActiveMarker(templeId);

    const templeIndex = allMapTemples.findIndex(t => t.id === templeId);
    if (templeIndex !== -1) {
        const targetPage = Math.ceil((templeIndex + 1) / PAGE_SIZE);
        if (targetPage !== currentPage) {
            currentPage = targetPage;
            try {
                const params = { page: targetPage, page_size: PAGE_SIZE };
                if (selectedCity) params.city = selectedCity;
                const data = await fetchTemples(params);
                const pageOffset = (targetPage - 1) * PAGE_SIZE;
                renderTable(data.data, onRowClick, pageOffset);
                renderPagination(data.total, targetPage, PAGE_SIZE, (p) => loadPage(p, selectedCity));
                updateTempleCount(data.total, !!selectedCity);
            } catch (e) {
                console.error('Failed to load page:', e);
            }
        }
        setActiveRow(templeId);
    }

    try {
        const temple = await fetchTemple(templeId);
        openSidebar(temple);
    } catch (e) {
        console.error('Failed to load temple details:', e);
    }
}