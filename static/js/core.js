let currentTranslations = {};

function _(key, params = {}) {
    let text = currentTranslations[key] || key;
    Object.keys(params).forEach(param => {
        text = text.replace(`{${param}}`, params[param]);
    });
    return text;
}

function updatePageLanguage() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        el.textContent = _(key);
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        el.placeholder = _(key);
    });
    document.title = _('app_title');
}

async function loadLanguage(lang) {
    try {
        const res = await fetch('/api/language', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ language: lang })
        });
        const data = await res.json();
        if (data.status === 'success') {
            const transRes = await fetch('/api/language');
            const transData = await transRes.json();
            currentTranslations = transData.translations;
            updatePageLanguage();
            
            if (typeof fetchTasks === 'function') fetchTasks();
            if (typeof fetchFiles === 'function') fetchFiles();
            if (typeof updateStatsLabels === 'function') updateStatsLabels();
        }
    } catch(e) { console.error('Failed to load language:', e); }
}

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

async function initLanguage() {
    try {
        const res = await fetch('/api/language');
        const data = await res.json();
        currentTranslations = data.translations;
        updatePageLanguage();
        document.getElementById('languageSelect').value = data.current;
    } catch(e) { console.error('Failed to load initial language:', e); }
}

document.getElementById('languageSelect').onchange = async (e) => {
    const lang = e.target.value;
    await loadLanguage(lang);
};

function initEventSource() {
    const evtSource = new EventSource("/api/events");
    evtSource.onmessage = function(event) {
        const payload = JSON.parse(event.data);
        if (payload.type === 'tasks') {
            const data = payload.data;
            if (data.stats && typeof updateStatsDisplay === 'function') updateStatsDisplay(data.stats);
            if (data.tasks && typeof renderTasks === 'function') renderTasks(data.tasks);
        } else if (payload.type === 'files') {
            if (typeof fetchFiles === 'function') fetchFiles();
        }
    };
    evtSource.onerror = function(err) {
        evtSource.close();
        setTimeout(initEventSource, 5000);
    };
}

initLanguage();
initEventSource();

// Fallback polling to ensure UI is updated even if SSE drops silently
setInterval(() => {
    if (typeof fetchTasks === 'function') fetchTasks();
}, 5000);
