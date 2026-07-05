// explore-all.js — orchestrates the Explore All page

let currentPage   = 1;
const PAGE_SIZE   = 5;
let allMapTemples = [];
let totalTemples  = 0;
let currentSearch = '';

document.addEventListener('DOMContentLoaded', async () => {
    initMap('map');
    await loadAllMapTemples();
    await loadPage(1);
});


async function loadAllMapTemples() {
    try {
        const data = await fetchTemples({ page: 1, page_size: 100 });
        allMapTemples = data.data;
        totalTemples  = data.total;
        addMarkers(allMapTemples, onMarkerClick);
        fitMapToMarkers();
    } catch (e) {
        console.error('Failed to load map temples:', e);
    }
}


async function loadPage(page) {
    currentPage = page;
    closeSidebar();
    try {
        let data;
        if (currentSearch) {
            data = await fetchSearch(currentSearch, page, PAGE_SIZE);
        } else {
            data = await fetchTemples({ page, page_size: PAGE_SIZE });
        }
        const pageOffset = (page - 1) * PAGE_SIZE;
        renderTable(data.data, onRowClick, pageOffset);
        renderPagination(data.total, page, PAGE_SIZE, loadPage);
        updateTempleCount(data.total, !!currentSearch);
    } catch (e) {
        document.getElementById('temple-tbody').innerHTML =
            '<tr><td colspan="6" class="error">Failed to load temples.</td></tr>';
    }
}


async function onSearch(query) {
    currentSearch = query;
    if (query) {
        // Update map with search results
        try {
            const data = await fetchSearch(query, 1, 100);
            allMapTemples = data.data;
            addMarkers(allMapTemples, onMarkerClick);
            fitMapToMarkers();
        } catch (e) {
            console.error('Search failed:', e);
        }
    } else {
        // Reset to all temples
        await loadAllMapTemples();
    }
    await loadPage(1);
}


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
                let data;
                if (currentSearch) {
                    data = await fetchSearch(currentSearch, targetPage, PAGE_SIZE);
                } else {
                    data = await fetchTemples({ page: targetPage, page_size: PAGE_SIZE });
                }
                const pageOffset = (targetPage - 1) * PAGE_SIZE;
                renderTable(data.data, onRowClick, pageOffset);
                renderPagination(data.total, targetPage, PAGE_SIZE, loadPage);
                updateTempleCount(data.total, !!currentSearch);
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