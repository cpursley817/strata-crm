/**
 * map.js
 * Powers the Interactive Map page
 *
 * This file contains:
 * - Map initialization with multiple base layers
 * - Marker clustering for 717K+ geocoded contacts
 * - State and classification filter controls
 * - Color-coded markers by classification type
 */

/**
 * initMap()
 * Initializes the Leaflet map with base layers and controls.
 * Loads Louisiana markers by default (most relevant to Haynesville basin).
 */
function initMap() {
    if (map) {
        map.invalidateSize();
        return;
    }

    // Center on Haynesville Basin, Louisiana
    map = L.map('map').setView([32.0, -93.5], 8);

    // Base layers
    const osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap', maxZoom: 19
    });
    const topo = L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenTopoMap', maxZoom: 17
    });
    const satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        attribution: '&copy; Esri', maxZoom: 19
    });

    osm.addTo(map);
    L.control.layers({'Street': osm, 'Topographic': topo, 'Satellite': satellite}).addTo(map);

    setTimeout(() => map.invalidateSize(), 200);

    // Load with UI default filters (Individual, Living, Louisiana)
    filterMap();
}

/**
 * loadMapMarkers(state, classification)
 * Loads geocoded contact markers from the lightweight /api/map/markers endpoint.
 * Renders as clustered, color-coded circle markers.
 */
async function loadMapMarkers(state, classification, deceased) {
    if (!map) return;

    // Build query params
    let url = '/map/markers?limit=50000';
    if (state) url += `&state=${encodeURIComponent(state)}`;
    if (classification) url += `&classification=${encodeURIComponent(classification)}`;
    if (deceased === 'alive') url += '&deceased=0';
    else if (deceased === 'deceased') url += '&deceased=1';

    // Show loading
    const countEl = document.getElementById('map-marker-count');
    if (countEl) countEl.textContent = 'Loading...';

    const data = await apiCall(url);
    if (!data) return;

    // Remove existing markers
    if (markerGroup) map.removeLayer(markerGroup);
    markerGroup = L.markerClusterGroup({
        maxClusterRadius: 50,
        spiderfyOnMaxZoom: true,
        showCoverageOnHover: false,
        chunkedLoading: true
    });

    let markerCount = 0;
    (data.markers || []).forEach(o => {
        const lat = parseFloat(o.latitude);
        const lng = parseFloat(o.longitude);
        if (!lat || !lng || isNaN(lat) || isNaN(lng)) return;

        const color = o.classification === 'Individual' ? '#5b9fff' :
                      o.classification === 'Trust' ? '#9b8ff5' :
                      o.classification === 'LLC' || o.classification === 'Corporation' || o.classification === 'Business' ? '#00B451' :
                      o.classification === 'Estate' ? '#e8c57a' : '#8892c8';

        const marker = L.circleMarker([lat, lng], {
            radius: 5, fillColor: color, color: '#fff',
            weight: 1, fillOpacity: 0.8
        }).bindPopup(`<strong style="cursor:pointer" onclick="viewOwnerDetail(${o.owner_id})">${esc(o.full_name)}</strong><br>
            ${o.classification ? classBadge(o.classification) : ''}
            ${o.contact_status ? '<br>' + statusBadge(o.contact_status) : ''}
            ${o.phone_1 ? '<br><a href="tel:' + o.phone_1 + '">' + esc(o.phone_1) + '</a>' : ''}
            <br>${[o.city, o.state].filter(Boolean).join(', ')}
            <br><a href="#" onclick="viewOwnerDetail(${o.owner_id});return false;" style="font-size:11px">View Profile</a>`);
        markerGroup.addLayer(marker);
        markerCount++;
    });

    map.addLayer(markerGroup);

    if (countEl) countEl.textContent = `${markerCount.toLocaleString()} contacts displayed`;

    // Fit bounds if we have markers
    if (markerCount > 0 && markerGroup.getBounds().isValid()) {
        map.fitBounds(markerGroup.getBounds(), { padding: [20, 20] });
    }
}

/**
 * filterMap()
 * Called when user changes the state or classification filter dropdowns
 */
function filterMap() {
    const state = document.getElementById('map-state-filter').value;
    const classification = document.getElementById('map-class-filter').value;
    const deceased = document.getElementById('map-deceased-filter')?.value || '';
    loadMapMarkers(state, classification, deceased);
}
