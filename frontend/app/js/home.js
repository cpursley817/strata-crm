/**
 * home.js
 * Powers the Home/Dashboard page of Strata CRM
 *
 * This file contains:
 * - Dashboard data loading and rendering
 * - Filter dropdown population
 * - Global state for filter preferences
 */

let usersLoaded = false;

/**
 * loadDashboard()
 * Fetches and renders the home dashboard with personal stats, pipeline summary, and data coverage metrics
 */
async function loadDashboard() {
    // Load both personal dashboard and global stats in parallel
    const [dash, stats] = await Promise.all([
        apiCall('/dashboard'),
        apiCall('/stats')
    ]);

    // Welcome message
    if (currentUser) {
        document.getElementById('welcome-user').textContent = `Welcome back, ${currentUser.name || 'User'}`;
    }

    // Personal stats
    if (dash) {
        document.getElementById('stat-sections').textContent = (dash.my_sections || 0).toLocaleString();
        document.getElementById('stat-deals').textContent = (dash.my_open_deals || 0).toLocaleString();
        document.getElementById('stat-deal-value').textContent = formatCurrency(dash.my_deal_value || 0);

        // Pipeline summary
        const pipeDiv = document.getElementById('home-pipeline-summary');
        if (dash.pipeline_summary && dash.pipeline_summary.length > 0) {
            pipeDiv.innerHTML = dash.pipeline_summary.map(s => {
                const count = s.deal_count || 0;
                const value = s.stage_value || 0;
                return `<div style="background:var(--s2);border:1px solid var(--b);border-radius:6px;padding:8px 14px;text-align:center;min-width:100px;cursor:pointer;transition:border-color .15s" onclick="setPage('pipeline')" onmouseover="this.style.borderColor='var(--ac)'" onmouseout="this.style.borderColor='var(--b)'">
                    <div style="font-size:18px;font-weight:700;color:${count > 0 ? 'var(--t)' : 'var(--td)'}">${count}</div>
                    <div style="font-size:10px;color:var(--td);text-transform:uppercase;letter-spacing:.3px">${esc(s.stage_name)}</div>
                    ${value > 0 ? `<div style="font-size:11px;color:var(--g);font-weight:600;margin-top:2px">${formatCurrency(value)}</div>` : ''}
                </div>`;
            }).join('');
        } else {
            pipeDiv.innerHTML = '<div style="color:var(--td);padding:8px;font-size:13px">No pipeline stages. Import deals to see your pipeline.</div>';
        }
    }

    // Global stats for totals
    if (stats) {
        document.getElementById('stat-owners').textContent = (stats.total_owners || 0).toLocaleString();

        // Data coverage (phone %, email %)
        const phoneRate = stats.total_owners > 0 ? ((stats.total_with_phone / stats.total_owners) * 100).toFixed(1) : 0;
        const emailRate = stats.total_owners > 0 ? ((stats.total_with_email / stats.total_owners) * 100).toFixed(1) : 0;
        let coverageHtml = `
            <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--b)">
                <span style="color:var(--td);font-size:13px">Has Phone</span>
                <span style="font-weight:600">${(stats.total_with_phone || 0).toLocaleString()} <span style="color:var(--g);font-size:12px">(${phoneRate}%)</span></span>
            </div>
            <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--b)">
                <span style="color:var(--td);font-size:13px">Has Email</span>
                <span style="font-weight:600">${(stats.total_with_email || 0).toLocaleString()} <span style="color:var(--g);font-size:12px">(${emailRate}%)</span></span>
            </div>
            <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--b)">
                <span style="color:var(--td);font-size:13px">Total Sections</span>
                <span style="font-weight:600">${(stats.total_sections || 0).toLocaleString()}</span>
            </div>
            <div style="display:flex;justify-content:space-between;padding:8px 0">
                <span style="color:var(--td);font-size:13px">Total Deals</span>
                <span style="font-weight:600">${(stats.total_deals || 0).toLocaleString()}</span>
            </div>`;
        document.getElementById('classification-summary').innerHTML = coverageHtml;

        // Recent activity / contact status summary
        let contactSum = '';
        if (stats.owners_by_contact_status) {
            contactSum = Object.entries(stats.owners_by_contact_status)
                .filter(([k]) => k && k !== 'None')
                .sort((a,b) => b[1] - a[1])
                .map(([k, v]) => `<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--b);cursor:pointer" onclick="setPage('owners')">${statusBadge(k)} <strong>${v.toLocaleString()}</strong></div>`)
                .join('');
        }
        document.getElementById('contact-summary').innerHTML = contactSum || '<div style="color:var(--td);padding:8px">No activity data</div>';
    }
}

/**
 * loadParishes()
 * Populates the parish and user filter dropdowns on the Sections page
 */
async function loadParishes() {
    if (parishesLoaded) return;
    const parishes = await apiCall('/sections/parishes');
    if (!parishes) return;
    const select = document.getElementById('sections-parish-filter');
    while (select.options.length > 1) select.remove(1);
    parishes.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.parish_id;
        opt.textContent = `${p.name} (${p.section_count})`;
        select.appendChild(opt);
    });
    parishesLoaded = true;
}

let operatorsLoaded = false;

/**
 * loadOperators()
 * Populates the operator filter dropdown on the Sections page
 */
async function loadOperators() {
    if (operatorsLoaded) return;
    const operators = await apiCall('/sections/operators');
    if (!operators) return;
    const select = document.getElementById('sections-operator-filter');
    while (select.options.length > 1) select.remove(1);
    operators.forEach(o => {
        const opt = document.createElement('option');
        opt.value = o.operator_id;
        opt.textContent = `${o.name} (${o.section_count})`;
        select.appendChild(opt);
    });
    operatorsLoaded = true;
}
