/**
 * pipeline.js
 * Powers the Deal Pipeline Kanban board page
 *
 * This file contains:
 * - Pipeline loading and Kanban rendering
 * - Deal dragging and stage transitions
 */

/**
 * loadPipeline()
 * Fetches and renders the Kanban board with deals organized by stage
 */
async function loadPipeline() {
    const data = await apiCall('/deals?pipeline=Haynesville&status=open');
    if (!data) return;

    // Pipeline summary stats
    const statsDiv = document.getElementById('pipeline-stats');
    const totalDeals = data.total_deals || 0;
    const totalValue = data.total_value || 0;
    const stageCount = data.stages ? data.stages.length : 0;
    statsDiv.innerHTML = `
        <div class="pipeline-stat-card"><div class="pipeline-stat-value">${totalDeals}</div><div class="pipeline-stat-label">Open Deals</div></div>
        <div class="pipeline-stat-card"><div class="pipeline-stat-value">${formatCurrency(totalValue)}</div><div class="pipeline-stat-label">Total Value</div></div>
        <div class="pipeline-stat-card"><div class="pipeline-stat-value">${stageCount}</div><div class="pipeline-stat-label">Stages</div></div>
    `;

    const board = document.getElementById('kanban-board');
    board.innerHTML = '';

    if (!data.stages || data.stages.length === 0) {
        board.innerHTML = '<div style="padding:40px;text-align:center;color:var(--td)">No pipeline stages found. Import deals to see the pipeline.</div>';
        return;
    }

    data.stages.forEach(stageGroup => {
        const stageId = stageGroup.stage?.stage_id;
        const stageName = stageGroup.stage?.name || 'Unknown';
        const dealCount = stageGroup.deals?.length || 0;
        const stageValue = (stageGroup.deals || []).reduce((sum, d) => sum + (d.value || 0), 0);

        const col = document.createElement('div');
        col.className = 'kanban-column';
        col.dataset.stageId = stageId;

        // Drop zone events
        col.addEventListener('dragover', e => { e.preventDefault(); col.classList.add('drag-over'); });
        col.addEventListener('dragleave', e => {
            if (!col.contains(e.relatedTarget)) col.classList.remove('drag-over');
        });
        col.addEventListener('drop', e => {
            e.preventDefault();
            col.classList.remove('drag-over');
            const dealId = e.dataTransfer.getData('text/plain');
            if (dealId && stageId) moveDeal(parseInt(dealId), stageId);
        });

        const header = document.createElement('div');
        header.className = 'kanban-header';
        header.innerHTML = `<span>${esc(stageName)}</span><span class="kanban-count">${dealCount}</span>`;
        col.appendChild(header);

        if (stageValue > 0) {
            const valueBar = document.createElement('div');
            valueBar.style.cssText = 'font-size:11px;color:var(--g);font-weight:600;margin-bottom:8px;padding-bottom:8px;border-bottom:1px solid var(--b)';
            valueBar.textContent = formatCurrency(stageValue);
            col.appendChild(valueBar);
        }

        const cardsContainer = document.createElement('div');
        cardsContainer.className = 'kanban-cards';

        (stageGroup.deals || []).forEach(deal => {
            const card = document.createElement('div');
            card.className = 'kanban-card';
            card.draggable = true;
            card.dataset.dealId = deal.deal_id;

            card.addEventListener('dragstart', e => {
                e.dataTransfer.setData('text/plain', deal.deal_id);
                e.dataTransfer.effectAllowed = 'move';
                setTimeout(() => card.classList.add('dragging'), 0);
            });
            card.addEventListener('dragend', () => card.classList.remove('dragging'));
            card.addEventListener('click', (e) => {
                if (!e.defaultPrevented) viewDealDetail(deal.deal_id);
            });

            card.innerHTML = `
                <div class="kanban-title">${esc(deal.title)}</div>
                <div class="kanban-meta">${esc(deal.owner_name || 'No owner')}</div>
                <div class="kanban-meta">${esc(deal.section_name || '')}</div>
                ${deal.value ? `<div class="kanban-value">${formatCurrency(deal.value)}</div>` : ''}
                ${deal.nra ? `<div class="kanban-meta">${deal.nra} NRA</div>` : ''}
            `;
            cardsContainer.appendChild(card);
        });

        col.appendChild(cardsContainer);
        board.appendChild(col);
    });
}

/**
 * moveDeal(dealId, newStageId)
 * Moves a deal to a new stage and refreshes the pipeline
 */
async function moveDeal(dealId, newStageId) {
    const resp = await apiCall(`/deals/${dealId}`, 'PUT', { stage_id: newStageId });
    if (resp) {
        loadPipeline(); // Refresh the board
    }
}

/**
 * togglePipelineView()
 * Toggles between normal (scrollable) and compact (fit-to-screen) pipeline views
 */
function togglePipelineView() {
    const board = document.getElementById('kanban-board');
    const btn = event.target;
    if (board.classList.contains('compact')) {
        board.classList.remove('compact');
        btn.textContent = 'Compact View';
    } else {
        board.classList.add('compact');
        btn.textContent = 'Normal View';
    }
}
