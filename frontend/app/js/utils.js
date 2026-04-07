// ===== SHARED UTILITIES =====
// These helper functions are used by multiple pages throughout the app.

/**
 * Generates an HTML badge for a property class.
 * Maps class names (Individual, Trust, Business, etc.) to styled span elements
 * with custom background and text colors. Returns empty string if class is invalid or '-'.
 */
function classBadge(c) {
    if (!c || c === '-') return '';
    const m = {
        'Individual': {bg:'rgba(0,100,255,.15)',color:'#7eb8ff'},
        'Trust': {bg:'rgba(101,93,198,.2)',color:'#b5aeff'},
        'Business': {bg:'rgba(0,180,81,.15)',color:'#00D460'},
        'Estate': {bg:'rgba(189,154,95,.2)',color:'#e8c57a'},
        'LLC': {bg:'rgba(0,180,81,.15)',color:'#00D460'},
        'Corporation': {bg:'rgba(0,180,81,.15)',color:'#00D460'}
    };
    const s = m[c] || {bg:'rgba(120,130,180,.15)',color:'#8892c8'};
    return `<span style="display:inline-block;padding:3px 8px;border-radius:4px;font-size:10px;font-weight:600;background:${s.bg};color:${s.color}">${c}</span>`;
}

/**
 * Generates an HTML badge for a contact status.
 * Maps status names (Not Contacted, Attempted, Reached, etc.) to styled span elements
 * with custom background and text colors. Returns empty string if status is invalid.
 */
function statusBadge(st) {
    if (!st) return '';
    const m = {
        'Not Contacted': {bg:'rgba(120,130,180,.15)',color:'#8892c8'},
        'Attempted': {bg:'rgba(0,100,255,.15)',color:'#7eb8ff'},
        'Reached': {bg:'rgba(0,180,81,.15)',color:'#00D460'},
        'Follow Up Needed': {bg:'rgba(189,154,95,.2)',color:'#e8c57a'},
        'No Answer': {bg:'rgba(101,93,198,.2)',color:'#b5aeff'},
        'Bad Contact Info': {bg:'rgba(255,103,29,.15)',color:'#ff9060'}
    };
    const s = m[st] || {bg:'rgba(120,130,180,.15)',color:'#8892c8'};
    return `<span style="display:inline-block;padding:3px 8px;border-radius:4px;font-size:11px;font-weight:600;background:${s.bg};color:${s.color}">${st}</span>`;
}

/**
 * Escapes HTML special characters in a string.
 * Creates a temporary div element, sets the string as textContent, and returns the escaped innerHTML.
 * Prevents XSS vulnerabilities when displaying user-provided text.
 */
function esc(s) {
    const d = document.createElement('div');
    d.textContent = s || '';
    return d.innerHTML;
}

/**
 * Sanitizes a phone number for use in tel:/sms: href attributes.
 * Strips everything except digits and leading +.
 */
function sanitizePhone(p) {
    if (!p) return '';
    return p.replace(/[^\d+]/g, '');
}

/**
 * Sanitizes an email address for use in mailto: href attributes.
 * Strips characters that could break out of attribute context.
 */
function sanitizeEmail(e) {
    if (!e) return '';
    return e.replace(/["'<>&]/g, '');
}

/**
 * Formats a data_source tag into a human-readable label for source badges.
 */
function formatSourceName(src) {
    if (!src) return '';
    const map = {
        'ais_sql_dump': 'AIS',
        'ais_contact_directory': 'AIS Directory',
        'aethon': 'Aethon',
        'idicore': 'idiCore',
        'pipedrive': 'Pipedrive',
        'paydeck': 'Pay Deck',
        'expand_paydeck': 'Pay Deck'
    };
    return map[src.toLowerCase()] || src;
}

/**
 * Formats a numeric value as USD currency.
 * Uses the browser's Intl.NumberFormat API to format as currency with no decimal places.
 * Returns '-' if value is null, undefined, or falsy (except 0).
 */
/**
 * Formats a numeric ID into a human-readable display ID.
 * formatDisplayId(412, 'C') → 'ST-C-00412'
 * formatDisplayId(89, 'S') → 'ST-S-00089'
 * formatDisplayId(1, 'D') → 'ST-D-00001'
 */
function formatDisplayId(id, type) {
    if (!id) return '-';
    return `ST-${type}-${String(id).padStart(5, '0')}`;
}

function formatCurrency(value) {
    if (!value && value !== 0) return '-';
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(value);
}

/**
 * Toggles all checkboxes in sections table.
 */
function toggleAllSections(master) {
    document.querySelectorAll('.section-check').forEach(cb => cb.checked = master.checked);
    updateBulkBar();
}

/**
 * Toggles all checkboxes in owners table.
 */
function toggleAllOwners(master) {
    document.querySelectorAll('.owner-check').forEach(cb => cb.checked = master.checked);
    updateBulkBar();
}

/**
 * Updates the bulk action bar visibility based on checkbox selections.
 */
function updateBulkBar() {
    const checked = document.querySelectorAll('.section-check:checked, .owner-check:checked');
    const bar = document.getElementById('bulk-action-bar');
    if (checked.length > 0) {
        bar.classList.remove('hidden');
        document.getElementById('bulk-count').textContent = `${checked.length} selected`;
    } else {
        bar.classList.add('hidden');
    }
}

/**
 * Clears all checkbox selections and hides the bulk bar.
 */
function clearSelection() {
    document.querySelectorAll('.section-check, .owner-check').forEach(cb => cb.checked = false);
    document.querySelectorAll('#sections-select-all, #owners-select-all').forEach(cb => cb.checked = false);
    document.getElementById('bulk-action-bar').classList.add('hidden');
}

/**
 * Exports selected rows as CSV.
 */
function exportSelectedCSV() {
    const checked = document.querySelectorAll('.section-check:checked, .owner-check:checked');
    if (checked.length === 0) return;
    const ids = Array.from(checked).map(cb => cb.value);
    const type = checked[0].classList.contains('section-check') ? 'sections' : 'contacts';
    alert(`Export ${ids.length} ${type} to CSV — feature coming soon`);
}
