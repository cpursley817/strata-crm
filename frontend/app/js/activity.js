/**
 * activity.js
 * Powers the Activity Log page (Personal Tracker)
 *
 * This file contains:
 * - Activity loading and rendering
 * - Activity type and date filtering
 * - Activity form for logging new activities
 * - Owner search functionality in the form
 */

/**
 * loadActivities(page)
 * Fetches and renders activities with stats and filtering
 */
async function loadActivities(page = 1) {
    const typeFilter = document.getElementById('activity-type-filter').value;
    const dateFilter = document.getElementById('activity-date-filter').value;

    // Scope to current user
    const userId = currentUser ? currentUser.user_id : '';
    let url = `/activities?page=${page}&per_page=50`;
    if (userId) url += `&user_id=${userId}`;
    if (typeFilter) url += `&type=${encodeURIComponent(typeFilter)}`;

    // Date filtering
    if (dateFilter) {
        const now = new Date();
        let startDate = '';
        if (dateFilter === 'today') startDate = now.toISOString().split('T')[0];
        else if (dateFilter === 'week') {
            const d = new Date(now); d.setDate(d.getDate() - 7);
            startDate = d.toISOString().split('T')[0];
        } else if (dateFilter === 'month') {
            const d = new Date(now); d.setDate(d.getDate() - 30);
            startDate = d.toISOString().split('T')[0];
        }
        if (startDate) url += `&start_date=${startDate}`;
    }

    const data = await apiCall(url);
    if (!data) return;

    // Activity stats
    const statsDiv = document.getElementById('activity-stats');
    const total = data.total || 0;
    const actTypes = {};
    (data.activities || []).forEach(a => {
        actTypes[a.type] = (actTypes[a.type] || 0) + 1;
    });
    let statsHtml = `<div style="background:var(--s);border:1px solid var(--b);border-radius:var(--rad);padding:8px 16px;text-align:center">
        <div style="font-size:18px;font-weight:700">${total}</div>
        <div style="font-size:10px;color:var(--td);text-transform:uppercase">Total</div>
    </div>`;
    const typeIcons = {call:'📞', voicemail:'📱', text:'💬', email:'📧', letter:'📬', note:'📝', document:'📄', meeting:'🤝'};
    Object.entries(actTypes).sort((a,b) => b[1] - a[1]).forEach(([type, count]) => {
        statsHtml += `<div style="background:var(--s);border:1px solid var(--b);border-radius:var(--rad);padding:8px 16px;text-align:center">
            <div style="font-size:18px;font-weight:700">${count}</div>
            <div style="font-size:10px;color:var(--td);text-transform:uppercase">${typeIcons[type] || ''} ${type}</div>
        </div>`;
    });
    statsDiv.innerHTML = statsHtml;

    const list = document.getElementById('activities-list');
    if (!data.activities || data.activities.length === 0) {
        list.innerHTML = '<div style="padding:40px;text-align:center;color:var(--td)">No activities recorded yet. Click "+ Log Activity" to start tracking.</div>';
        return;
    }

    list.innerHTML = data.activities.map(a => `
        <div class="activity-item">
            <div class="activity-content">
                <div style="display:flex;gap:8px;align-items:center">
                    <span style="font-size:16px">${typeIcons[a.type] || '📝'}</span>
                    <strong style="text-transform:capitalize;color:var(--ac)">${esc(a.type || 'note')}</strong>
                    ${a.owner_name ? `<span style="color:var(--td)">— <span style="color:var(--ac);cursor:pointer" onclick="viewOwnerDetail(${a.owner_id})">${esc(a.owner_name)}</span></span>` : ''}
                    ${a.section_name ? `<span style="color:var(--td)">| ${esc(a.section_name)}</span>` : ''}
                    ${a.call_outcome ? `<span style="font-size:11px;padding:1px 6px;border-radius:8px;background:var(--b);color:var(--td)">${esc(a.call_outcome)}</span>` : ''}
                </div>
                <div style="margin-top:4px;font-size:13px">${esc(a.subject || a.body || '')}</div>
                <div class="activity-time">${new Date(a.created_at).toLocaleString()}</div>
            </div>
        </div>
    `).join('');
}

