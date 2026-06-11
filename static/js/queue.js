function updateStatsLabels() {}

function updateStatsDisplay(stats) {
    document.getElementById('stats').innerHTML = `
        <span class="stat">⏳ ${_('waiting')}: ${stats.waiting}</span>
        <span class="stat">⬇ ${_('downloading')}: ${stats.downloading}</span>
        <span class="stat">✅ ${_('completed')}: ${stats.completed}</span>
        <span class="stat">❌ ${_('failed')}: ${stats.failed}</span>
    `;
}

async function fetchTasks() {
    try {
        const res = await fetch('/api/tasks');
        const tasks = await res.json();
        const statsRes = await fetch('/api/queue/stats');
        const stats = await statsRes.json();
        updateStatsDisplay(stats);
        if (tasks) renderTasks(tasks);
    } catch(e) { console.error(e); }
}

function renderTasks(tasks) {
    const listEl = document.getElementById('taskList');
    const entries = Object.entries(tasks);
    if (entries.length === 0) {
        listEl.innerHTML = `<div style="text-align:center; padding:20px;">${_('no_downloads')}</div>`;
        return;
    }
    listEl.innerHTML = entries.reverse().map(([id, t]) => {
        let cls = '';
        let statusText = '';
        if (t.status === 'Completed') {
            cls = 'completed'; statusText = _('completed');
        } else if (t.status === 'Cancelled') {
            cls = 'cancelled'; statusText = _('cancelled');
        } else if (t.status && t.status.startsWith('Error')) {
            cls = 'error'; statusText = _('failed');
        } else if (t.status === 'Downloading') {
            cls = 'downloading'; statusText = _('downloading');
        } else if (t.status === 'Paused') {
            cls = 'paused'; statusText = _('paused') || 'Paused';
        } else {
            statusText = t.status;
        }
        
        const progress = t.progress || 0;
        const stage = t.stage || '';
        const title = t.filename || (t.url ? t.url.substring(0, 50) : 'Unknown');
        const metaInfo = [
            t.resolution ? `📐 ${t.resolution}` : '',
            t.filesize ? `💾 ${formatSize(t.filesize)}` : '',
            t.time_taken ? `⏱️ ${formatTime(t.time_taken)}` : ''
        ].filter(Boolean).join(' | ');
        const thumbHtml = t.thumb_url 
            ? `<div class="task-thumb"><img src="${t.thumb_url}" alt="thumb"></div>`
            : `<div class="task-thumb"><i class="fas fa-video"></i></div>`;
            
        return `
            <div class="task-card ${cls}">
                ${thumbHtml}
                <div class="task-main">
                    <div class="task-top">
                        <div style="flex:1">
                            <strong>${escapeHtml(title)}</strong>
                            <div style="font-size:12px; opacity:0.8">${statusText} ${stage ? `- ${stage}` : ''}</div>
                            ${metaInfo ? `<div style="font-size:11px; margin-top:4px; color: var(--text-secondary, #aaa);">${metaInfo}</div>` : ''}
                        </div>
                        <div class="task-actions">
                            ${(t.status === 'Downloading' || t.status === 'Waiting') ? 
                                `<button onclick="pauseTask('${id}')" class="btn-secondary" style="padding:5px 10px; margin-right:5px;" title="${_('pause') || 'Pause'}">⏸️</button>` : ''
                            }
                            ${t.status === 'Paused' ? 
                                `<button onclick="resumeTask('${id}')" class="btn-primary" style="padding:5px 10px; margin-right:5px;" title="${_('resume') || 'Resume'}">▶️</button>` : ''
                            }
                            ${(t.status === 'Downloading' || t.status === 'Waiting' || t.status === 'Paused') ? 
                                `<button onclick="cancelTask('${id}')" class="btn-secondary" style="padding:5px 10px; margin-right:5px;" title="${_('stop')}">🛑</button>` : ''
                            }
                            ${(t.status.startsWith('Error') || t.status === 'Cancelled') ? 
                                `<button onclick="retryTask('${id}')" class="btn-primary" style="padding:5px 10px; margin-right:5px;" title="${_('retry') || 'Retry'}">🔄</button>` : ''
                            }
                            <button onclick="deleteTask('${id}')" class="btn-danger" style="padding:5px 10px" title="${_('delete')}">✕</button>
                        </div>
                    </div>
                    ${(t.status === 'Downloading' || t.status === 'Waiting' || t.status === 'Paused') ? `
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${progress}%"></div>
                        </div>
                        <div style="font-size:12px; margin-top:5px">${progress}%</div>
                    ` : ''}
                </div>
            </div>
        `;
    }).join('');
}

async function deleteTask(id) {
    if (confirm(_('delete_task_confirm') || 'Remove this task from list?')) {
        await fetch(`/api/tasks/${id}`, { method: 'DELETE' });
        fetchTasks();
    }
}
async function cancelTask(id) { await fetch(`/api/tasks/${id}/cancel`, { method: 'POST' }); fetchTasks(); }
async function pauseTask(id) { await fetch(`/api/tasks/${id}/pause`, { method: 'POST' }); fetchTasks(); }
async function resumeTask(id) {
    await fetch(`/api/tasks/${id}/resume`, { method: 'POST' });
    fetchTasks();
}

async function retryTask(id) {
    await fetch(`/api/tasks/${id}/retry`, { method: 'POST' });
    fetchTasks();
}

async function clearQueue() {}

document.getElementById('cleanBtn').onclick = async () => { await fetch('/api/queue/clean', { method: 'POST' }); fetchTasks(); };
document.getElementById('cleanHistoryBtn').onclick = async () => {
    if (confirm(_('clear_gui_confirm'))) { await fetch('/api/queue/clear_all', { method: 'POST' }); fetchTasks(); }
};
document.getElementById('clearBtn').onclick = async () => {
    if (confirm(_('clear_waiting_confirm'))) { await fetch('/api/queue/clear', { method: 'POST' }); fetchTasks(); }
};
