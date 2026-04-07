// ===== AI ASSISTANT CHAT =====
// Powers AI chat with persistent conversation history.

let currentConvoId = null;

async function loadAssistant() {
    const data = await apiCall('/assistant/suggestions');
    if (data && data.suggestions) {
        const container = document.getElementById('assistant-suggestions');
        if (container) {
            container.innerHTML = '';
            data.suggestions.forEach(s => {
                const chip = document.createElement('div');
                chip.className = 'assistant-chip';
                chip.textContent = s;
                chip.style.cssText = 'display:inline-block;padding:5px 10px;border:1px solid var(--b);border-radius:16px;cursor:pointer;font-size:11px;color:var(--td);transition:all .15s';
                chip.onmouseover = () => chip.style.background = 'var(--s2)';
                chip.onmouseout = () => chip.style.background = 'transparent';
                chip.onclick = () => { document.getElementById('assistant-input').value = s; sendAssistantMessage(); };
                container.appendChild(chip);
            });
        }
    }
    loadConversationList();
}

async function loadConversationList() {
    const convos = await apiCall('/assistant/conversations');
    const list = document.getElementById('assistant-convo-list');
    if (!list) return;
    if (!convos || convos.length === 0) {
        list.innerHTML = '<div style="padding:12px;font-size:11px;color:var(--td);text-align:center">No conversations yet</div>';
        return;
    }
    let html = '';
    convos.forEach(c => {
        const active = c.conversation_id === currentConvoId ? 'background:var(--b);' : '';
        const pin = c.is_pinned ? '<span style="color:var(--y);margin-right:3px" title="Pinned">★</span>' : '';
        const count = c.message_count ? `<span style="font-size:10px;color:var(--td);opacity:.7">${c.message_count}</span>` : '';
        html += `<div style="padding:8px 10px;margin:2px 0;border-radius:6px;cursor:pointer;font-size:12px;display:flex;justify-content:space-between;align-items:center;${active}" onclick="loadConversation(${c.conversation_id})" oncontextmenu="event.preventDefault();showConvoMenu(event,${c.conversation_id},${c.is_pinned})">
            <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1">${pin}${esc(c.title || 'New conversation')}</span>
            ${count}
        </div>`;
    });
    list.innerHTML = html;
}

async function newAssistantConversation() {
    const resp = await apiCall('/assistant/conversations', 'POST', { title: 'New conversation' });
    if (resp && resp.conversation_id) {
        currentConvoId = resp.conversation_id;
        document.getElementById('assistant-chat').innerHTML = '<div style="text-align:center;color:var(--td);padding:30px 20px;font-size:13px">Start a new conversation — ask anything about your data.</div>';
        loadConversationList();
    }
}

async function loadConversation(convoId) {
    currentConvoId = convoId;
    const data = await apiCall(`/assistant/conversations/${convoId}`);
    if (!data) return;
    const chat = document.getElementById('assistant-chat');
    chat.innerHTML = '';
    if (data.messages && data.messages.length > 0) {
        data.messages.forEach(m => {
            if (m.role === 'user') {
                appendUserBubble(chat, m.content);
            } else {
                let parsed = null;
                try { parsed = JSON.parse(m.content); } catch(e) {}
                if (parsed && parsed.type) {
                    renderAssistantResponse(chat, parsed);
                } else {
                    appendAssistantBubble(chat, m.content);
                }
            }
        });
    } else {
        chat.innerHTML = '<div style="text-align:center;color:var(--td);padding:30px 20px;font-size:13px">Empty conversation — ask a question to get started.</div>';
    }
    chat.scrollTop = chat.scrollHeight;
    loadConversationList();
}