/**
 * showLogActivityForm()
 * Opens a modal form to log a new activity with owner search
 */
function showLogActivityForm() {
    let formHtml = `<div id="log-activity-form" style="position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.6);z-index:2000;display:flex;align-items:center;justify-content:center" onclick="if(event.target===this)this.remove()">
        <div style="background:var(--s);border:1px solid var(--b);border-radius:var(--rad);padding:24px;width:420px">
            <h3 style="margin-bottom:16px">Log Activity</h3>
            <div style="margin-bottom:12px">
                <label style="font-size:12px;color:var(--td);display:block;margin-bottom:4px">Type</label>
                <select id="log-type" style="width:100%">
                    <option value="call">Call</option>
                    <option value="voicemail">Voicemail</option>
                    <option value="text">Text</option>
                    <option value="email">Email</option>
                    <option value="letter">Letter</option>
                    <option value="note">Note</option>
                    <option value="document">Document</option>
                    <option value="meeting">Meeting</option>
                </select>
            </div>
            <div style="margin-bottom:12px">
                <label style="font-size:12px;color:var(--td);display:block;margin-bottom:4px">Owner (search by name)</label>
                <input type="text" id="log-owner-search" style="width:100%" placeholder="Start typing owner name...">
                <div id="log-owner-results" style="max-height:120px;overflow-y:auto;margin-top:4px"></div>
                <input type="hidden" id="log-owner-id">
            </div>
            <div style="margin-bottom:12px">
                <label style="font-size:12px;color:var(--td);display:block;margin-bottom:4px">Subject</label>
                <input type="text" id="log-subject" style="width:100%">
            </div>
            <div style="margin-bottom:12px">
                <label style="font-size:12px;color:var(--td);display:block;margin-bottom:4px">Details</label>
                <textarea id="log-body" rows="3" style="width:100%;resize:vertical"></textarea>
            </div>
            <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px">
                <button class="bs" onclick="document.getElementById('log-activity-form').remove()">Cancel</button>
                <button class="bp" onclick="submitLogActivity()">Log It</button>
            </div>
        </div>
    </div>`;
    document.body.insertAdjacentHTML('beforeend', formHtml);

    // Owner search with debounce
    let ownerTimer;
    document.getElementById('log-owner-search').addEventListener('input', function() {
        clearTimeout(ownerTimer);
        const q = this.value.trim();
        if (q.length < 2) { document.getElementById('log-owner-results').innerHTML = ''; return; }
        ownerTimer = setTimeout(async () => {
            const data = await apiCall(`/owners?page=1&per_page=8&search=${encodeURIComponent(q)}`);
            if (!data) return;
            document.getElementById('log-owner-results').innerHTML = (data.owners || []).map(o =>
                `<div style="padding:6px 8px;cursor:pointer;font-size:13px;border-bottom:1px solid var(--b)" onclick="document.getElementById('log-owner-id').value=${o.owner_id};document.getElementById('log-owner-search').value='${esc(o.full_name)}';document.getElementById('log-owner-results').innerHTML=''">${esc(o.full_name)} <span style="color:var(--td);font-size:11px">${o.city ? o.city + ', ' : ''}${o.state || ''}</span></div>`
            ).join('');
        }, 300);
    });
}

/**
 * submitLogActivity()
 * Submits the activity log form and creates a new activity record
 */
async function submitLogActivity() {
    const type = document.getElementById('log-type').value;
    const ownerId = document.getElementById('log-owner-id').value;
    const subject = document.getElementById('log-subject').value.trim();
    const body = document.getElementById('log-body').value.trim();

    if (!ownerId) { alert('Please select an owner.'); return; }
    if (!subject && !body) { alert('Please enter a subject or details.'); return; }

    const resp = await apiCall('/activities', 'POST', {
        owner_id: parseInt(ownerId),
        type,
        subject,
        body
    });

    if (resp) {
        document.getElementById('log-activity-form').remove();
        loadActivities();
    }
}
