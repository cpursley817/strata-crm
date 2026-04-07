/**
 * sections.js
 * Powers the Sections list view and section detail panel
 *
 * This file contains:
 * - Sections table sorting and filtering
 * - Sections list loading and rendering
 * - Section detail view builder
 * - Tab switching for section details (owners, deals, pricing history)
 */

// Sections sort state — default to pricing_date descending
let sectionsSortCol = 'pricing_date';
let sectionsSortOrder = 'desc';

/**
 * sortSections(col)
 * Toggles sort order for sections table and reloads the list
 */
function sortSections(col) {
    if (sectionsSortCol === col) {
        sectionsSortOrder = sectionsSortOrder === 'asc' ? 'desc' : 'asc';
    } else {
        sectionsSortCol = col;
        // Default to desc for prices and dates, asc for names
        sectionsSortOrder = ['exit_price','cost_free_price','pricing_date','total_contacts','updated_at'].includes(col) ? 'desc' : 'asc';
    }
    // Update header arrows
    document.querySelectorAll('#page-sections th.sortable').forEach(th => {
        th.classList.remove('active', 'asc', 'desc');
        th.querySelector('.sort-arrow').textContent = '';
    });
    const activeTh = document.querySelector(`#page-sections th[data-sort="${col}"]`);
    if (activeTh) {
        activeTh.classList.add('active', sectionsSortOrder);
        activeTh.querySelector('.sort-arrow').textContent = sectionsSortOrder === 'asc' ? '▲' : '▼';
    }
    loadSections(1);
}

/**
 * loadSections(page)
 * Fetches and renders the sections table with filters and pagination
 */
