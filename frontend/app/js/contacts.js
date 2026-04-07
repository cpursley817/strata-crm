/**
 * contacts.js
 * Powers the Contacts list view and contact detail panel
 *
 * This file contains:
 * - Contacts table sorting and filtering
 * - Contact list loading and rendering
 * - Contact detail panel builder
 * - Deal creation from contact
 * - Contact status updates
 * - Contact notes management
 * - Phone verification
 * - Tab switching for contact details (sections, deals, activity)
 */

let ownersSortCol = 'full_name';
let ownersSortOrder = 'asc';
let ownerStatesLoaded = false;

/**
 * Populates the states filter dropdown on the Contacts page.
 */
async function loadOwnerStates() {
    if (ownerStatesLoaded) return;
    const states = await apiCall('/owners/states');
    if (!states) return;
    const select = document.getElementById('owners-state-filter');
    if (!select) return;
    while (select.options.length > 1) select.remove(1);
    states.forEach(s => {
        if (s.state) {
            const opt = document.createElement('option');
            opt.value = s.state;
            opt.textContent = `${s.state} (${s.cnt.toLocaleString()})`;
            select.appendChild(opt);
        }
    });
    ownerStatesLoaded = true;
}

/**
 * sortOwners(col)
 * Toggles sort order for contacts table and reloads the list
 */
function sortOwners(col) {
    if (ownersSortCol === col) {
        ownersSortOrder = ownersSortOrder === 'asc' ? 'desc' : 'asc';
    } else {
        ownersSortCol = col;
        ownersSortOrder = 'asc';
    }
    document.querySelectorAll('#page-owners th.sortable').forEach(th => {
        th.classList.remove('active', 'asc', 'desc');
        th.querySelector('.sort-arrow').textContent = '';
    });
    const activeTh = document.querySelector(`#page-owners th[data-sort="${col}"]`);
    if (activeTh) {
        activeTh.classList.add('active', ownersSortOrder);
        activeTh.querySelector('.sort-arrow').textContent = ownersSortOrder === 'asc' ? '\u25B2' : '\u25BC';
    }
    loadOwners(1);
}

/**
 * sourceBadge(src)
 * Returns HTML badge for the data source of a contact
 */
function sourceBadge(src) {
    if (!src) return '';
    const label = src === 'ais_sql_dump' ? 'AIS' :
                  src === 'ais_contact_directory' ? 'AIS Dir' :
                  src === 'pipedrive' ? 'Pipedrive' :
                  src === 'paydeck' ? 'Pay Deck' :
                  src === 'idicore' ? 'idiCore' : src;
    const colors = {
        'AIS': 'background:rgba(91,159,255,.15);color:#5b9fff;border:1px solid rgba(91,159,255,.3)',
        'AIS Dir': 'background:rgba(91,159,255,.15);color:#5b9fff;border:1px solid rgba(91,159,255,.3)',
        'Pipedrive': 'background:rgba(0,180,81,.15);color:var(--g);border:1px solid rgba(0,180,81,.3)',
        'Pay Deck': 'background:rgba(189,154,95,.15);color:var(--y);border:1px solid rgba(189,154,95,.3)',
        'idiCore': 'background:rgba(156,107,255,.15);color:var(--p);border:1px solid rgba(156,107,255,.3)',
    };
    const style = colors[label] || 'background:var(--b);color:var(--td)';
    return `<span style="display:inline-block;padding:2px 7px;border-radius:10px;font-size:10px;font-weight:600;letter-spacing:.3px;${style}">${esc(label)}</span>`;
}

/**
 * loadOwners(page)
 * Fetches and renders the contacts table with filters and pagination
 */
