// ===== GLOBAL STATE =====
// Application-wide state variables shared across all pages and components.

let map = null;                      // Leaflet map instance (initialized when user navigates to map page)
let markerGroup = null;              // Leaflet marker cluster group for displaying property locations
let currentUser = null;              // Logged-in user object (null if not authenticated)
let currentSectionsPage = 1;         // Current page number in sections table pagination
let currentSectionsPages = 1;        // Total number of pages in sections table
let currentOwnersPage = 1;           // Current page number in owners table pagination
let currentOwnersPages = 1;          // Total number of pages in owners table
let searchTimer = null;              // Timer ID for debouncing search inputs
let parishesLoaded = false;          // Flag to avoid reloading parishes dropdown

// ===== LOGIN =====

/**
 * Handles login form submission.
 * Validates password against single password gate.
 * Called when user clicks "Sign In" button.
 */
async function handleLogin(e) {
    e.preventDefault();
    const password = document.getElementById('password-input').value;
    const errorEl = document.getElementById('login-error');
    errorEl.textContent = '';
    errorEl.classList.remove('show');

    try {
        const resp = await fetch('/api/auth/login', {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password })
        });
        if (resp.ok) {
            currentUser = await resp.json();
            showApp();
            setPage('home');
            loadDashboard();
        } else {
            const data = await resp.json().catch(() => ({}));
            errorEl.textContent = data.error || 'Invalid password';
            errorEl.classList.add('show');
        }
    } catch (err) {
        errorEl.textContent = 'Connection error';
        errorEl.classList.add('show');
    }
}

/**
 * Shows the login overlay and hides the main app.
 * Called when session expires (401) or during initial page load before authentication.
 */
function showLogin() {
    document.getElementById('login-overlay').classList.remove('hidden');
    document.getElementById('app-container').classList.add('hidden');
}

/**
 * Hides the login overlay and shows the main app.
 * Called after successful login or when session is still valid.
 */
function showApp() {
    document.getElementById('login-overlay').classList.add('hidden');
    document.getElementById('app-container').classList.remove('hidden');
}

// ===== PAGE NAVIGATION =====

/**
 * Navigates to a specific page in the app.
 * Updates the active nav button, hides all pages, shows the selected page,
 * and triggers page-specific data loading (dashboard, sections, etc.).
 * Called when user clicks nav buttons or during app initialization.
 *
 * @param {string} pageName - The page to navigate to: 'home', 'sections', 'owners', 'pipeline', 'map', 'documents', 'activity'
 */
function setPage(pageName) {
    // Close the contact side panel when navigating to a different page
    if (typeof closeOwnerPanel === 'function') closeOwnerPanel();
    document.querySelectorAll('.nl button').forEach(btn => {
        btn.classList.toggle('act', btn.dataset.page === pageName);
    });
    document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
    const pageEl = document.getElementById(`page-${pageName}`);
    if (pageEl) {
        pageEl.classList.add('active');
        if (pageName === 'home') loadDashboard();
        else if (pageName === 'sections') { loadParishes(); loadOperators(); loadSections(); }
        else if (pageName === 'owners') { loadOwnerStates(); loadOwners(); }
        else if (pageName === 'pipeline') loadPipeline();
        else if (pageName === 'map') setTimeout(() => initMap(), 100);
        else if (pageName === 'documents') loadDocuments();
        else if (pageName === 'activity') loadActivities();
        else if (pageName === 'assistant') loadAssistant();
    }
}

// ===== GLOBAL SEARCH =====
let globalSearchTimer = null;

/**
 * Debounces the global search input — waits 300ms after user stops typing before searching.
 */
function debounceGlobalSearch() {
    clearTimeout(globalSearchTimer);
    const query = document.getElementById('global-search').value.trim();
    const resultsDiv = document.getElementById('global-search-results');
    if (query.length < 2) {
        resultsDiv.classList.add('hidden');
        return;
    }
    globalSearchTimer = setTimeout(() => runGlobalSearch(query), 300);
}

/**
 * Runs the global search against /api/search and displays results in a dropdown.
 * Shows contacts, sections, and deals in grouped sections.
 */