async function loadSections(page = 1) {
    const search = document.getElementById('sections-search').value;
    const parish = document.getElementById('sections-parish-filter').value;
    const status = document.getElementById('sections-status-filter').value;
    const operator = document.getElementById('sections-operator-filter').value;

    let url = `/sections?page=${page}&per_page=25&sort=${sectionsSortCol}&order=${sectionsSortOrder}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (parish) url += `&parish=${parish}`;
    if (status) url += `&status=${encodeURIComponent(status)}`;
    if (operator) url += `&operator_id=${operator}`;

    const data = await apiCall(url);
    if (!data) return;

    window.currentSectionsPage = currentSectionsPage = data.page || 1;
    window.currentSectionsPages = currentSectionsPages = data.pages || 1;

    document.getElementById('sections-total-display').textContent = `${(data.total || 0).toLocaleString()} sections`;

    const tbody = document.getElementById('sections-table');
    tbody.innerHTML = '';

    (data.sections || []).forEach(s => {
        const row = tbody.insertRow();
        row.style.cursor = 'pointer';
        row.onclick = (e) => { if (e.target.type !== 'checkbox' && e.target.tagName !== 'SELECT') viewSectionDetail(s.section_id); };

        // Checkbox
        const checkCell = row.insertCell();
        checkCell.innerHTML = `<input type="checkbox" class="section-check" value="${s.section_id}">`;

        // Parish
        row.insertCell().textContent = s.parish_name || '-';

        // S-T-R (display_name)
        row.insertCell().innerHTML = `<span style="font-weight:500">${esc(s.display_name || '')}</span>`;

        // Status dropdown
        const statusCell = row.insertCell();
        const statuses = ['ACTIVE','INACTIVE','EXHAUSTED','NO PRICE','PROSPECT','CLOSED','HOLD'];
        const curStatus = s.status || '';
        let selHtml = `<select class="status-select" onchange="updateSectionStatus(${s.section_id}, this.value)" onclick="event.stopPropagation()">`;
        statuses.forEach(st => {
            selHtml += `<option value="${st}" ${curStatus.toUpperCase() === st ? 'selected' : ''}>${st}</option>`;
        });
        selHtml += '</select>';
        statusCell.innerHTML = selHtml;

        // Cost-Bearing $/NRA (exit_price)
        const cbCell = row.insertCell();
        cbCell.style.fontWeight = '500';
        cbCell.style.color = s.exit_price ? 'var(--g)' : 'var(--td)';
        cbCell.textContent = s.exit_price ? formatCurrency(s.exit_price) : '-';

        // Cost-Free $/NRA
        const cfCell = row.insertCell();
        cfCell.style.fontWeight = '500';
        cfCell.style.color = s.cost_free_price ? 'var(--g)' : 'var(--td)';
        cfCell.textContent = s.cost_free_price ? formatCurrency(s.cost_free_price) : '-';

        // Pricing Date with recency coloring
        const pdCell = row.insertCell();
        const pDate = s.pricing_date;
        let daysSince = null;
        if (pDate) {
            daysSince = Math.floor((Date.now() - new Date(pDate).getTime()) / 86400000);
            pdCell.style.color = daysSince <= 30 ? 'var(--g)' : daysSince <= 90 ? 'var(--y)' : 'var(--r)';
        } else {
            pdCell.style.color = 'var(--td)';
        }
        pdCell.textContent = pDate || '-';

        // Days Since Price Update (calculated)
        const dsCell = row.insertCell();
        dsCell.style.fontSize = '12px';
        if (daysSince !== null) {
            dsCell.style.color = daysSince <= 30 ? 'var(--g)' : daysSince <= 90 ? 'var(--y)' : 'var(--r)';
            dsCell.textContent = daysSince + 'd';
        } else {
            dsCell.style.color = 'var(--td)';
            dsCell.textContent = '-';
        }

        // Price Change % (calculated from prev_exit_price)
        const pcCell = row.insertCell();
        pcCell.style.fontSize = '12px';
        pcCell.style.fontWeight = '500';
        if (s.exit_price && s.prev_exit_price && s.prev_exit_price > 0) {
            const pctChange = ((s.exit_price - s.prev_exit_price) / s.prev_exit_price * 100);
            if (pctChange > 0) {
                pcCell.style.color = 'var(--g)';
                pcCell.textContent = '+' + pctChange.toFixed(1) + '%';
            } else if (pctChange < 0) {
                pcCell.style.color = 'var(--r)';
                pcCell.textContent = pctChange.toFixed(1) + '%';
            } else {
                pcCell.style.color = 'var(--td)';
                pcCell.textContent = '0%';
            }
        } else {
            pcCell.style.color = 'var(--td)';
            pcCell.textContent = '-';
        }

        // Operator
        row.insertCell().textContent = s.operator_name || '-';

        // Ownership Data
        const odCell = row.insertCell();
        odCell.style.cssText = 'font-size:12px;max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap';
        odCell.textContent = s.ownership_data || '-';
        if (s.ownership_data) odCell.title = s.ownership_data;

        // Section Notes
        const snCell = row.insertCell();
        snCell.style.cssText = 'font-size:12px;max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap';
        snCell.textContent = s.section_notes || '-';
        if (s.section_notes) snCell.title = s.section_notes;

        // Deck Name
        row.insertCell().textContent = s.deck_name || '-';
    });

    document.getElementById('sections-page-display').textContent = currentSectionsPage;
    document.getElementById('sections-pages-display').textContent = currentSectionsPages;
}

/**
 * updateSectionStatus(sectionId, newStatus)
 * Updates a section's status via API call
 */
async function updateSectionStatus(sectionId, newStatus) {
    const resp = await fetch(`/api/sections/${sectionId}`, {
        method: 'PUT',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
    });
    if (!resp.ok) {
        alert('Failed to update section status');
        loadSections(window.currentSectionsPage);
    }
}

/**
 * debounceSections()
 * Debounces the sections search/filter input to avoid excessive API calls
 */
function debounceSections() {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => loadSections(), 300);
}

/**
 * viewSectionDetail(sectionId)
 * Builds and displays the detailed view for a single section with tabs for owners, deals, and pricing history
 */
async function viewSectionDetail(sectionId) {
    const data = await apiCall(`/sections/${sectionId}`);
    if (!data) return;

    // Switch to section detail page
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById('page-section-detail').classList.add('active');
    // Highlight Sections in nav
    document.querySelectorAll('.nl button').forEach(btn => {
        btn.classList.toggle('act', btn.dataset.page === 'sections');
    });

    const ownerCount = data.owners ? data.owners.length : 0;
    const dealCount = data.deals ? data.deals.length : 0;
    const pricingCount = data.pricing_history ? data.pricing_history.length : 0;

    let h = '';

    // ── HEADER ──
    const sonrisUrl = `https://sonlite.dnr.state.la.us/ords/f?p=108:2700:::::P2700_SECTION,P2700_TOWNSHIP,P2700_RANGE:${encodeURIComponent(data.section_number || '')},${encodeURIComponent(data.township || '')},${encodeURIComponent(data.range || '')}`;
    h += `<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:24px">
        <div>
            <div style="font-size:11px;color:var(--td);font-family:monospace;margin-bottom:4px">${formatDisplayId(data.section_id, 'S')}</div>
            <h2 style="font-size:22px;margin-bottom:6px">${esc(data.display_name || '')}</h2>
            <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
                ${data.parish_name ? `<span class="owner-meta-badge source-badge">${esc(data.parish_name)} Parish</span>` : ''}
                ${data.status ? statusBadge(data.status) : ''}
                ${data.operator_name ? `<span style="font-size:12px;color:var(--td)">Operator: <strong style="color:var(--t)">${esc(data.operator_name)}</strong></span>` : ''}
            </div>
        </div>
        <div style="display:flex;gap:6px;flex-wrap:wrap">
            <a href="${sonrisUrl}" target="_blank" class="quick-link-btn" style="font-size:11px">SONRIS Wells</a>
            <a href="https://www.evaultla.com/Identity/Account/Login?ReturnUrl=%2FeClerks%2FStatewidePortal" target="_blank" class="quick-link-btn" style="font-size:11px">eClerk Records</a>
        </div>
    </div>`;

    // ── PRICING & INFO CARDS ──
    h += `<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px">
        <div class="stat-card success">
            <div class="stat-label">Cost-Bearing $/NRA</div>
            <div class="stat-value" style="font-size:22px">${data.exit_price ? formatCurrency(data.exit_price) : 'N/A'}</div>
        </div>
        <div class="stat-card success">
            <div class="stat-label">Cost-Free $/NRA</div>
            <div class="stat-value" style="font-size:22px">${data.cost_free_price ? formatCurrency(data.cost_free_price) : 'N/A'}</div>
            ${data.prev_cost_free_price ? `<div style="font-size:11px;color:var(--td);margin-top:4px">Prev: ${formatCurrency(data.prev_cost_free_price)}</div>` : ''}
        </div>
        <div class="stat-card">
            <div class="stat-label">Pricing Date</div>
            <div class="stat-value" style="font-size:18px">${data.pricing_date || 'N/A'}</div>
            ${data.prev_pricing_date ? `<div style="font-size:11px;color:var(--td);margin-top:4px">Prev: ${data.prev_pricing_date}</div>` : ''}
        </div>
        <div class="stat-card">
            <div class="stat-label">Linked Owners</div>
            <div class="stat-value" style="font-size:18px">${ownerCount}</div>
        </div>
    </div>`;

    // ── CONTACT STATUS SUMMARY BAR ──
    if (ownerCount > 0) {
        const statusCounts = {};
        data.owners.forEach(o => {
            const st = o.contact_status || 'Not Contacted';
            statusCounts[st] = (statusCounts[st] || 0) + 1;
        });
        h += `<div class="card" style="margin-bottom:16px;padding:12px 16px">
            <div style="font-size:11px;text-transform:uppercase;letter-spacing:.4px;color:var(--td);font-weight:600;margin-bottom:8px">Contact Status Breakdown</div>
            <div style="display:flex;gap:12px;flex-wrap:wrap">`;
        Object.entries(statusCounts).forEach(([status, count]) => {
            h += `<span style="font-size:12px">${statusBadge(status)} <strong>${count}</strong></span>`;
        });
        h += `</div></div>`;
    }

    // ── PRICING HISTORY CHART (simple visual if data exists) ──
    if (pricingCount > 1) {
        const prices = data.pricing_history.slice().reverse();
        const maxPrice = Math.max(...prices.map(p => Math.max(p.exit_price || 0, p.cost_free_price || 0)));
        h += `<div class="card" style="margin-bottom:16px">
            <div style="font-size:11px;text-transform:uppercase;letter-spacing:.4px;color:var(--td);font-weight:600;margin-bottom:12px">Pricing Trend</div>
            <div style="display:flex;align-items:flex-end;gap:4px;height:80px">`;
        prices.forEach(p => {
            const bbrH = maxPrice > 0 ? Math.round((p.exit_price || 0) / maxPrice * 70) : 0;
            const cfH = maxPrice > 0 ? Math.round((p.cost_free_price || 0) / maxPrice * 70) : 0;
            h += `<div style="flex:1;display:flex;gap:1px;align-items:flex-end" title="${p.effective_date}: Exit ${formatCurrency(p.exit_price || 0)}, CF ${formatCurrency(p.cost_free_price || 0)}">
                <div style="flex:1;height:${bbrH}px;background:var(--g);border-radius:2px 2px 0 0;min-height:2px"></div>
                <div style="flex:1;height:${cfH}px;background:var(--ac);border-radius:2px 2px 0 0;min-height:2px"></div>
            </div>`;
        });
        h += `</div>
            <div style="display:flex;gap:12px;margin-top:8px;font-size:10px;color:var(--td)">
                <span><span style="display:inline-block;width:8px;height:8px;background:var(--g);border-radius:1px;margin-right:3px"></span>Cost-Bearing $/NRA</span>
                <span><span style="display:inline-block;width:8px;height:8px;background:var(--ac);border-radius:1px;margin-right:3px"></span>Cost-Free $/NRA</span>
            </div>
        </div>`;
    }

    // ── LEGAL & DETAILS ──
    h += `<div class="card" style="margin-bottom:24px">
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px">
            <div>
                <div style="font-size:11px;color:var(--td);text-transform:uppercase;letter-spacing:.4px;margin-bottom:4px">Section / Township / Range</div>
                <div style="font-size:14px">${[data.section_number, data.township, data.range].filter(Boolean).join(' · ') || 'N/A'}</div>
            </div>
            <div>
                <div style="font-size:11px;color:var(--td);text-transform:uppercase;letter-spacing:.4px;margin-bottom:4px">Deck Name</div>
                <div style="font-size:14px">${esc(data.deck_name || 'N/A')}</div>
            </div>
            <div>
                <div style="font-size:11px;color:var(--td);text-transform:uppercase;letter-spacing:.4px;margin-bottom:4px">Ownership Data</div>
                <div style="font-size:14px">${esc(data.ownership_data || 'N/A')}</div>
            </div>
        </div>
        ${data.section_notes ? `<div style="margin-top:16px;padding-top:16px;border-top:1px solid var(--b)">
            <div style="font-size:11px;color:var(--td);text-transform:uppercase;letter-spacing:.4px;margin-bottom:4px">Notes</div>
            <div style="font-size:13px;white-space:pre-wrap">${esc(data.section_notes)}</div>
        </div>` : ''}
    </div>`;

    // ── TABBED: Owners / Deals / Pricing History ──
    h += `<div class="owner-section-tabs">
        <div class="owner-section-tab active" onclick="switchSectionTab('owners', this)">Owners ${ownerCount > 0 ? '<span style="opacity:.6">(' + ownerCount + ')</span>' : ''}</div>
        <div class="owner-section-tab" onclick="switchSectionTab('deals', this)">Deals ${dealCount > 0 ? '<span style="opacity:.6">(' + dealCount + ')</span>' : ''}</div>
        <div class="owner-section-tab" onclick="switchSectionTab('pricing', this)">Pricing History ${pricingCount > 0 ? '<span style="opacity:.6">(' + pricingCount + ')</span>' : ''}</div>
    </div>`;

    // Owners tab
    h += '<div id="section-tab-owners" class="owner-tab-content active">';
    if (ownerCount > 0) {
        h += `<table style="width:100%;border-collapse:collapse;font-size:13px">
            <thead><tr>
                <th style="text-align:left;padding:8px">Name</th>
                <th style="text-align:left;padding:8px">Phone</th>
                <th style="text-align:left;padding:8px">Email</th>
                <th style="text-align:left;padding:8px">City</th>
                <th style="text-align:right;padding:8px">NRA</th>
                <th style="text-align:left;padding:8px">Interest</th>
                <th style="text-align:left;padding:8px">Status</th>
            </tr></thead><tbody>`;
        data.owners.forEach(o => {
            h += `<tr style="cursor:pointer" onclick="viewOwnerDetail(${o.owner_id})">
                <td style="padding:8px;color:var(--ac);font-weight:500">${esc(o.full_name || '')}</td>
                <td style="padding:8px">${o.phone_1 ? `<a href="tel:${o.phone_1}" style="color:var(--ac)">${esc(o.phone_1)}</a>` : '<span style="color:var(--td)">-</span>'}</td>
                <td style="padding:8px">${o.email_1 ? `<a href="mailto:${o.email_1}" style="color:var(--ac)">${esc(o.email_1)}</a>` : '<span style="color:var(--td)">-</span>'}</td>
                <td style="padding:8px">${esc(o.city || '')}</td>
                <td style="padding:8px;text-align:right;font-weight:500">${o.nra || '-'}</td>
                <td style="padding:8px;font-size:11px">${esc(o.interest_type || '')}</td>
                <td style="padding:8px">${statusBadge(o.contact_status || '')}</td>
            </tr>`;
        });
        h += '</tbody></table>';
    } else {
        h += '<div style="padding:24px;color:var(--td);text-align:center">No owners linked to this section. Import pay deck data to populate ownership.</div>';
    }
    h += '</div>';

    // Deals tab
    h += '<div id="section-tab-deals" class="owner-tab-content">';
    if (dealCount > 0) {
        h += `<table style="width:100%;border-collapse:collapse;font-size:13px">
            <thead><tr>
                <th style="text-align:left;padding:8px">Deal</th>
                <th style="text-align:left;padding:8px">Owner</th>
                <th style="text-align:left;padding:8px">Stage</th>
                <th style="text-align:right;padding:8px">Value</th>
            </tr></thead><tbody>`;
        data.deals.forEach(d => {
            h += `<tr>
                <td style="padding:8px;font-weight:500">${esc(d.title || '')}</td>
                <td style="padding:8px;color:var(--ac);cursor:pointer" onclick="viewOwnerDetail(${d.owner_id})">${esc(d.owner_name || '')}</td>
                <td style="padding:8px">${statusBadge(d.stage_name || '')}</td>
                <td style="padding:8px;text-align:right;font-weight:500;color:var(--g)">${formatCurrency(d.value || 0)}</td>
            </tr>`;
        });
        h += '</tbody></table>';
    } else {
        h += '<div style="padding:24px;color:var(--td);text-align:center">No deals for this section yet.</div>';
    }
    h += '</div>';

    // Pricing History tab
    h += '<div id="section-tab-pricing" class="owner-tab-content">';
    if (pricingCount > 0) {
        h += `<table style="width:100%;border-collapse:collapse;font-size:13px">
            <thead><tr>
                <th style="text-align:left;padding:8px">Date</th>
                <th style="text-align:right;padding:8px">Cost-Bearing</th>
                <th style="text-align:right;padding:8px">Cost-Free</th>
                <th style="text-align:left;padding:8px">Notes</th>
            </tr></thead><tbody>`;
        data.pricing_history.forEach(p => {
            h += `<tr>
                <td style="padding:8px">${p.effective_date || ''}</td>
                <td style="padding:8px;text-align:right;font-weight:500;color:var(--g)">${formatCurrency(p.exit_price || 0)}</td>
                <td style="padding:8px;text-align:right;font-weight:500;color:var(--g)">${formatCurrency(p.cost_free_price || 0)}</td>
                <td style="padding:8px;font-size:12px;color:var(--td)">${esc(p.notes || '')}</td>
            </tr>`;
        });
        h += '</tbody></table>';
    } else {
        h += '<div style="padding:24px;color:var(--td);text-align:center">No pricing history recorded.</div>';
    }
    h += '</div>';

    document.getElementById('section-detail-content').innerHTML = h;
}

/**
 * switchSectionTab(tab, el)
 * Switches between tabs in the section detail view (owners, deals, pricing)
 */
function switchSectionTab(tab, el) {
    const container = document.getElementById('section-detail-content');
    container.querySelectorAll('.owner-section-tab').forEach(t => t.classList.remove('active'));
    container.querySelectorAll('.owner-tab-content').forEach(c => c.classList.remove('active'));
    if (el) el.classList.add('active');
    const tabEl = container.querySelector(`#section-tab-${tab}`);
    if (tabEl) tabEl.classList.add('active');
}
