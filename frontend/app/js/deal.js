/**
 * deal.js
 * Powers the Deal Detail page
 * Shows full deal information with editable fields, stage management, owner/section info, and activity timeline
 */

/**
 * viewDealDetail(dealId)
 * Loads and renders the full deal detail page
 */
async function viewDealDetail(dealId) {
    const data = await apiCall(`/deals/${dealId}`);
    if (!data) return;

    // Switch to deal detail page
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById('page-deal-detail').classList.add('active');
    document.querySelectorAll('.nl button').forEach(btn => {
        btn.classList.toggle('act', btn.dataset.page === 'pipeline');
    });

    const activityCount = data.activities ? data.activities.length : 0;
    const historyCount = data.history ? data.history.length : 0;

    let h = '';

    // ── HEADER ──
    h += `<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:24px">
        <div>
            <h2 style="font-size:22px;margin-bottom:6px">${esc(data.title || '')}</h2>
            <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
                ${statusBadge(data.stage_name || '')}
                <span style="font-size:12px;color:var(--td)">Status: <strong style="color:${data.status === 'open' ? 'var(--g)' : data.status === 'closed_won' ? 'var(--g)' : 'var(--r)'}">${(data.status || 'open').toUpperCase()}</strong></span>
                ${data.assigned_name ? `<span style="font-size:12px;color:var(--td)">Assigned: <strong style="color:var(--t)">${esc(data.assigned_name)}</strong></span>` : ''}
                <button class="bs" style="font-size:11px;padding:4px 10px;color:var(--r);margin-left:8px" onclick="deleteDeal(${data.deal_id}, '${esc(data.title || '').replace(/'/g, "\\'")}')">Delete Deal</button>
            </div>
        </div>
        <div style="text-align:right">
            <div style="font-size:28px;font-weight:700;color:var(--g)">${data.value ? formatCurrency(data.value) : 'No Value'}</div>
            <div style="font-size:11px;color:var(--td)">Deal Value</div>
        </div>
    </div>`;

    // ── KEY METRICS ──
    h += `<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px">
        <div class="stat-card success">
            <div class="stat-label">NRA</div>
            <div class="stat-value" style="font-size:22px">${data.nra || 'N/A'}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Price / NRA</div>
            <div class="stat-value" style="font-size:22px">${data.price_per_nra ? formatCurrency(data.price_per_nra) : 'N/A'}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Expected Close</div>
            <div class="stat-value" style="font-size:18px">${data.expected_close || 'Not Set'}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Created</div>
            <div class="stat-value" style="font-size:18px">${data.created_at ? new Date(data.created_at).toLocaleDateString() : 'N/A'}</div>
        </div>
    </div>`;

    // ── STAGE SELECTOR ──
    const lookups = await apiCall('/lookups');
    const stages = lookups ? (lookups.pipeline_stages || []) : [];
    h += `<div class="card" style="margin-bottom:24px">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
            <div class="card-title" style="margin-bottom:0">Pipeline Stage</div>
            <select style="font-size:13px;padding:6px 12px" onchange="updateDealStage(${data.deal_id}, this.value)">
                ${stages.map(s => `<option value="${s.stage_id}" ${s.stage_id === data.stage_id ? 'selected' : ''}>${esc(s.name)}</option>`).join('')}
            </select>
        </div>
        <div style="display:flex;gap:4px;overflow-x:auto">
            ${stages.map(s => {
                const isCurrent = s.stage_id === data.stage_id;
                const isPast = s.sort_order < (stages.find(st => st.stage_id === data.stage_id) || {sort_order: 0}).sort_order;
                const color = isCurrent ? 'var(--g)' : isPast ? 'var(--ac)' : 'var(--b)';
                return `<div style="flex:1;height:6px;border-radius:3px;background:${color}" title="${esc(s.name)}"></div>`;
            }).join('')}
        </div>
    </div>`;

    // ── OWNER & SECTION INFO (side by side) ──
    h += `<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:24px">`;

    // Owner card
    h += `<div class="card" style="margin-bottom:0">
        <div class="card-title">Contact</div>
        <div style="font-weight:500;font-size:15px;color:var(--ac);cursor:pointer;margin-bottom:8px" onclick="viewOwnerDetail(${data.owner_id})">${esc(data.owner_name || 'Unknown')}</div>
        <div style="font-size:12px;color:var(--td)">
            ${data.owner_classification ? classBadge(data.owner_classification) + '<br>' : ''}
            ${data.owner_phone ? `<a href="tel:${data.owner_phone}" style="color:var(--ac)">${esc(data.owner_phone)}</a><br>` : ''}
            ${data.owner_email ? `<a href="mailto:${data.owner_email}" style="color:var(--ac)">${esc(data.owner_email)}</a><br>` : ''}
            ${[data.owner_city, data.owner_state].filter(Boolean).join(', ') || ''}
        </div>
    </div>`;

    // Section card
    h += `<div class="card" style="margin-bottom:0">
        <div class="card-title">Section</div>
        <div style="font-weight:500;font-size:15px;color:var(--ac);cursor:pointer;margin-bottom:8px" onclick="viewSectionDetail(${data.section_id})">${esc(data.section_name || 'Unknown')}</div>
        <div style="font-size:12px;color:var(--td)">
            ${data.parish_name ? esc(data.parish_name) + ' Parish<br>' : ''}
            ${data.exit_price ? 'Exit: ' + formatCurrency(data.exit_price) + '<br>' : ''}
            ${data.cost_free_price ? 'CF: ' + formatCurrency(data.cost_free_price) : ''}
        </div>
    </div>`;
    h += `</div>`;

    // ── EDIT FIELDS ──
    h += `<div class="card" style="margin-bottom:24px">
        <div class="card-title">Edit Deal</div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px">
            <div>
                <label style="font-size:11px;color:var(--td);display:block;margin-bottom:4px">NRA</label>
                <input type="number" id="deal-edit-nra" value="${data.nra || ''}" step="0.00000001" style="width:100%">
            </div>
            <div>
                <label style="font-size:11px;color:var(--td);display:block;margin-bottom:4px">Price / NRA</label>
                <input type="number" id="deal-edit-price" value="${data.price_per_nra || ''}" step="1" style="width:100%">
            </div>
            <div>
                <label style="font-size:11px;color:var(--td);display:block;margin-bottom:4px">Expected Close</label>
                <input type="date" id="deal-edit-close" value="${data.expected_close || ''}" style="width:100%">
            </div>
        </div>
        <div style="margin-top:12px;display:flex;gap:8px">
            <button class="bp" style="font-size:12px;padding:6px 14px" onclick="saveDealEdits(${data.deal_id})">Save Changes</button>
            ${data.status === 'open' ? `
                <button class="bp" style="font-size:12px;padding:6px 14px;background:var(--g)" onclick="closeDeal(${data.deal_id}, 'closed_won')">Close Won</button>
                <button class="bs" style="font-size:12px;padding:6px 14px;color:var(--r)" onclick="closeDeal(${data.deal_id}, 'closed_lost')">Close Lost</button>
            ` : ''}
        </div>
    </div>`;

    // ── TABS: Activity / History ──
    h += `<div class="owner-section-tabs">
        <div class="owner-section-tab active" onclick="switchDealTab('activity', this)">Activity ${activityCount > 0 ? '<span style="opacity:.6">(' + activityCount + ')</span>' : ''}</div>
        <div class="owner-section-tab" onclick="switchDealTab('history', this)">Stage History ${historyCount > 0 ? '<span style="opacity:.6">(' + historyCount + ')</span>' : ''}</div>
    </div>`;

    // Activity tab
    h += '<div id="deal-tab-activity" class="owner-tab-content active">';
    if (activityCount > 0) {
        data.activities.forEach(a => {
            h += `<div style="padding:8px 0;border-bottom:1px solid var(--b);font-size:12px">
                <div style="display:flex;justify-content:space-between">
                    <strong style="text-transform:capitalize;color:var(--ac)">${esc(a.type)}</strong>
                    <span style="color:var(--td);font-size:10px">${new Date(a.created_at).toLocaleDateString()}</span>
                </div>
                <div style="margin-top:3px;color:var(--t)">${esc(a.subject || a.body || '')}</div>
                ${a.user_name ? `<div style="color:var(--td);font-size:10px;margin-top:2px">by ${esc(a.user_name)}</div>` : ''}
            </div>`;
        });
    } else {
        h += '<div style="padding:16px;color:var(--td);text-align:center;font-size:13px">No activity logged for this deal</div>';
    }
    h += '</div>';

    // History tab
    h += '<div id="deal-tab-history" class="owner-tab-content">';
    if (historyCount > 0) {
        data.history.forEach(entry => {
            h += `<div style="padding:8px 0;border-bottom:1px solid var(--b);font-size:12px">
                <div style="display:flex;justify-content:space-between">
                    <strong style="color:var(--ac)">${esc(entry.action)}</strong>
                    <span style="color:var(--td);font-size:10px">${new Date(entry.created_at).toLocaleDateString()}</span>
                </div>
                ${entry.user_name ? `<div style="color:var(--td);font-size:10px;margin-top:2px">by ${esc(entry.user_name)}</div>` : ''}
            </div>`;
        });
    } else {
        h += '<div style="padding:16px;color:var(--td);text-align:center;font-size:13px">No stage history</div>';
    }
    h += '</div>';

    document.getElementById('deal-detail-content').innerHTML = h;
}