function showConvoMenu(event, convoId, isPinned) {
    document.querySelectorAll('.convo-menu').forEach(m => m.remove());
    const menu = document.createElement('div');
    menu.className = 'convo-menu';
    menu.style.cssText = `position:fixed;left:${event.clientX}px;top:${event.clientY}px;background:var(--s);border:1px solid var(--b);border-radius:6px;padding:4px;z-index:300;box-shadow:0 4px 12px rgba(0,0,0,.3)`;
    menu.innerHTML = `
        <div style="padding:6px 12px;cursor:pointer;font-size:12px;border-radius:4px" onmouseover="this.style.background='var(--b)'" onmouseout="this.style.background='transparent'" onclick="togglePinConvo(${convoId});this.parentElement.remove()">${isPinned ? 'Unpin' : 'Pin'}</div>
        <div style="padding:6px 12px;cursor:pointer;font-size:12px;color:var(--r);border-radius:4px" onmouseover="this.style.background='var(--b)'" onmouseout="this.style.background='transparent'" onclick="deleteConvo(${convoId});this.parentElement.remove()">Delete</div>
    `;
    document.body.appendChild(menu);
    setTimeout(() => document.addEventListener('click', () => menu.remove(), { once: true }), 10);
}

async function togglePinConvo(convoId) {
    await apiCall(`/assistant/conversations/${convoId}/pin`, 'PUT');
    loadConversationList();
}

async function deleteConvo(convoId) {
    if (!confirm('Delete this conversation?')) return;
    await apiCall(`/assistant/conversations/${convoId}`, 'DELETE');
    if (currentConvoId === convoId) {
        currentConvoId = null;
        document.getElementById('assistant-chat').innerHTML = '<div style="text-align:center;color:var(--td);padding:30px 20px;font-size:13px">Select a conversation or start a new one.</div>';
    }
    loadConversationList();
}

function appendUserBubble(container, text) {
    const div = document.createElement('div');
    div.style.cssText = 'display:flex;justify-content:flex-end;margin:6px 0';
    div.innerHTML = `<div style="max-width:70%;padding:8px 12px;background:var(--ac);color:white;border-radius:10px;font-size:13px;word-wrap:break-word">${esc(text)}</div>`;
    container.appendChild(div);
}

function appendAssistantBubble(container, text) {
    const div = document.createElement('div');
    div.style.cssText = 'display:flex;justify-content:flex-start;margin:6px 0';
    div.innerHTML = `<div style="max-width:80%;padding:8px 12px;background:var(--s);border:1px solid var(--b);border-radius:10px;font-size:13px;word-wrap:break-word;color:var(--t)">${esc(text)}</div>`;
    container.appendChild(div);
}

function renderAssistantResponse(container, response) {
    if (response.type === 'text') {
        appendAssistantBubble(container, response.text);
    } else if (response.type === 'query') {
        const div = document.createElement('div');
        div.style.cssText = 'display:flex;flex-direction:column;max-width:90%;margin:6px 0';
        let html = `<div style="padding:8px 12px;background:var(--s);border:1px solid var(--b);border-radius:10px;font-size:13px;color:var(--t);margin-bottom:6px">${esc(response.text)}</div>`;
        if (response.data && Array.isArray(response.data) && response.data.length > 0) {
            html += `<div style="overflow-x:auto">${renderAssistantTable(response.data)}</div>`;
        }
        if (response.sql) {
            html += `<details style="margin-top:6px;font-size:11px"><summary style="cursor:pointer;color:var(--ac)">Show SQL</summary><code style="display:block;background:rgba(0,0,0,.1);padding:6px;border-radius:4px;font-size:10px;white-space:pre-wrap;color:var(--t);margin-top:4px">${esc(response.sql)}</code></details>`;
        }
        div.innerHTML = html;
        container.appendChild(div);
    } else if (response.type === 'action') {
        const div = document.createElement('div');
        div.style.cssText = 'display:flex;justify-content:flex-start;margin:6px 0';
        div.innerHTML = `<div style="max-width:70%;padding:8px 12px;background:rgba(0,180,81,.15);color:#00D460;border-radius:10px;font-size:13px">${esc(response.text || 'Action completed.')}</div>`;
        container.appendChild(div);
    } else if (response.type === 'error') {
        const div = document.createElement('div');
        div.style.cssText = 'display:flex;justify-content:flex-start;margin:6px 0';
        div.innerHTML = `<div style="max-width:70%;padding:8px 12px;background:rgba(255,103,29,.15);color:#ff9060;border-radius:10px;font-size:13px">${esc(response.text || 'An error occurred.')}</div>`;
        container.appendChild(div);
    }
}

