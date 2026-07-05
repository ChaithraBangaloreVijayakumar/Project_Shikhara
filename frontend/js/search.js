// search.js — search box logic for explore pages

document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('search-input');
    const searchBtn   = document.getElementById('search-btn');

    if (!searchInput || !searchBtn) return;

    // Check if redirected from home page with a search term
    const savedSearch = sessionStorage.getItem('shikhara_search');
    if (savedSearch) {
        searchInput.value = savedSearch;
        sessionStorage.removeItem('shikhara_search');
        triggerSearch(savedSearch);
    }

    function triggerSearch(query) {
        if (typeof onSearch === 'function') {
            onSearch(query);
        }
    }

    searchBtn.addEventListener('click', () => {
        const q = searchInput.value.trim();
        if (q) triggerSearch(q);
        else if (typeof onSearch === 'function') onSearch(''); // clear search
    });

    searchInput.addEventListener('keydown', e => {
        if (e.key === 'Enter') {
            const q = searchInput.value.trim();
            triggerSearch(q);
        }
    });
});