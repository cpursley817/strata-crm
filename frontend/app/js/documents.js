/**
 * documents.js
 * Powers the Document Templates page
 *
 * This file contains:
 * - Document template list and filtering
 * - Document card rendering
 */

// ===== DOCUMENTS PAGE =====
const DOCUMENTS = [
    { title: 'LA Offer Letter 2024', type: 'offer', file: 'LA_OFFER LETTER_ 2024.docx', desc: 'Standard mineral acquisition offer letter for Louisiana properties' },
    { title: 'PSA — Standard', type: 'psa', file: 'LA_PSA_TEMPLATE_BBRHTX.docx', desc: 'Purchase & Sales Agreement — standard template' },
    { title: 'PSA — Joinder', type: 'psa', file: 'LA_PSA_TEMPLATE_BBRHTX (Joinder).docx', desc: 'PSA template for joinder transactions' },
    { title: 'PSA — Royalty', type: 'psa', file: 'LA_PSA_ROYALTY_TEMPLATE.docx', desc: 'Royalty-specific Purchase & Sales Agreement' },
    { title: 'PSA — Royalty (Prescription)', type: 'psa', file: 'LA_PSA_ROYALTY_PRESCRIPTION_TEMPLATE.docx', desc: 'Royalty PSA with prescription provisions' },
    { title: 'PSA — Mesa', type: 'psa', file: 'LA_PSA_MESA_TEMPLATE.docx', desc: 'Mesa-specific PSA template' },
    { title: 'OOP Closing (No PSA)', type: 'oop', file: 'BBR- OOP-NO PSA Closing.docx', desc: 'Out-of-pocket closing without PSA' },
    { title: 'OOP Closing + PSA (10-Day)', type: 'oop', file: 'BBR- OOP-PSA Closing- 10 Day Payment.docx', desc: 'OOP closing with PSA, 10-day payment terms' },
    { title: 'OOP Closing (Broker)', type: 'oop', file: 'BBR-BROKER- OOP Closing.docx', desc: 'Broker OOP closing template' },
    { title: 'OOP — Royalty Only', type: 'oop', file: 'LA_ROYALTY ONLY_ OOP.docx', desc: 'Royalty-only out-of-pocket closing' },
    { title: 'Mail Merge Template v3', type: 'merge', file: 'MailMerge_Word_Template_v3.docx', desc: 'Bulk mail merge template for owner outreach' }
];

let currentDocFilter = 'all';

/**
 * loadDocuments()
 * Initializes the documents page by rendering all templates
 */
function loadDocuments() {
    renderDocuments();
}

/**
 * filterDocs(type, btn)
 * Filters documents by type and updates the active button
 */
function filterDocs(type, btn) {
    currentDocFilter = type;
    document.querySelectorAll('.doc-type-btn').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');
    renderDocuments();
}

/**
 * renderDocuments()
 * Renders the filtered document cards to the grid
 */
function renderDocuments() {
    const grid = document.getElementById('documents-grid');
    const filtered = currentDocFilter === 'all' ? DOCUMENTS : DOCUMENTS.filter(d => d.type === currentDocFilter);

    const typeBadge = (type) => {
        const m = {psa:'background:rgba(0,180,81,.15);color:var(--g);border:1px solid rgba(0,180,81,.3)',
                   offer:'background:rgba(91,159,255,.15);color:#5b9fff;border:1px solid rgba(91,159,255,.3)',
                   oop:'background:rgba(255,167,38,.15);color:var(--y);border:1px solid rgba(255,167,38,.3)',
                   merge:'background:rgba(156,107,255,.15);color:var(--p);border:1px solid rgba(156,107,255,.3)'};
        return `<span style="display:inline-block;padding:2px 9px;border-radius:12px;font-size:10px;font-weight:700;letter-spacing:.4px;text-transform:uppercase;${m[type] || ''}">${type}</span>`;
    };

    grid.innerHTML = filtered.map(doc => `
        <div class="document-card">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px">
                <div style="font-size:14px;font-weight:600;color:var(--t);line-height:1.3">${esc(doc.title)}</div>
                ${typeBadge(doc.type)}
            </div>
            <div style="color:var(--td);font-size:12px;margin-top:8px;line-height:1.5;flex:1">${esc(doc.desc)}</div>
            <div style="margin-top:12px;font-size:11px;color:var(--td);font-family:monospace">${esc(doc.file)}</div>
        </div>
    `).join('');
}