async function sendAssistantMessage() {
    const input = document.getElementById('assistant-input');
    const chat = document.getElementById('assistant-chat');
    if (!input || !chat) return;
    const text = input.value.trim();
    if (!text) return;

    // Auto-create conversation if none active
    if (!currentConvoId) {
        const resp = await apiCall('/assistant/conversations', 'POST', { title: 'New conversation' });
        if (resp) currentConvoId = resp.conversation_id;
        else return;
    }

    // Clear placeholder text if present
    if (chat.querySelector('div[style*="text-align:center"]') && chat.children.length === 1) {
        chat.innerHTML = '';
    }

    appendUserBubble(chat, text);
    input.value = '';

    // Save user message
    apiCall(`/assistant/conversations/${currentConvoId}/messages`, 'POST', { role: 'user', content: text });

    // Loading indicator
    const loading = document.createElement('div');
    loading.style.cssText = 'display:flex;justify-content:flex-start;margin:6px 0';
    loading.innerHTML = '<div style="padding:8px 12px;background:var(--s);border:1px solid var(--b);border-radius:10px;font-size:13px;color:var(--td);animation:pulse 1.5s ease-in-out infinite">Thinking...</div>';
    if (!document.getElementById('assistant-pulse-style')) {
        const style = document.createElement('style');
        style.id = 'assistant-pulse-style';
        style.textContent = '@keyframes pulse { 0%,100% { opacity:.6 } 50% { opacity:1 } }';
        document.head.appendChild(style);
    }
    chat.appendChild(loading);
    chat.scrollTop = chat.scrollHeight;

    const response = await apiCall('/assistant', 'POST', { message: text });
    loading.remove();

    if (!response) {
        appendAssistantBubble(chat, 'Failed to get response. Please try again.');
        chat.scrollTop = chat.scrollHeight;
        return;
    }

    renderAssistantResponse(chat, response);
    chat.scrollTop = chat.scrollHeight;

    // Save assistant response
    apiCall(`/assistant/conversations/${currentConvoId}/messages`, 'POST', {
        role: 'assistant',
        content: JSON.stringify(response),
        sql_query: response.sql || null,
        result_data: response.data ? JSON.stringify(response.data) : null
    });

    // Refresh sidebar to show updated title
    loadConversationList();
}

function renderAssistantTable(data) {
    if (!data || data.length === 0) return '';
    const columns = Object.keys(data[0]);
    const maxRows = 50;
    const displayRows = data.slice(0, maxRows);
    let html = '<table style="width:100%;border-collapse:collapse;font-size:11px;border:1px solid var(--b)">';
    html += '<thead><tr style="background:var(--s2)">';
    columns.forEach(col => { html += `<th style="padding:6px 8px;text-align:left;font-weight:600;color:var(--t);border-right:1px solid var(--b);font-size:10px">${esc(col)}</th>`; });
    html += '</tr></thead><tbody>';
    displayRows.forEach((row, idx) => {
        html += `<tr style="background:${idx % 2 ? 'rgba(0,0,0,.02)' : 'transparent'};border-bottom:1px solid var(--b)">`;
        columns.forEach(col => {
            let v = row[col];
            let cell = '';
            if ((col.includes('price') || col.includes('value') || col.includes('cost')) && typeof v === 'number') cell = formatCurrency(v);
            else if (col === 'owner_id' && v) cell = `<a style="color:var(--ac);cursor:pointer" onclick="viewOwnerDetail(${v})">${v}</a>`;
            else if (col === 'section_id' && v) cell = `<a style="color:var(--ac);cursor:pointer" onclick="viewSectionDetail(${v})">${v}</a>`;
            else if (typeof v === 'number') cell = new Intl.NumberFormat('en-US').format(v);
            else cell = esc(String(v || '-'));
            html += `<td style="padding:5px 8px;border-right:1px solid var(--b)">${cell}</td>`;
        });
        html += '</tr>';
    });
    html += '</tbody></table>';
    if (data.length > maxRows) html += `<div style="margin-top:4px;font-size:10px;color:var(--td)">Showing ${maxRows} of ${data.length} rows</div>`;
    return html;
}

function handleAssistantKeydown(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendAssistantMessage(); }
}