async function loadOwners(page = 1) {
    const search = document.getElementById('owners-search').value;
    const phoneSearch = document.getElementById('owners-phone-search')?.value || '';
    const emailSearch = document.getElementById('owners-email-search')?.value || '';
    const status = document.getElementById('owners-status-filter').value;
    const classification = document.getElementById('owners-classification-filter').value;
    const stateFilter = document.getElementById('owners-state-filter')?.value || '';
    const sourceFilter = document.getElementById('owners-source-filter')?.value || '';
    const deceasedFilter = document.getElementById('owners-deceased-filter').value;

    const combinedSearch = [search, phoneSearch, emailSearch].filter(Boolean).join(' ');

    let url = `/owners?page=${page}&per_page=25&sort=${ownersSortCol}&order=${ownersSortOrder}`;
    if (combinedSearch) url += `&search=${encodeURIComponent(combinedSearch)}`;
    if (stateFilter) url += `&state=${encodeURIComponent(stateFilter)}`;
    if (sourceFilter) url += `&data_source=${encodeURIComponent(sourceFilter)}`;
    if (status) url += `&contact_status=${encodeURIComponent(status)}`;
    if (classification) url += `&classification=${encodeURIComponent(classification)}`;
    if (deceasedFilter === 'alive') url += '&deceased=0';
    else if (deceasedFilter === 'deceased') url += '&deceased=1';

    const data = await apiCall(url);
    if (!data) return;

    window.currentOwnersPage = currentOwnersPage = data.page || 1;
    window.currentOwnersPages = currentOwnersPages = data.pages || 1;

    const tbody = document.getElementById('owners-table');
    tbody.innerHTML = '';

    let owners = data.owners || [];
    if (deceasedFilter === 'deceased') owners = owners.filter(o => o.is_deceased);

    const searchLower = search.toLowerCase();

    owners.forEach(o => {
        const row = tbody.insertRow();
        row.style.cursor = 'pointer';
        row.onclick = (e) => { if (e.target.type !== 'checkbox') viewOwnerDetail(o.owner_id); };

        // Checkbox
        const checkCell = row.insertCell();
        checkCell.innerHTML = `<input type="checkbox" class="owner-check" value="${o.owner_id}">`;

        // Name with DNC + deceased flags
        const nameCell = row.insertCell();
        let nameHtml = `<span style="font-weight:500">${esc(o.full_name || '')}</span>`;
        if (o.do_not_contact === 1) {
            nameHtml += ` <span style="padding:1px 5px;border-radius:3px;font-size:9px;font-weight:700;background:rgba(255,0,0,.15);color:#ff4444">DNC</span>`;
            row.style.opacity = '0.6';
        }
        if (o.reserved_for_user_id) {
            nameHtml += ` <span style="padding:1px 5px;border-radius:3px;font-size:9px;font-weight:700;background:rgba(189,154,95,.15);color:var(--y)">RESERVED</span>`;
        }
        if (o.is_deceased) nameHtml += ` <span style="padding:1px 5px;border-radius:3px;font-size:9px;font-weight:700;background:rgba(255,103,29,.15);color:var(--r)">DECEASED</span>`;
        nameCell.innerHTML = nameHtml;

        // Type badge
        row.insertCell().innerHTML = classBadge(o.classification);

        // Address
        row.insertCell().textContent = o.mailing_address || '-';

        // City
        row.insertCell().textContent = o.city || '-';

        // State
        row.insertCell().textContent = o.state || '-';

        // Phone with verification star
        const phone = o.phone_1 || '';
        const phoneCell = row.insertCell();
        if (phone) {
            const star = o.phone_1_verified ? '<span style="color:var(--y);margin-right:2px" title="Verified">\u2605</span>' : '';
            phoneCell.innerHTML = `${star}<a href="tel:${sanitizePhone(phone)}" style="color:var(--ac)">${esc(formatPhone(phone))}</a>`;
        } else {
            phoneCell.innerHTML = '<span style="color:var(--td)">-</span>';
        }

        // Email
        const email = o.email_1 || '';
        const emailCell = row.insertCell();
        emailCell.innerHTML = email ? `<a href="mailto:${email}" style="color:var(--ac)">${esc(email)}</a>` : '<span style="color:var(--td)">-</span>';

        // Age + deceased tag
        const ageCell = row.insertCell();
        const estAge = o.date_of_birth ? Math.floor((Date.now() - new Date(o.date_of_birth).getTime()) / 31557600000) : (o.age || null);
        let ageHtml = estAge ? `${estAge}` : '-';
        if (o.is_deceased) ageHtml += ` <span style="padding:1px 4px;border-radius:3px;font-size:8px;font-weight:700;background:rgba(255,103,29,.15);color:var(--r)">DECEASED</span>`;
        ageCell.innerHTML = ageHtml;

        // Sections count
        const secCell = row.insertCell();
        const secCount = o.section_count || 0;
        if (secCount > 0) {
            secCell.innerHTML = `<span style="padding:2px 7px;border-radius:10px;font-size:10px;font-weight:600;background:rgba(0,180,81,.12);color:var(--g);border:1px solid rgba(0,180,81,.25)">${secCount}</span>`;
        } else {
            secCell.innerHTML = '<span style="color:var(--td)">-</span>';
        }

        // Sources count
        const srcCell = row.insertCell();
        const srcList = (o.data_source || '').split(',').filter(Boolean);
        const srcCount = srcList.length;
        if (srcCount > 1) {
            srcCell.innerHTML = `<span style="padding:2px 7px;border-radius:10px;font-size:10px;font-weight:600;background:rgba(156,107,255,.12);color:var(--p);border:1px solid rgba(156,107,255,.25)">${srcCount} sources</span>`;
        } else {
            srcCell.innerHTML = sourceBadge(o.data_source);
        }

        // Status
        row.insertCell().innerHTML = statusBadge(o.contact_status);

        // Flags (source badges + financial flag count)
        const flagsCell = row.insertCell();
        let flagsHtml = '';
        // Financial flags count
        const flagCount = (o.has_bankruptcy ? 1 : 0) + (o.has_lien ? 1 : 0) + (o.has_judgment ? 1 : 0) +
            (o.has_evictions ? 1 : 0) + (o.has_foreclosures ? 1 : 0) + (o.has_debt ? 1 : 0);
        if (flagCount > 0) {
            const flagClass = flagCount >= 3 ? 'danger' : 'warn';
            flagsHtml += `<span class="flag-count ${flagClass}" title="${flagCount} financial flag${flagCount > 1 ? 's' : ''}">${flagCount}</span>`;
        }
        flagsCell.innerHTML = flagsHtml;
    });

    document.getElementById('owners-page-display').textContent = currentOwnersPage;
    document.getElementById('owners-pages-display').textContent = currentOwnersPages;
    document.getElementById('owners-total-display').textContent = `${(data.total || 0).toLocaleString()} contacts`;
}

/**
 * debounceOwners()
 * Debounces the contacts search/filter input to avoid excessive API calls
 */
function debounceOwners() {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => loadOwners(), 300);
}

/**
 * viewOwnerDetail(ownerId)
 * Builds and displays the detailed panel for a single contact with tabs for sections, deals, and activity
 */
