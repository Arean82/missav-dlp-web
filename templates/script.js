let cachedSettings = null;
let currentTranslations = {};

// Translation function
function _(key, params = {}) {
    let text = currentTranslations[key] || key;
    // Replace parameters like {count}
    Object.keys(params).forEach(param => {
        text = text.replace(`{${param}}`, params[param]);
    });
    return text;
}

// Update all i18n elements on the page
function updatePageLanguage() {
    // Update elements with data-i18n attribute
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        el.textContent = _(key);
    });
    
    // Update placeholders
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        el.placeholder = _(key);
    });
    
    // Update document title
    document.title = _('app_title');
}

// Load language
async function loadLanguage(lang) {
    try {
        const res = await fetch('/api/language', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ language: lang })
        });
        const data = await res.json();
        
        if (data.status === 'success') {
            // Get translations
            const transRes = await fetch('/api/language');
            const transData = await transRes.json();
            currentTranslations = transData.translations;
            updatePageLanguage();
            
            // Refresh UI text that might have been dynamically generated
            fetchTasks();
            fetchFiles();
            
            // Update stats labels
            updateStatsLabels();
        }
    } catch(e) {
        console.error('Failed to load language:', e);
    }
}

// Format functions
function formatSize(bytes) {
    if (bytes >= 1e9) return (bytes / 1e9).toFixed(1) + ' GB';
    if (bytes >= 1e6) return (bytes / 1e6).toFixed(1) + ' MB';
    if (bytes >= 1e3) return (bytes / 1e3).toFixed(1) + ' KB';
    return bytes + ' B';
}

