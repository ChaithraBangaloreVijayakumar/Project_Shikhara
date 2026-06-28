// map.js — Leaflet map initialisation and marker management

let map = null;
let markers = {};          // temple id → Leaflet marker
let activeMarkerId = null; // currently highlighted marker

const DEFAULT_CENTER = [51.1657, 10.4515]; // centre of Germany
const DEFAULT_ZOOM   = 6;

// Marker icons
const defaultIcon = L.divIcon({
    className: '',
    html: `<div style="
        font-size: 20px;
        line-height: 1;
        filter: drop-shadow(0 1px 2px rgba(0,0,0,0.3));
        cursor: pointer;
    ">🛕</div>`,
    iconSize:   [24, 24],
    iconAnchor: [12, 12],
});

const activeIcon = L.divIcon({
    className: '',
    html: `<div style="
        font-size: 32px;
        line-height: 1;
        filter: drop-shadow(0 2px 6px rgba(0,0,0,0.5)) sepia(1) saturate(5) hue-rotate(-30deg);
        cursor: pointer;
    ">🛕</div>`,
    iconSize:   [36, 36],
    iconAnchor: [18, 18],
});


function initMap(containerId = 'map') {
    map = L.map(containerId, {
        center:     DEFAULT_CENTER,
        zoom:       DEFAULT_ZOOM,
        zoomControl: true,
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 18,
    }).addTo(map);

    return map;
}


function addMarkers(temples, onMarkerClick) {
    // Clear existing markers
    Object.values(markers).forEach(m => map.removeLayer(m));
    markers = {};

    temples.forEach(temple => {
        if (!temple.location_latitude || !temple.location_longitude) return;

        const marker = L.marker(
            [temple.location_latitude, temple.location_longitude],
            { icon: defaultIcon }
        ).addTo(map);

        marker.bindTooltip(temple.name, {
            permanent:  false,
            direction:  'top',
            offset:     [0, -8],
        });

        marker.on('click', () => {
            setActiveMarker(temple.id);
            onMarkerClick(temple.id);
        });

        markers[temple.id] = marker;
    });
}


function setActiveMarker(templeId, pan = false) {
    // Reset previous active marker
    if (activeMarkerId && markers[activeMarkerId]) {
        markers[activeMarkerId].setIcon(defaultIcon);
    }

    // Set new active marker
    if (templeId && markers[templeId]) {
        markers[templeId].setIcon(activeIcon);
        if (pan) map.setView(markers[templeId].getLatLng(), 10, { animate: true });
        activeMarkerId = templeId;
    } else {
        activeMarkerId = null;
    }
}


function resetActiveMarker() {
    if (activeMarkerId && markers[activeMarkerId]) {
        markers[activeMarkerId].setIcon(defaultIcon);
    }
    activeMarkerId = null;
}


function fitMapToMarkers() {
    const validMarkers = Object.values(markers);
    if (validMarkers.length === 0) return;
    const group = L.featureGroup(validMarkers);
    map.fitBounds(group.getBounds().pad(0.1), { maxZoom: 10 });
}