async function viewOwnerDetail(ownerId) {
    const data = await apiCall(`/owners/${ownerId}`);
    if (!data) return;

    // Header — name
    document.getElementById('panel-owner-name').textContent = data.full_name || '';

    // Aliases inline under name
    const aliasEl = document.getElementById('panel-aliases-inline');
    if (data.aliases && data.aliases.length > 0) {
        const akaNames = data.aliases.map(a => esc(a.alias_value || a.alias_name || '')).filter(Boolean);
        aliasEl.innerHTML = `<div style="font-size:12px;color:var(--td);margin-top:2px">aka: ${akaNames.join(', ')}</div>`;
    } else {
        aliasEl.innerHTML = '';
    }

    // Meta badges
    let badges = [];
    if (data.classification) badges.push(classBadge(data.classification));
    const estAge = data.date_of_birth ? Math.floor((Date.now() - new Date(data.date_of_birth).getTime()) / 31557600000) : (data.age || null);
    if (estAge) badges.push(`<span class="owner-meta-badge age-badge">Age: ${estAge}</span>`);
    if (data.is_deceased) badges.push(`<span class="owner-meta-badge deceased-badge">DECEASED</span>`);
    // Source badges — show each source individually
    if (data.data_source) {
        data.data_source.split(',').forEach(src => {
            src = src.trim();
            if (src) badges.push(sourceBadge(src));
        });
    }
    document.getElementById('panel-meta-badges').innerHTML = badges.join('');

    // Build body HTML
    let h = '';

    // ── DNC / RESERVED WARNINGS ──
    if (data.do_not_contact === 1) {
        h += `<div style="background:rgba(255,103,29,.15);border:2px solid var(--r);border-radius:var(--rad);padding:12px 16px;margin-bottom:16px;display:flex;align-items:center;gap:10px">
            <span style="font-size:20px">🚫</span>
            <div>
                <div style="font-weight:700;color:var(--r);font-size:14px">DO NOT CONTACT</div>
                <div style="font-size:12px;color:var(--td)">${data.dnc_reason ? esc(data.dnc_reason) : 'Contact has requested no further communication'}${data.dnc_date ? ' · Set: ' + data.dnc_date : ''}</div>
            </div>
        </div>`;
    }
    if (data.reserved_for_user_id) {
        h += `<div style="background:rgba(189,154,95,.12);border:2px solid var(--y);border-radius:var(--rad);padding:12px 16px;margin-bottom:16px;display:flex;align-items:center;gap:10px">
            <span style="font-size:20px">🔒</span>
            <div>
                <div style="font-weight:700;color:var(--y);font-size:14px">RESERVED FOR: ${esc(data.reserved_for_name || 'Unknown')}</div>
                <div style="font-size:12px;color:var(--td)">${data.reserved_reason ? esc(data.reserved_reason) : 'This contact is assigned to a specific buyer'}${data.reserved_date ? ' · Since: ' + data.reserved_date : ''}</div>
            </div>
        </div>`;
    }

    // ── ACTION BUTTONS ──
    h += `<div style="display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap">
        <button class="bp" style="font-size:12px;padding:6px 14px" onclick="showCreateDealForm(${data.owner_id}, '${esc(data.full_name || '')}')">+ Create Deal</button>
        <select style="font-size:12px;padding:5px 10px;border-radius:var(--rad)" onchange="updateContactStatus(${data.owner_id}, this.value)">
            <option value="">Change Status</option>
            <option value="Not Contacted" ${data.contact_status === 'Not Contacted' ? 'selected' : ''}>Not Contacted</option>
            <option value="Attempted" ${data.contact_status === 'Attempted' ? 'selected' : ''}>Attempted</option>
            <option value="Reached" ${data.contact_status === 'Reached' ? 'selected' : ''}>Reached</option>
            <option value="Follow Up Needed" ${data.contact_status === 'Follow Up Needed' ? 'selected' : ''}>Follow Up</option>
            <option value="No Answer" ${data.contact_status === 'No Answer' ? 'selected' : ''}>No Answer</option>
            <option value="Bad Contact Info" ${data.contact_status === 'Bad Contact Info' ? 'selected' : ''}>Bad Contact</option>
        </select>
        <button class="bs" style="font-size:11px;padding:5px 10px;color:${data.do_not_contact ? 'var(--g)' : 'var(--r)'}" onclick="toggleDNC(${data.owner_id}, ${data.do_not_contact ? 0 : 1})">${data.do_not_contact ? 'Remove DNC' : '🚫 Mark DNC'}</button>
        ${data.reserved_for_user_id
            ? `<button class="bs" style="font-size:11px;padding:5px 10px;color:var(--g)" onclick="unreserveContact(${data.owner_id})">🔓 Unreserve</button>`
            : `<button class="bs" style="font-size:11px;padding:5px 10px;color:var(--y)" onclick="showReserveForm(${data.owner_id})">🔒 Reserve</button>`
        }
    </div>`;

    // ── TABS AT TOP ──
    const sectionCount = data.sections ? data.sections.length : 0;
    const dealCount = data.deals ? data.deals.length : 0;
    const activityCount = data.activities ? data.activities.length : 0;
    h += `<div class="owner-section-tabs">
        <div class="owner-section-tab active" onclick="switchOwnerTab('contact-info', this)">Contact Info</div>
        <div class="owner-section-tab" onclick="switchOwnerTab('sections', this)">Sections ${sectionCount > 0 ? '<span style="opacity:.6">(' + sectionCount + ')</span>' : ''}</div>
        <div class="owner-section-tab" onclick="switchOwnerTab('deals', this)">Deals ${dealCount > 0 ? '<span style="opacity:.6">(' + dealCount + ')</span>' : ''}</div>
        <div class="owner-section-tab" onclick="switchOwnerTab('associated', this);loadAssociatedContacts(${data.owner_id})">Associated</div>
        <div class="owner-section-tab" onclick="switchOwnerTab('activity', this)">Activities ${activityCount > 0 ? '<span style="opacity:.6">(' + activityCount + ')</span>' : ''}</div>
    </div>`;

    // ═══════════════════════════════════════════════════════════════
    // CONTACT INFO TAB
    // ═══════════════════════════════════════════════════════════════
    h += '<div id="owner-tab-contact-info" class="owner-tab-content active">';

    // ── CONTACT INFO SECTION ──
    h += `<div class="detail-card">
        <div class="detail-card-header">Contact Information</div>
        <div class="owner-info-grid">`;

    // Name breakdown
    h += `<div class="owner-info-card">
        <div class="owner-card-label">Name</div>
        <div class="owner-card-value" style="font-size:13px;color:#fff">
            ${data.first_name ? `<div><span style="color:var(--td);font-size:10px;margin-right:4px">First:</span> ${esc(data.first_name)}</div>` : ''}
            ${data.middle_name ? `<div><span style="color:var(--td);font-size:10px;margin-right:4px">Middle:</span> ${esc(data.middle_name)}</div>` : ''}
            ${data.last_name ? `<div><span style="color:var(--td);font-size:10px;margin-right:4px">Last:</span> ${esc(data.last_name)}</div>` : ''}
            ${data.suffix ? `<div><span style="color:var(--td);font-size:10px;margin-right:4px">Suffix:</span> ${esc(data.suffix)}</div>` : ''}
            ${data.entity_name ? `<div><span style="color:var(--td);font-size:10px;margin-right:4px">Entity:</span> ${esc(data.entity_name)}</div>` : ''}
        </div>
    </div>`;

    // Address card
    const addrParts = [];
    if (data.mailing_address) addrParts.push(esc(data.mailing_address));
    const csz = [data.city, data.state].filter(Boolean).join(', ') + (data.zip_code ? ' ' + data.zip_code : '');
    if (csz.trim()) addrParts.push(esc(csz));
    const mapsLink = (data.latitude && data.longitude)
        ? `<div style="margin-top:4px"><a href="https://www.google.com/maps?q=${data.latitude},${data.longitude}" target="_blank" style="color:var(--ac);font-size:11px;font-weight:600">Open in Google Maps</a></div>`
        : '';
    h += `<div class="owner-info-card">
        <div class="owner-card-label">Mailing Address</div>
        <div class="owner-card-value" style="font-size:13px;color:#fff">${addrParts.length ? addrParts.join('<br>') + mapsLink : '<span style="color:var(--td)">No address on file</span>'}</div>
    </div>`;

    h += `</div></div>`;

    // ── ALTERNATE ADDRESS ──
    if (data.alt_address) {
        const altParts = [data.alt_address, [data.alt_city, data.alt_state].filter(Boolean).join(', ') + (data.alt_zip ? ' ' + data.alt_zip : '')].filter(Boolean);
        h += `<div class="detail-card">
            <div class="detail-card-header">Alternate Addresses (1)</div>
            <div style="padding:8px 12px;background:var(--s2);border:1px solid var(--b);border-radius:6px;display:flex;justify-content:space-between;align-items:center">
                <span style="color:#fff;font-size:13px">${altParts.map(p => esc(p)).join(', ')}</span>
                ${sourceBadge('ais_sql_dump')}
            </div>
        </div>`;
    }

    // ── FINANCIAL FLAGS SECTION (only if flags exist) ──
    const flags = [
        { key: 'has_bankruptcy', label: 'Bankruptcy', color: 'var(--r)' },
        { key: 'has_lien', label: 'Lien', color: 'var(--y)' },
        { key: 'has_judgment', label: 'Judgment', color: 'var(--r)' },
        { key: 'has_evictions', label: 'Evictions', color: 'var(--y)' },
        { key: 'has_foreclosures', label: 'Foreclosures', color: 'var(--r)' },
        { key: 'has_debt', label: 'Debt', color: 'var(--y)' },
    ].filter(f => data[f.key] === 1);

    if (flags.length > 0) {
        h += `<div class="detail-card" style="border-left:3px solid var(--r)">
            <div class="detail-card-header" style="color:var(--r)">Risk Flags (${flags.length})</div>
            <div style="display:flex;flex-wrap:wrap;gap:6px">`;
        flags.forEach(f => {
            h += `<span style="display:inline-block;padding:4px 10px;border-radius:4px;font-size:11px;font-weight:600;background:rgba(255,103,29,.12);color:${f.color};border:1px solid rgba(255,103,29,.25)">${f.label}</span>`;
        });
        h += `</div></div>`;
    }

    // ── PHONE NUMBERS SECTION (sorted by last seen, with delete buttons) ──
    const phoneData = [
        { num: data.phone_1, type: data.phone_1_type, field: 'phone_1', source: data.phone_1_source, lastSeen: data.phone_1_last_seen, verified: data.phone_1_verified, verifiedBy: data.phone_1_verified_by, verifiedDate: data.phone_1_verified_date },
        { num: data.phone_2, type: data.phone_2_type, field: 'phone_2', source: data.phone_2_source, lastSeen: data.phone_2_last_seen, verified: data.phone_2_verified, verifiedBy: data.phone_2_verified_by, verifiedDate: data.phone_2_verified_date },
        { num: data.phone_3, type: data.phone_3_type, field: 'phone_3', source: data.phone_3_source, lastSeen: data.phone_3_last_seen, verified: data.phone_3_verified, verifiedBy: data.phone_3_verified_by, verifiedDate: data.phone_3_verified_date },
        { num: data.phone_4, type: data.phone_4_type, field: 'phone_4', source: data.phone_4_source, lastSeen: data.phone_4_last_seen, verified: data.phone_4_verified, verifiedBy: data.phone_4_verified_by, verifiedDate: data.phone_4_verified_date },
        { num: data.phone_5, type: data.phone_5_type, field: 'phone_5', source: data.phone_5_source, lastSeen: data.phone_5_last_seen, verified: data.phone_5_verified, verifiedBy: data.phone_5_verified_by, verifiedDate: data.phone_5_verified_date },
        { num: data.phone_6, type: data.phone_6_type, field: 'phone_6', source: data.phone_6_source, lastSeen: data.phone_6_last_seen, verified: data.phone_6_verified, verifiedBy: data.phone_6_verified_by, verifiedDate: data.phone_6_verified_date }
    ].filter(p => p.num);

    // Sort by last seen (most recent first), then verified as tiebreaker
    phoneData.sort((a, b) => {
        const aSeen = a.lastSeen ? new Date(a.lastSeen).getTime() : -Infinity;
        const bSeen = b.lastSeen ? new Date(b.lastSeen).getTime() : -Infinity;
        if (bSeen !== aSeen) return bSeen - aSeen;
        return (b.verified === 1) - (a.verified === 1);
    });

    h += `<div class="detail-card">
        <div class="detail-card-header">Phone Numbers (${phoneData.length})</div>`;
    if (phoneData.length > 0) {
        phoneData.forEach(p => {
            const srcTag = p.source ? sourceBadge(p.source) : '';
            const typeTag = p.type ? `<span class="phone-type-badge">${esc(p.type)}</span>` : '';
            const seenTag = p.lastSeen ? `<span style="font-size:10px;color:var(--td);margin-left:4px">Seen: ${esc(p.lastSeen)}</span>` : '';
            const isVerified = p.verified === 1;
            const starHtml = p.field ? `<span class="verify-star ${isVerified ? 'verified' : ''}" onclick="togglePhoneVerify(event, ${data.owner_id}, '${p.field}', ${isVerified ? 0 : 1})" title="${isVerified ? 'Verified' : 'Click to verify'}" style="cursor:pointer;margin-right:4px;font-size:16px;color:${isVerified ? 'var(--y)' : 'var(--b)'}">${isVerified ? '\u2605' : '\u2606'}</span>` : '';
            const phoneSlot = p.field ? parseInt(p.field.replace('phone_', '')) : null;
            const deleteBtn = phoneSlot ? `<button style="margin-left:auto;background:var(--r);color:#fff;border:none;border-radius:4px;padding:2px 10px;font-size:10px;font-weight:600;cursor:pointer" onclick="event.stopPropagation();deletePhoneField(${data.owner_id}, ${phoneSlot})">Delete</button>` : '';
            h += `<div style="padding:6px 0;border-bottom:1px solid var(--b);display:flex;align-items:center;gap:8px">
                ${starHtml}<a href="tel:${sanitizePhone(p.num)}" style="color:#fff;font-size:13px;text-decoration:none">${esc(formatPhone(p.num))}</a>${srcTag}${typeTag}${seenTag}${deleteBtn}
            </div>`;
        });
    } else {
        h += '<div style="color:var(--td);padding:4px;font-size:12px">No phone numbers</div>';
    }
    h += '</div>';

    // ── EMAIL ADDRESSES SECTION (with delete buttons) ──
    const emailData = [
        { addr: data.email_1, source: data.email_1_source, lastSeen: data.email_1_last_seen, field: 'email_1' },
        { addr: data.email_2, source: data.email_2_source, lastSeen: data.email_2_last_seen, field: 'email_2' },
        { addr: data.email_3, source: data.email_3_source, lastSeen: data.email_3_last_seen, field: 'email_3' },
        { addr: data.email_4, source: data.email_4_source, lastSeen: data.email_4_last_seen, field: 'email_4' }
    ].filter(e => e.addr);

    // Sort by last seen
    emailData.sort((a, b) => {
        if (a.lastSeen && b.lastSeen) return new Date(b.lastSeen) - new Date(a.lastSeen);
        if (a.lastSeen) return -1;
        if (b.lastSeen) return 1;
        return 0;
    });

    h += `<div class="detail-card">
        <div class="detail-card-header">Email Addresses (${emailData.length})</div>`;
    if (emailData.length > 0) {
        emailData.forEach(e => {
            const srcTag = e.source ? sourceBadge(e.source) : '';
            const seenTag = e.lastSeen ? `<span style="font-size:10px;color:var(--td);margin-left:4px">Seen: ${esc(e.lastSeen)}</span>` : '';
            const emailSlot = parseInt(e.field.replace('email_', ''));
            const deleteBtn = `<button style="margin-left:auto;background:var(--r);color:#fff;border:none;border-radius:4px;padding:2px 10px;font-size:10px;font-weight:600;cursor:pointer" onclick="event.stopPropagation();deleteEmailField(${data.owner_id}, ${emailSlot})">Delete</button>`;
            h += `<div style="padding:6px 0;border-bottom:1px solid var(--b);display:flex;align-items:center;gap:8px">
                <a href="mailto:${sanitizeEmail(e.addr)}" style="color:#fff;font-size:13px;text-decoration:none">${esc(e.addr)}</a>${srcTag}${seenTag}${deleteBtn}
            </div>`;
        });
    } else {
        h += '<div style="color:var(--td);padding:4px;font-size:12px">No email addresses</div>';
    }
    h += '</div>';

    // ── QUICK ACTIONS ──
    h += `<div class="detail-card">
        <div class="detail-card-header">Quick Actions</div>
        <div style="display:flex;flex-wrap:wrap;gap:6px">`;
    if (data.phone_1) {
        h += `<a href="sms:${sanitizePhone(data.phone_1)}" style="display:inline-flex;align-items:center;gap:4px;padding:5px 12px;background:var(--s2);border:1px solid var(--b);border-radius:20px;font-size:11px;color:var(--g);text-decoration:none;font-weight:600">💬 Text</a>`;
    }
    const searchName = encodeURIComponent((data.full_name || '').replace(/\b(LLC|LP|LLP|Inc|Corp|Trust|Estate)\b/gi, '').trim());
    const searchLoc = encodeURIComponent([data.city, data.state].filter(Boolean).join(' '));
    h += `<a href="https://www.linkedin.com/search/results/all/?keywords=${searchName}+${searchLoc}" target="_blank" style="display:inline-flex;align-items:center;gap:4px;padding:5px 12px;background:var(--s2);border:1px solid var(--b);border-radius:20px;font-size:11px;color:#0A66C2;text-decoration:none;font-weight:600">LinkedIn</a>`;
    h += `<a href="https://www.facebook.com/search/people/?q=${searchName}" target="_blank" style="display:inline-flex;align-items:center;gap:4px;padding:5px 12px;background:var(--s2);border:1px solid var(--b);border-radius:20px;font-size:11px;color:#1877F2;text-decoration:none;font-weight:600">Facebook</a>`;
    h += `</div></div>`;

    // ── RELATIVES SECTION ──
    let relatives = [];
    try { if (data.relatives_json) relatives = JSON.parse(data.relatives_json); } catch(e) {}
    if (relatives.length > 0) {
        h += `<div class="detail-card">
            <div class="detail-card-header">Relatives (${relatives.length})</div>`;
        relatives.forEach(rel => {
            const relAge = rel.estimated_age ? ` · Age: ${rel.estimated_age}` : '';
            const relPhone = rel.phone1 || '';
            const relEmail = rel.email1 || '';
            const relLocation = [rel.city, rel.zip].filter(Boolean).join(' ');
            const safeRelName = (rel.name || '').replace(/'/g, "\\'").replace(/\\/g, '\\\\');
            h += `<div style="padding:8px 10px;background:var(--s2);margin:4px 0;border-radius:6px;border:1px solid var(--b)">
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <span style="font-weight:500;font-size:13px;color:#fff">${esc(rel.name)}${relAge}</span>
                    <a style="font-size:10px;color:var(--ac);cursor:pointer;font-weight:600" onclick="searchRelativeInCRM('${safeRelName}')">Search in CRM</a>
                </div>
                <div style="font-size:11px;color:var(--td);margin-top:3px">
                    ${relPhone ? `<a href="tel:${relPhone}" style="color:#fff">${esc(relPhone)}</a>` : ''}
                    ${relPhone && relEmail ? ' · ' : ''}
                    ${relEmail ? `<a href="mailto:${relEmail}" style="color:#fff">${esc(relEmail)}</a>` : ''}
                    ${relLocation ? ` · ${esc(relLocation)}` : ''}
                </div>
            </div>`;
        });
        h += '</div>';
    }

    // ── NOTES SECTION ──
    const contactNotes = data.contact_notes || [];
    h += `<div class="detail-card">
        <div class="detail-card-header">Notes (${contactNotes.length})</div>
        <div style="margin-bottom:12px">
            <textarea id="new-note-body" rows="2" style="width:100%;resize:vertical;font-size:13px" placeholder="Add a note..."></textarea>
            <button class="bp" style="margin-top:6px;font-size:12px;padding:6px 14px" onclick="addContactNote(${data.owner_id})">Add Note</button>
        </div>`;
    if (contactNotes.length > 0) {
        contactNotes.forEach(n => {
            h += `<div style="padding:8px 10px;background:var(--s2);margin:4px 0;border-radius:6px;border:1px solid var(--b);font-size:13px">
                <div style="white-space:pre-wrap;color:#fff">${esc(n.body)}</div>
                <div style="display:flex;justify-content:space-between;align-items:center;margin-top:6px">
                    <span style="font-size:10px;color:var(--td)">${n.user_name || ''} · ${new Date(n.created_at).toLocaleString()}</span>
                    <span style="font-size:10px;color:var(--r);cursor:pointer" onclick="deleteContactNote(${n.note_id}, ${data.owner_id})">Delete</span>
                </div>
            </div>`;
        });
    } else if (data.notes) {
        h += `<div style="padding:8px 10px;background:var(--s2);border-radius:6px;border:1px solid var(--b);font-size:13px">
            <div style="white-space:pre-wrap;color:#fff">${esc(data.notes)}</div>
            <div style="font-size:10px;color:var(--td);margin-top:4px">Legacy note (imported)</div>
        </div>`;
    } else {
        h += '<div style="color:var(--td);padding:4px;font-size:12px">No notes yet</div>';
    }
    h += '</div>';

    h += '</div>'; // end contact-info tab

    // ═══════════════════════════════════════════════════════════════
    // SECTIONS TAB
    // ═══════════════════════════════════════════════════════════════
    h += '<div id="owner-tab-sections" class="owner-tab-content">';
    if (sectionCount > 0) {
        data.sections.forEach(s => {
            const details = [s.nra ? s.nra + ' NRA' : '', s.parish_name || ''].filter(Boolean).join(' · ');
            h += `<div style="padding:8px 10px;background:var(--s2);margin:4px 0;border-radius:6px;font-size:12px;display:flex;justify-content:space-between;align-items:center;border:1px solid var(--b)">
                <span style="color:var(--ac);cursor:pointer;font-weight:500" onclick="viewSectionDetail(${s.section_id})">${esc(s.display_name)}</span>
                <span style="color:var(--td);font-size:11px">${details}</span>
            </div>`;
        });
    } else {
        h += '<div style="padding:16px;color:var(--td);text-align:center;font-size:13px">No linked sections</div>';
    }
    h += '</div>';

    // ═══════════════════════════════════════════════════════════════
    // DEALS TAB
    // ═══════════════════════════════════════════════════════════════
    h += '<div id="owner-tab-deals" class="owner-tab-content">';
    if (dealCount > 0) {
        data.deals.forEach(d => {
            h += `<div style="padding:8px 10px;background:var(--s2);margin:4px 0;border-radius:6px;font-size:12px;border:1px solid var(--b)">
                <div style="font-weight:500;color:#fff">${esc(d.title)}</div>
                <div style="color:var(--td);margin-top:3px;font-size:11px">${d.stage_name || 'No stage'} · ${esc(d.section_name || '')} · ${formatCurrency(d.value || 0)}</div>
            </div>`;
        });
    } else {
        h += '<div style="padding:16px;color:var(--td);text-align:center;font-size:13px">No deals</div>';
    }
    h += '</div>';

    // ═══════════════════════════════════════════════════════════════
    // ASSOCIATED TAB
    // ═══════════════════════════════════════════════════════════════
    h += '<div id="owner-tab-associated" class="owner-tab-content">';
    h += '<div id="associated-content" style="padding:16px;color:var(--td);text-align:center;font-size:13px">Click to load associated contacts</div>';
    h += '</div>';

    // ═══════════════════════════════════════════════════════════════
    // ACTIVITIES TAB
    // ═══════════════════════════════════════════════════════════════
    h += '<div id="owner-tab-activity" class="owner-tab-content">';
    if (activityCount > 0) {
        data.activities.slice(0, 20).forEach(a => {
            h += `<div style="padding:8px 0;border-bottom:1px solid var(--b);font-size:12px">
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <strong style="text-transform:capitalize;color:var(--ac)">${esc(a.type)}</strong>
                    <span style="color:var(--td);font-size:10px">${new Date(a.created_at).toLocaleDateString()}</span>
                </div>
                <div style="margin-top:3px;color:#fff">${esc(a.subject || a.body || '')}</div>
                ${a.user_name ? `<div style="color:var(--td);font-size:10px;margin-top:2px">by ${esc(a.user_name)}</div>` : ''}
            </div>`;
        });
    } else {
        h += '<div style="padding:16px;color:var(--td);text-align:center;font-size:13px">No activity logged</div>';
    }
    h += '</div>';

    document.getElementById('panel-body').innerHTML = h;
    document.getElementById('owner-panel').classList.add('open');
}

/**
 * switchOwnerTab(tab, el)
 * Switches between tabs in the contact detail panel (sections, deals, activity)
 */
function switchOwnerTab(tab, el) {
    document.querySelectorAll('.owner-section-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.owner-tab-content').forEach(c => c.classList.remove('active'));
    if (el) {
        el.classList.add('active');
    } else {
        document.querySelector('.owner-section-tab').classList.add('active');
    }
    document.getElementById(`owner-tab-${tab}`).classList.add('active');
}

/**
 * closeOwnerPanel()
 * Closes the contact detail panel
 */
function closeOwnerPanel() {
    document.getElementById('owner-panel').classList.remove('open');
}

/**
 * searchRelativeInCRM(name)
 * Searches for a relative's name in the contacts page — safe from inline JS injection
 */
function searchRelativeInCRM(name) {
    closeOwnerPanel();
    document.getElementById('owners-search').value = name;
    setPage('owners');
}

/**
 * loadAssociatedContacts(ownerId)
 * Lazy-loads associated contacts when the tab is clicked
 */
async function loadAssociatedContacts(ownerId) {
    const container = document.getElementById('associated-content');
    if (!container) return;
    container.innerHTML = '<div style="padding:16px;color:var(--td);text-align:center;font-size:13px">Loading...</div>';

    const data = await apiCall(`/owners/${ownerId}/associated`);
    if (!data || data.length === 0) {
        container.innerHTML = '<div style="padding:16px;color:var(--td);text-align:center;font-size:13px">No associated contacts found</div>';
        return;
    }

    let h = '';
    const byPhone = data.filter(a => a.match_type === 'phone');
    const byEmail = data.filter(a => a.match_type === 'email');
    const byAddr  = data.filter(a => a.match_type === 'address');

    if (byPhone.length > 0) {
        h += `<div style="font-size:11px;color:var(--td);text-transform:uppercase;letter-spacing:.4px;font-weight:600;margin-bottom:6px;margin-top:8px">Shared Phone (${byPhone.length})</div>`;
        byPhone.forEach(a => {
            h += `<div style="padding:8px 10px;background:var(--s2);margin:4px 0;border-radius:6px;font-size:12px;display:flex;justify-content:space-between;align-items:center;border:1px solid var(--b);cursor:pointer" onclick="viewOwnerDetail(${a.owner_id})">
                <div><span style="color:var(--ac);font-weight:500">${esc(a.full_name)}</span>${a.classification ? ' ' + classBadge(a.classification) : ''}</div>
                <div style="text-align:right"><div style="color:var(--td);font-size:11px">${esc(formatPhone(a.phone_1 || ''))}</div></div>
            </div>`;
        });
    }
    if (byEmail.length > 0) {
        h += `<div style="font-size:11px;color:var(--td);text-transform:uppercase;letter-spacing:.4px;font-weight:600;margin-bottom:6px;margin-top:12px">Shared Email (${byEmail.length})</div>`;
        byEmail.forEach(a => {
            h += `<div style="padding:8px 10px;background:var(--s2);margin:4px 0;border-radius:6px;font-size:12px;display:flex;justify-content:space-between;align-items:center;border:1px solid var(--b);cursor:pointer" onclick="viewOwnerDetail(${a.owner_id})">
                <div><span style="color:var(--ac);font-weight:500">${esc(a.full_name)}</span>${a.classification ? ' ' + classBadge(a.classification) : ''}</div>
                <div style="text-align:right"><div style="color:var(--td);font-size:11px">${esc(a.email_1 || '')}</div></div>
            </div>`;
        });
    }
    if (byAddr.length > 0) {
        h += `<div style="font-size:11px;color:var(--td);text-transform:uppercase;letter-spacing:.4px;font-weight:600;margin-bottom:6px;margin-top:12px">Same Address (${byAddr.length})</div>`;
        byAddr.forEach(a => {
            h += `<div style="padding:8px 10px;background:var(--s2);margin:4px 0;border-radius:6px;font-size:12px;display:flex;justify-content:space-between;align-items:center;border:1px solid var(--b);cursor:pointer" onclick="viewOwnerDetail(${a.owner_id})">
                <div><span style="color:var(--ac);font-weight:500">${esc(a.full_name)}</span>${a.classification ? ' ' + classBadge(a.classification) : ''}</div>
                <div style="color:var(--td);font-size:11px">${esc(a.city || '')}${a.state ? ', ' + esc(a.state) : ''}</div>
            </div>`;
        });
    }
    container.innerHTML = h;
}

/**
 * showCreateDealForm(ownerId, ownerName)
 * Opens a modal form to create a new deal for a contact
 */
async function showCreateDealForm(ownerId, ownerName) {
    // Load sections and stages for the form
    const lookups = await apiCall('/lookups');
    if (!lookups) return;
    const sections = await apiCall('/sections?page=1&per_page=1000&sort=display_name&order=asc');
    if (!sections) return;

    let formHtml = `<div id="create-deal-form" style="position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.6);z-index:2000;display:flex;align-items:center;justify-content:center" onclick="if(event.target===this)this.remove()">
        <div style="background:var(--s);border:1px solid var(--b);border-radius:var(--rad);padding:24px;width:420px;max-height:80vh;overflow-y:auto">
            <h3 style="margin-bottom:16px">Create Deal for ${esc(ownerName)}</h3>
            <div style="margin-bottom:12px">
                <label style="font-size:12px;color:var(--td);display:block;margin-bottom:4px">Deal Title</label>
                <input type="text" id="deal-title" style="width:100%" value="${esc(ownerName)} - ">
            </div>
            <div style="margin-bottom:12px">
                <label style="font-size:12px;color:var(--td);display:block;margin-bottom:4px">Section</label>
                <select id="deal-section" style="width:100%">
                    <option value="">Select section...</option>
                    ${(sections.sections || []).map(s => `<option value="${s.section_id}">${esc(s.display_name)}</option>`).join('')}
                </select>
            </div>
            <div style="margin-bottom:12px">
                <label style="font-size:12px;color:var(--td);display:block;margin-bottom:4px">Stage</label>
                <select id="deal-stage" style="width:100%">
                    ${(lookups.pipeline_stages || []).map(s => `<option value="${s.stage_id}">${esc(s.name)}</option>`).join('')}
                </select>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
                <div>
                    <label style="font-size:12px;color:var(--td);display:block;margin-bottom:4px">NRA</label>
                    <input type="number" id="deal-nra" style="width:100%" step="0.00000001">
                </div>
                <div>
                    <label style="font-size:12px;color:var(--td);display:block;margin-bottom:4px">Price/NRA</label>
                    <input type="number" id="deal-price" style="width:100%" step="1">
                </div>
            </div>
            <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px">
                <button class="bs" onclick="document.getElementById('create-deal-form').remove()">Cancel</button>
                <button class="bp" onclick="createDealFromContact(${ownerId})">Create Deal</button>
            </div>
        </div>
    </div>`;
    document.body.insertAdjacentHTML('beforeend', formHtml);
}

/**
 * createDealFromContact(ownerId)
 * Submits the create deal form and creates a new deal for the contact
 */
async function createDealFromContact(ownerId) {
    const title = document.getElementById('deal-title').value.trim();
    const sectionId = document.getElementById('deal-section').value;
    const stageId = document.getElementById('deal-stage').value;
    const nra = parseFloat(document.getElementById('deal-nra').value) || null;
    const pricePerNra = parseFloat(document.getElementById('deal-price').value) || null;

    if (!title || !sectionId || !stageId) {
        alert('Title, section, and stage are required.');
        return;
    }

    const value = (nra && pricePerNra) ? nra * pricePerNra : null;

    const resp = await apiCall('/deals', 'POST', {
        owner_id: ownerId,
        section_id: parseInt(sectionId),
        stage_id: parseInt(stageId),
        title,
        nra,
        price_per_nra: pricePerNra,
        value
    });

    if (resp) {
        document.getElementById('create-deal-form').remove();
        viewOwnerDetail(ownerId); // Refresh panel
    }
}

/**
 * updateContactStatus(ownerId, newStatus)
 * Updates the contact status and refreshes the detail panel
 */
async function updateContactStatus(ownerId, newStatus) {
    if (!newStatus) return;
    const resp = await apiCall(`/owners/${ownerId}`, 'PUT', { contact_status: newStatus });
    if (resp) {
        viewOwnerDetail(ownerId);
    }
}

/**
 * addContactNote(ownerId)
 * Adds a new note to the contact
 */
async function addContactNote(ownerId) {
    const body = document.getElementById('new-note-body').value.trim();
    if (!body) return;
    const resp = await apiCall(`/owners/${ownerId}/notes`, 'POST', { body });
    if (resp) {
        viewOwnerDetail(ownerId); // Refresh panel
    }
}

/**
 * deleteContactNote(noteId, ownerId)
 * Deletes a note from the contact
 */
async function deleteContactNote(noteId, ownerId) {
    const resp = await apiCall(`/notes/${noteId}`, 'DELETE');
    if (resp) {
        viewOwnerDetail(ownerId); // Refresh panel
    }
}

/**
 * togglePhoneVerify(event, ownerId, phoneField, newValue)
 * Toggles the verified status of a phone number
 */
async function togglePhoneVerify(event, ownerId, phoneField, newValue) {
    event.preventDefault();
    event.stopPropagation();
    const resp = await apiCall(`/owners/${ownerId}/verify-phone`, 'PUT', { phone_field: phoneField, verified: newValue });
    if (resp) {
        viewOwnerDetail(ownerId); // Refresh panel
    }
}

/**
 * toggleDNC(ownerId, newValue)
 * Toggles Do Not Contact flag on a contact
 */
async function toggleDNC(ownerId, newValue) {
    let reason = '';
    if (newValue === 1) {
        reason = prompt('Reason for Do Not Contact:');
        if (reason === null) return; // cancelled
    }
    const today = new Date().toISOString().split('T')[0];
    const resp = await apiCall(`/owners/${ownerId}`, 'PUT', {
        do_not_contact: newValue,
        dnc_reason: newValue ? reason : '',
        dnc_date: newValue ? today : ''
    });
    if (resp) viewOwnerDetail(ownerId);
}

/**
 * showReserveForm(ownerId)
 * Shows a form to reserve a contact for a specific buyer
 */
async function showReserveForm(ownerId) {
    const lookups = await apiCall('/lookups');
    if (!lookups) return;
    let formHtml = `<div id="reserve-form" style="position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.6);z-index:2000;display:flex;align-items:center;justify-content:center" onclick="if(event.target===this)this.remove()">
        <div style="background:var(--s);border:1px solid var(--b);border-radius:var(--rad);padding:24px;width:380px">
            <h3 style="margin-bottom:16px;color:var(--y)">🔒 Reserve Contact</h3>
            <div style="margin-bottom:12px">
                <label style="font-size:12px;color:var(--td);display:block;margin-bottom:4px">Reserve for Buyer</label>
                <select id="reserve-user" style="width:100%">
                    ${(lookups.users || []).map(u => `<option value="${u.user_id}">${esc(u.name)}</option>`).join('')}
                </select>
            </div>
            <div style="margin-bottom:12px">
                <label style="font-size:12px;color:var(--td);display:block;margin-bottom:4px">Reason</label>
                <input type="text" id="reserve-reason" style="width:100%" placeholder="e.g. Existing relationship, active deal...">
            </div>
            <div style="display:flex;gap:8px;justify-content:flex-end">
                <button class="bs" onclick="document.getElementById('reserve-form').remove()">Cancel</button>
                <button class="bp" style="background:var(--y)" onclick="submitReservation(${ownerId})">Reserve</button>
            </div>
        </div>
    </div>`;
    document.body.insertAdjacentHTML('beforeend', formHtml);
}

/**
 * submitReservation(ownerId)
 * Submits the reservation form
 */
async function submitReservation(ownerId) {
    const userId = document.getElementById('reserve-user').value;
    const reason = document.getElementById('reserve-reason').value.trim();
    const today = new Date().toISOString().split('T')[0];
    const resp = await apiCall(`/owners/${ownerId}`, 'PUT', {
        reserved_for_user_id: parseInt(userId),
        reserved_reason: reason,
        reserved_date: today
    });
    if (resp) {
        document.getElementById('reserve-form').remove();
        viewOwnerDetail(ownerId);
    }
}

/**
 * unreserveContact(ownerId)
 * Removes the reservation from a contact
 */
async function unreserveContact(ownerId) {
    if (!confirm('Remove reservation from this contact?')) return;
    const resp = await apiCall(`/owners/${ownerId}`, 'PUT', {
        reserved_for_user_id: null,
        reserved_reason: null,
        reserved_date: null
    });
    if (resp) viewOwnerDetail(ownerId);
}

/**
 * deletePhoneField(ownerId, slot)
 * Deletes a specific phone slot (1-6) from a contact
 */
async function deletePhoneField(ownerId, slot) {
    if (!confirm(`Delete phone ${slot}? This cannot be undone.`)) return;
    const resp = await fetch(`/api/owners/${ownerId}/phone/${slot}`, {
        method: 'DELETE',
        headers: {'Content-Type': 'application/json'}
    });
    if (resp.ok) {
        viewOwnerDetail(ownerId);
    } else {
        alert('Failed to delete phone');
    }
}

/**
 * deleteEmailField(ownerId, slot)
 * Deletes a specific email slot (1-4) from a contact
 */
async function deleteEmailField(ownerId, slot) {
    if (!confirm(`Delete email ${slot}? This cannot be undone.`)) return;
    const resp = await fetch(`/api/owners/${ownerId}/email/${slot}`, {
        method: 'DELETE',
        headers: {'Content-Type': 'application/json'}
    });
    if (resp.ok) {
        viewOwnerDetail(ownerId);
    } else {
        alert('Failed to delete email');
    }
}
