// by-state.js — orchestrates the By State page

let currentPage   = 1;
const PAGE_SIZE   = 5;
let allMapTemples = [];
let totalTemples  = 0;
let selectedState = null;

document.addEventListener('DOMContentLoaded', async () => {
    initMap('map');
    await Promise.all([loadStateTiles(), loadAllTemples()]);
    await loadPage(1);
});


// ── State tiles ───────────────────────────────────────────────────────────────

async function loadStateTiles() {
    try {
        const states = await fetchStates();
        renderStateTiles(states);
    } catch (e) {
        console.error('Failed to load states:', e);
    }
}

function renderStateTiles(states) {
    const container = document.getElementById('state-tiles');
    container.innerHTML = states.map(s => `
        <div class="tile" data-state="${s.state}" onclick="selectState('${s.state.replace(/'/g, "\\'")}')">
            <span>${s.state}</span>
            <span class="tile-count">${s.temple_count}</span>
        </div>
    `).join('');
}

function selectState(state) {
    if (selectedState === state) {
        // Deselect — show all
        selectedState = null;
        document.querySelectorAll('.tile').forEach(t => t.classList.remove('active'));
        document.getElementById('table-heading').textContent = 'All Temples in Germany';
        loadAllTemples();
        loadPage(1);
        fitMapToMarkers();
        return;
    }

    selectedState = state;
    document.querySelectorAll('.tile').forEach(t => t.classList.remove('active'));
    document.querySelector(`.tile[data-state="${state}"]`)?.classList.add('active');
    document.getElementById('table-heading').textContent = `Temples in ${state}`;
    loadFilteredTemples(state);
    loadPage(1, state);
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

async function loadFilteredTemples(state) {
    try {
        const data = await fetchTemples({ page: 1, page_size: 100, state });
        allMapTemples = data.data;
        totalTemples  = data.total;
        addMarkers(allMapTemples, onMarkerClick);
        fitMapToMarkers();
    } catch (e) {
        console.error('Failed to load filtered temples:', e);
    }
}

async function loadPage(page, state = selectedState) {
    currentPage = page;
    closeSidebar();
    try {
        const params = { page, page_size: PAGE_SIZE };
        if (state) params.state = state;

        const data = await fetchTemples(params);
        const pageOffset = (page - 1) * PAGE_SIZE;
        renderTable(data.data, onRowClick, pageOffset);
        renderPagination(data.total, page, PAGE_SIZE, (p) => loadPage(p, state));
        updateTempleCount(data.total, !!state);
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
                if (selectedState) params.state = selectedState;
                const data = await fetchTemples(params);
                const pageOffset = (targetPage - 1) * PAGE_SIZE;
                renderTable(data.data, onRowClick, pageOffset);
                renderPagination(data.total, targetPage, PAGE_SIZE, (p) => loadPage(p, selectedState));
                updateTempleCount(data.total, !!selectedState);
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