async function runGlobalSearch(query) {
    const resultsDiv = document.getElementById('global-search-results');
    const data = await apiCall(`/search?q=${encodeURIComponent(query)}`);
    if (!data) { resultsDiv.classList.add('hidden'); return; }

    let html = '';
    const owners = data.owners || [];
    const sections = data.sections || [];
    const deals = data.deals || [];

    if (owners.length === 0 && sections.length === 0 && deals.length === 0) {
        html = '<div style="padding:16px;color:var(--td);text-align:center;font-size:13px">No results found</div>';
    } else {
        if (owners.length > 0) {
            html += '<div style="padding:8px 12px;font-size:10px;text-transform:uppercase;letter-spacing:1px;color:var(--ac);font-weight:700;border-bottom:1px solid var(--b)">Contacts</div>';
            owners.slice(0, 8).forEach(o => {
                const loc = [o.city, o.state].filter(Boolean).join(', ');
                html += `<div style="padding:8px 12px;cursor:pointer;border-bottom:1px solid var(--b);font-size:13px" onclick="document.getElementById('global-search-results').classList.add('hidden');document.getElementById('global-search').value='';viewOwnerDetail(${o.owner_id})" onmouseover="this.style.background='var(--b)'" onmouseout="this.style.background=''">
                    <div style="font-weight:500;color:var(--t)">${esc(o.full_name)}</div>
                    <div style="font-size:11px;color:var(--td)">${esc(o.phone_1 || '')}${loc ? ' · ' + esc(loc) : ''}</div>
                </div>`;
            });
        }
        if (sections.length > 0) {
            html += '<div style="padding:8px 12px;font-size:10px;text-transform:uppercase;letter-spacing:1px;color:var(--g);font-weight:700;border-bottom:1px solid var(--b)">Sections</div>';
            sections.slice(0, 5).forEach(s => {
                html += `<div style="padding:8px 12px;cursor:pointer;border-bottom:1px solid var(--b);font-size:13px" onclick="document.getElementById('global-search-results').classList.add('hidden');document.getElementById('global-search').value='';viewSectionDetail(${s.section_id})" onmouseover="this.style.background='var(--b)'" onmouseout="this.style.background=''">
                    <div style="font-weight:500;color:var(--t)">${esc(s.display_name)}</div>
                    <div style="font-size:11px;color:var(--td)">${esc(s.parish_name || '')}${s.exit_price ? ' · ' + formatCurrency(s.exit_price) : ''}</div>
                </div>`;
            });
        }
        if (deals.length > 0) {
            html += '<div style="padding:8px 12px;font-size:10px;text-transform:uppercase;letter-spacing:1px;color:var(--y);font-weight:700;border-bottom:1px solid var(--b)">Deals</div>';
            deals.slice(0, 5).forEach(d => {
                html += `<div style="padding:8px 12px;cursor:pointer;border-bottom:1px solid var(--b);font-size:13px" onclick="document.getElementById('global-search-results').classList.add('hidden');document.getElementById('global-search').value=''" onmouseover="this.style.background='var(--b)'" onmouseout="this.style.background=''">
                    <div style="font-weight:500;color:var(--t)">${esc(d.title)}</div>
                    <div style="font-size:11px;color:var(--td)">${d.value ? formatCurrency(d.value) : ''}</div>
                </div>`;
            });
        }
    }

    resultsDiv.innerHTML = html;
    resultsDiv.classList.remove('hidden');
}

// Close search results when clicking outside
document.addEventListener('click', (e) => {
    const searchEl = document.getElementById('global-search');
    const resultsEl = document.getElementById('global-search-results');
    if (searchEl && resultsEl && !searchEl.contains(e.target) && !resultsEl.contains(e.target)) {
        resultsEl.classList.add('hidden');
    }
});

// ===== THEME TOGGLE =====

/**
 * Toggles between light and dark theme.
 * Updates the data-theme attribute on the root HTML element and persists the choice to localStorage.
 * Called when user clicks the theme toggle button.
 */
function toggleTheme() {
    const html = document.documentElement;
    const isDark = html.getAttribute('data-theme') !== 'light';
    html.setAttribute('data-theme', isDark ? 'light' : 'dark');
    localStorage.setItem('theme', isDark ? 'light' : 'dark');
}

// ===== APP INITIALIZATION =====

/**
 * Initializes the app on page load.
 * - Restores theme preference from localStorage
 * - Wires up login form and nav button event listeners
 * - Sets up debounced search inputs to avoid excessive API calls
 * - Checks if user has a valid session and shows either the app or login screen accordingly
 * Called automatically when page DOM is fully loaded.
 */
document.addEventListener('DOMContentLoaded', async () => {
    // Restore theme
    const theme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', theme === 'light' ? 'light' : '');

    // Setup login form
    document.getElementById('login-form').addEventListener('submit', handleLogin);

    // Setup nav buttons
    document.querySelectorAll('.nl button').forEach(btn => {
        btn.addEventListener('click', () => setPage(btn.dataset.page));
    });

    // Debounce search inputs
    const secSearch = document.getElementById('sections-search');
    if (secSearch) secSearch.removeAttribute('onkeyup');
    if (secSearch) secSearch.addEventListener('input', debounceSections);
    const ownSearch = document.getElementById('owners-search');
    if (ownSearch) ownSearch.removeAttribute('onkeyup');
    if (ownSearch) ownSearch.addEventListener('input', debounceOwners);

    // Delegate checkbox change events for bulk action bar
    document.addEventListener('change', (e) => {
        if (e.target.classList.contains('section-check') || e.target.classList.contains('owner-check')) {
            updateBulkBar();
        }
    });

    // Check session
    const me = await apiCall('/auth/me');
    if (me) {
        currentUser = me;
        showApp();
        setPage('home');
    } else {
        showLogin();
    }
});