/**
 * switchDealTab(tab, el)
 * Switches between activity and history tabs on the deal detail page
 */
function switchDealTab(tab, el) {
    const container = document.getElementById('deal-detail-content');
    container.querySelectorAll('.owner-section-tab').forEach(t => t.classList.remove('active'));
    container.querySelectorAll('.owner-tab-content').forEach(c => c.classList.remove('active'));
    if (el) el.classList.add('active');
    const tabEl = container.querySelector(`#deal-tab-${tab}`);
    if (tabEl) tabEl.classList.add('active');
}

/**
 * saveDealEdits(dealId)
 * Saves edited deal fields (NRA, price, expected close date)
 */
async function saveDealEdits(dealId) {
    const nra = parseFloat(document.getElementById('deal-edit-nra').value) || null;
    const pricePerNra = parseFloat(document.getElementById('deal-edit-price').value) || null;
    const expectedClose = document.getElementById('deal-edit-close').value || null;
    const value = (nra && pricePerNra) ? nra * pricePerNra : null;

    const resp = await apiCall(`/deals/${dealId}`, 'PUT', {
        nra, price_per_nra: pricePerNra, value, expected_close: expectedClose
    });
    if (resp) viewDealDetail(dealId);
}

/**
 * updateDealStage(dealId, newStageId)
 * Updates the deal's pipeline stage from the dropdown
 */
async function updateDealStage(dealId, newStageId) {
    const resp = await apiCall(`/deals/${dealId}`, 'PUT', { stage_id: parseInt(newStageId) });
    if (resp) viewDealDetail(dealId);
}

/**
 * closeDeal(dealId, status)
 * Closes a deal as won or lost
 */
async function closeDeal(dealId, status) {
    let reason = '';
    if (status === 'closed_lost') {
        reason = prompt('Reason for losing this deal:');
        if (reason === null) return;
    }
    const today = new Date().toISOString().split('T')[0];
    const update = { status, actual_close: today };
    if (reason) update.lost_reason = reason;
    const resp = await apiCall(`/deals/${dealId}`, 'PUT', update);
    if (resp) viewDealDetail(dealId);
}

/**
 * deleteDeal(dealId, title)
 * Deletes a deal after confirmation
 */
async function deleteDeal(dealId, title) {
    if (!confirm(`Delete deal "${title}"?\n\nThis cannot be undone. The deal and its stage history will be permanently removed.`)) return;
    const resp = await fetch(`/api/deals/${dealId}`, {
        method: 'DELETE',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
    });
    if (resp.ok) {
        setPage('pipeline');
    } else {
        alert('Failed to delete deal');
    }
}