function formatTime(seconds) {
    if (!seconds) return '-';
    const m = Math.floor(seconds / 60);
    const s = Math.round(seconds % 60);
    return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function updateStatsLabels() {
    // This will be called when stats are refreshed
}

async function fetchTasks() {
    try {
        const res = await fetch('/api/tasks');
        const tasks = await res.json();
        const statsRes = await fetch('/api/queue/stats');
        const stats = await statsRes.json();
        
        document.getElementById('stats').innerHTML = `
            <span class="stat">⏳ ${_('waiting')}: ${stats.waiting}</span>
            <span class="stat">⬇ ${_('downloading')}: ${stats.downloading}</span>
            <span class="stat">✅ ${_('completed')}: ${stats.completed}</span>
            <span class="stat">❌ ${_('failed')}: ${stats.failed}</span>
        `;
        if (tasks) {
            renderTasks(tasks);
        }
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
            cls = 'completed';
            statusText = _('completed');
        } else if (t.status === 'Cancelled') {
            cls = 'cancelled';
            statusText = _('cancelled');
        } else if (t.status && t.status.startsWith('Error')) {
            cls = 'error';
            statusText = _('failed');
        } else if (t.status === 'Downloading') {
            cls = 'downloading';
            statusText = _('downloading');
        } else {
            statusText = t.status;
        }
        
        const progress = t.progress || 0;
        const stage = t.stage || '';
        const title = t.filename || (t.url ? t.url.substring(0, 50) : 'Unknown');
        
        // Build metadata string (Resolution | Size | Time)
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
                            ${metaInfo ? `<div style="font-size:11px; margin-top:4px; color:#aaa;">${metaInfo}</div>` : ''}
                        </div>
                        <div class="task-actions">
                            ${(t.status === 'Downloading' || t.status === 'Waiting') ? 
                                `<button onclick="cancelTask('${id}')" class="btn-secondary" style="padding:5px 10px; margin-right:5px;" title="${_('stop')}">🛑</button>` : ''
                            }
                            <button onclick="deleteTask('${id}')" class="btn-danger" style="padding:5px 10px" title="${_('delete')}">✕</button>
                        </div>
                    </div>
                    ${(t.status === 'Downloading' || t.status === 'Waiting') ? `
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

async function cancelTask(id) {
    await fetch(`/api/tasks/${id}/cancel`, { method: 'POST' });
    fetchTasks();
}

async function fetchFiles() {
    try {
        const res = await fetch('/api/files');
        const files = await res.json();
        const search = document.getElementById('fileSearch').value.toLowerCase();
        const filtered = files.filter(f => f.name.toLowerCase().includes(search));
        
        const headerEl = document.getElementById('fileListHeader');
        const deleteSelectedBtn = document.getElementById('deleteSelectedFilesBtn');
        const listEl = document.getElementById('fileList');
        
        if (filtered.length === 0) {
            listEl.innerHTML = `<div style="text-align:center; padding:20px;">${_('no_files')}</div>`;
            headerEl.style.display = 'none';
            deleteSelectedBtn.style.display = 'none';
            return;
        }
        
        headerEl.style.display = 'flex';
        deleteSelectedBtn.style.display = filtered.length > 0 ? 'inline-block' : 'none';
        
        listEl.innerHTML = filtered.map(f => `
            <div class="file-card">
                <div style="display: flex; align-items: center; flex: 1;">
                    <input type="checkbox" class="file-checkbox" data-filename="${f.name}" style="margin-right: 15px;">
                    <span>🎬 ${escapeHtml(f.name)}</span>
                </div>
                <div>
                    <span style="margin-right:15px">${formatSize(f.size)}</span>
                    <a href="/api/files/${encodeURIComponent(f.name)}/download" download style="color:#00d9ff; margin-right:10px">⬇ ${_('downloads')}</a>
                    <button onclick="deleteFile('${encodeURIComponent(f.name)}')" class="btn-danger" style="padding:5px 10px">${_('delete')}</button>
                </div>
            </div>
        `).join('');
    } catch(e) { console.error(e); }
}

async function deleteFile(name) {
    if (confirm(_('delete_file_confirm'))) {
        await fetch(`/api/files/${name}`, { method: 'DELETE' });
        fetchFiles();
    }
}

// Start Download (Direct to Queue)
document.getElementById('startDownloadBtn').onclick = async () => {
    const url = document.getElementById('urlInput').value.trim();
    if (!url) { alert(_('enter_url_or_code')); return; }
    
    const btn = document.getElementById('startDownloadBtn');
    btn.disabled = true;
    btn.innerHTML = `⬇️ ${_('loading')}`;
    
    try {
        const res = await fetch('/api/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url }) // Sends directly to queue, no format selected
        });
        
        if (res.ok) {
            document.getElementById('urlInput').value = ''; // Clear input box
            fetchTasks();
            alert(_('added_to_queue'));
        } else {
            alert(_('error'));
        }
    } catch(e) { 
        alert('Error: ' + e.message); 
    } finally {
        btn.disabled = false;
        btn.innerHTML = `⬇️ <span data-i18n="download_now">Download</span>`;
    }
};

// Batch
document.getElementById('batchBtn').onclick = () => {
    document.getElementById('batchPanel').classList.toggle('hidden');
};

document.getElementById('cancelBatchBtn').onclick = () => {
    document.getElementById('batchPanel').classList.add('hidden');
    document.getElementById('batchUrls').value = '';
};

document.getElementById('addBatchBtn').onclick = async () => {
    const text = document.getElementById('batchUrls').value;
    const urls = text.split('\n').filter(l => l.trim());
    if (urls.length === 0) return;
    
    const res = await fetch('/api/batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ urls })
    });
    const data = await res.json();
    alert(_('batch_added', { count: data.count }));
    document.getElementById('batchPanel').classList.add('hidden');
    document.getElementById('batchUrls').value = '';
    fetchTasks();
};

// Queue controls
document.getElementById('cleanBtn').onclick = async () => {
    await fetch('/api/queue/clean', { method: 'POST' });
    fetchTasks();
};

document.getElementById('cleanHistoryBtn').onclick = async () => {
    if (confirm(_('clear_gui_confirm'))) {
        await fetch('/api/queue/clear_all', { method: 'POST' });
        fetchTasks();
    }
};

// New function for actual file purging (if we add a button for it)
async function purgeAllFiles() {
    if (confirm(_('purge_files_confirm'))) {
        const res = await fetch('/api/files/purge', { method: 'POST' });
        const data = await res.json();
        alert(_('files_deleted_count', { count: data.deleted }));
        fetchFiles();
    }
}

document.getElementById('purgeFilesBtn').onclick = purgeAllFiles;

document.getElementById('selectAllFiles').onclick = (e) => {
    const checked = e.target.checked;
    document.querySelectorAll('.file-checkbox').forEach(cb => {
        cb.checked = checked;
    });
};

document.getElementById('deleteSelectedFilesBtn').onclick = async () => {
    const selected = Array.from(document.querySelectorAll('.file-checkbox:checked'))
        .map(cb => cb.getAttribute('data-filename'));
    
    if (selected.length === 0) {
        alert(_('select_one_file') || 'Please select at least one file');
        return;
    }
    
    if (confirm(_('delete_selected_confirm', { count: selected.length }) || `Delete ${selected.length} selected files?`)) {
        await fetch('/api/files/batch_delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filenames: selected })
        });
        fetchFiles();
        document.getElementById('selectAllFiles').checked = false;
    }
};

document.getElementById('clearBtn').onclick = async () => {
    if (confirm(_('clear_waiting_confirm'))) {
        await fetch('/api/queue/clear', { method: 'POST' });
        fetchTasks();
    }
};

// Settings Modal
const modal = document.getElementById('settingsModal');

function populateSettingsForm(settings) {
    document.getElementById('settingsDownloadDir').value = settings.download_dir || './downloads';
    document.getElementById('settingsFfmpegPath').value = settings.ffmpeg_path || '';
    document.getElementById('settingsMaxConcurrent').value = settings.max_concurrent || 1;
    document.getElementById('settingsSequentialMode').checked = settings.sequential_mode !== false;
    document.getElementById('settingsDelay').value = settings.delay_between_downloads || 3;
    document.getElementById('settingsRateLimit').value = settings.ratelimit || 0;
    document.getElementById('settingsQuality').value = settings.video_quality || 'best';
    document.getElementById('settingsProxyBypass').checked = settings.proxy_bypass_all !== false;
    
    const mirrors = settings.mirrors || ['missav.ai', 'missav.net', 'missav123.com', 'missav.com', 'missav.ws'];
    document.getElementById('settingsMirrors').value = mirrors.join('\n');
}

// Pre-load settings in background
async function preloadSettings() {
    try {
        const res = await fetch('/api/settings');
        if (res.ok) {
            cachedSettings = await res.json();
        }
    } catch(e) {
        console.error('Failed to preload settings:', e);
    }
}

// Get current language and load translations
async function initLanguage() {
    try {
        const res = await fetch('/api/language');
        const data = await res.json();
        currentTranslations = data.translations;
        updatePageLanguage();
        
        // Set language select to current
        const langSelect = document.getElementById('languageSelect');
        langSelect.value = data.current;
    } catch(e) {
        console.error('Failed to load initial language:', e);
    }
}

// Language selector
document.getElementById('languageSelect').onchange = async (e) => {
    const lang = e.target.value;
    await loadLanguage(lang);
};

// Settings button handler
document.getElementById('settingsBtn').onclick = async () => {
    modal.style.display = 'flex';
    
    if (cachedSettings) {
        populateSettingsForm(cachedSettings);
    } else {
        const saveBtn = document.getElementById('saveSettingsBtn');
        const originalText = saveBtn.innerHTML;
        saveBtn.innerHTML = _('loading');
        saveBtn.disabled = true;
        
        try {
            const res = await fetch('/api/settings');
            if (!res.ok) throw new Error('Failed to load settings');
            const settings = await res.json();
            cachedSettings = settings;
            populateSettingsForm(settings);
        } catch(e) {
            console.error('Settings load error:', e);
            const defaultSettings = {
                download_dir: './downloads',
                sequential_mode: true,
                delay_between_downloads: 3,
                video_quality: 'best',
                mirrors: ['missav.ai', 'missav.net', 'missav123.com', 'missav.com', 'missav.ws']
            };
            populateSettingsForm(defaultSettings);
        } finally {
            saveBtn.innerHTML = originalText;
            saveBtn.disabled = false;
        }
    }
};

document.getElementById('closeSettingsBtn').onclick = () => {
    modal.style.display = 'none';
};

document.getElementById('saveSettingsBtn').onclick = async () => {
    try {
        const settings = {
            download_dir: document.getElementById('settingsDownloadDir').value,
            ffmpeg_path: document.getElementById('settingsFfmpegPath').value,
            max_concurrent: parseInt(document.getElementById('settingsMaxConcurrent').value) || 1,
            sequential_mode: document.getElementById('settingsSequentialMode').checked,
            delay_between_downloads: parseInt(document.getElementById('settingsDelay').value),
            ratelimit: parseInt(document.getElementById('settingsRateLimit').value) || 0,
            video_quality: document.getElementById('settingsQuality').value,
            proxy_bypass_all: document.getElementById('settingsProxyBypass').checked,
            mirrors: document.getElementById('settingsMirrors').value.split('\n').filter(l => l.trim())
        };
        
        const res = await fetch('/api/settings', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });
        
        if (res.ok) {
            cachedSettings = settings;
            modal.style.display = 'none';
            alert(_('settings_saved'));
        } else {
            const errData = await res.json();
            throw new Error(errData.message || 'Failed to save');
        }
    } catch(e) {
        alert(_('error') + ': ' + e.message);
    }
};

document.getElementById('checkMirrorsBtn').onclick = async () => {
    const mirrors = document.getElementById('settingsMirrors').value.split('\n').filter(l => l.trim());
    if (mirrors.length === 0) return;
    
    const btn = document.getElementById('checkMirrorsBtn');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `⚡ ${_('loading')}`;
    
    try {
        const res = await fetch('/api/mirrors/check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mirrors: mirrors })
        });
        const data = await res.json();
        
        if (data.status === 'success') {
            const sorted = data.results.map(r => r.domain);
            document.getElementById('settingsMirrors').value = sorted.join('\n');
            alert(_('success'));
        }
    } catch(e) {
        alert(_('error'));
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
};

// Docs Modal Logic
const docsModal = document.getElementById('docsModal');
const docsSelect = document.getElementById('docsSelect');
const docsContent = document.getElementById('docsContent');
const docsModalTitle = document.getElementById('docsModalTitle');

docsSelect.onchange = async (e) => {
    const docType = e.target.value;
    if (!docType) return;

    docsModalTitle.textContent = docType.toUpperCase();
    docsContent.textContent = _('loading');
    docsModal.style.display = 'flex';

    try {
        const res = await fetch(`/api/docs/${docType}`);
        const data = await res.json();
        if (data.status === 'success') {
            docsContent.innerHTML = marked.parse(data.content);
        } else {
            docsContent.textContent = _('failed_load_doc');
        }
    } catch(e) {
        docsContent.textContent = _('error');
    }
    
    // Reset dropdown back to placeholder
    docsSelect.value = "";
};

document.getElementById('closeDocsBtn').onclick = () => {
    docsModal.style.display = 'none';
};

// Close modals when clicking outside
window.onclick = function(event) {
    if (event.target === modal) {
        modal.style.display = 'none';
    }
    if (event.target === docsModal) {
        docsModal.style.display = 'none';
    }
};

// Search
document.getElementById('fileSearch').addEventListener('input', fetchFiles);

// EventSource for Real-time Updates (SSE)
function initEventSource() {
    console.log("Initializing Real-time Event Stream...");
    const evtSource = new EventSource("/api/events");

    evtSource.onmessage = function(event) {
        const payload = JSON.parse(event.data);
        if (payload.type === 'tasks') {
            const data = payload.data;
            if (data.stats) {
                document.getElementById('stats').innerHTML = `
                    <span class="stat">⏳ ${_('waiting')}: ${data.stats.waiting}</span>
                    <span class="stat">⬇ ${_('downloading')}: ${data.stats.downloading}</span>
                    <span class="stat">✅ ${_('completed')}: ${data.stats.completed}</span>
                    <span class="stat">❌ ${_('failed')}: ${data.stats.failed}</span>
                `;
            }
            if (data.tasks) {
                renderTasks(data.tasks);
            }
        } else if (payload.type === 'files') {
            fetchFiles();
        }
    };

    evtSource.onerror = function(err) {
        console.error("EventSource failed. Retrying in 5s...", err);
        evtSource.close();
        setTimeout(initEventSource, 5000);
    };
}

// Initial load
initLanguage();
preloadSettings();
initEventSource();
fetchFiles();