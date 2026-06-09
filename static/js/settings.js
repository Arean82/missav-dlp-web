let cachedSettings = null;
const settingsModal = document.getElementById('settingsModal');

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

async function preloadSettings() {
    try {
        const res = await fetch('/api/settings');
        if (res.ok) cachedSettings = await res.json();
    } catch(e) { console.error('Failed to preload settings:', e); }
}

document.getElementById('settingsBtn').onclick = async () => {
    settingsModal.style.display = 'flex';
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
            cachedSettings = await res.json();
            populateSettingsForm(cachedSettings);
        } catch(e) {
            populateSettingsForm({
                download_dir: './downloads', sequential_mode: true, delay_between_downloads: 3, video_quality: 'best',
                mirrors: ['missav.ai', 'missav.net', 'missav123.com', 'missav.com', 'missav.ws']
            });
        } finally {
            saveBtn.innerHTML = originalText; saveBtn.disabled = false;
        }
    }
};

document.getElementById('closeSettingsBtn').onclick = () => settingsModal.style.display = 'none';

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
            method: 'PUT', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });
        if (res.ok) {
            cachedSettings = settings;
            settingsModal.style.display = 'none';
            alert(_('settings_saved'));
        } else {
            const errData = await res.json();
            throw new Error(errData.message || 'Failed to save');
        }
    } catch(e) { alert(_('error') + ': ' + e.message); }
};

document.getElementById('checkMirrorsBtn').onclick = async () => {
    const mirrors = document.getElementById('settingsMirrors').value.split('\n').filter(l => l.trim());
    if (mirrors.length === 0) return;
    const btn = document.getElementById('checkMirrorsBtn');
    const originalText = btn.innerHTML;
    btn.disabled = true; btn.innerHTML = `⚡ ${_('loading')}`;
    try {
        const res = await fetch('/api/mirrors/check', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mirrors })
        });
        const data = await res.json();
        if (data.status === 'success') {
            document.getElementById('settingsMirrors').value = data.results.map(r => r.domain).join('\n');
            alert(_('success'));
        }
    } catch(e) { alert(_('error')); } 
    finally { btn.disabled = false; btn.innerHTML = originalText; }
};

preloadSettings();
