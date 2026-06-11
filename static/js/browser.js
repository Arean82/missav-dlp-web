let browserTargetInputId = null;
let browserCurrentPath = "";

async function openFolderBrowser(inputId) {
    browserTargetInputId = inputId;
    const startPath = document.getElementById(inputId).value || "";
    document.getElementById('browserModal').style.display = 'flex';
    document.getElementById('browserModal').classList.remove('hidden');
    await fetchDir(startPath);
}

async function fetchDir(path) {
    const listEl = document.getElementById('browserList');
    listEl.innerHTML = `<div style="padding:20px; text-align:center;">${_('loading') || 'Loading...'}</div>`;
    try {
        const res = await fetch('/api/utils/ls', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: path })
        });
        const data = await res.json();
        if (data.status === 'success') {
            browserCurrentPath = data.current_path;
            document.getElementById('browserCurrentPath').textContent = data.current_path;
            let html = "";
            if (data.parent_path) {
                html += `<div class="browser-item" onclick="fetchDir('${data.parent_path.replace(/\\/g, '\\\\')}')" style="padding: 10px; cursor: pointer; border-bottom: 1px solid var(--card-border); color: var(--accent-color);">📁 .. (Parent Directory)</div>`;
            }
            if (data.folders.length === 0) {
                html += `<div style="padding:20px; text-align:center; opacity:0.5;">No subfolders found</div>`;
            } else {
                data.folders.forEach(f => {
                    html += `<div class="browser-item" onclick="fetchDir('${f.path.replace(/\\/g, '\\\\')}')" style="padding: 10px; cursor: pointer; border-bottom: 1px solid var(--card-border);">📁 ${escapeHtml(f.name)}</div>`;
                });
            }
            listEl.innerHTML = html;
        } else { listEl.innerHTML = `<div style="padding:20px; text-align:center; color:#ff4757;">${data.message}</div>`; }
    } catch (e) { listEl.innerHTML = `<div style="padding:20px; text-align:center; color:#ff4757;">Error: ${e.message}</div>`; }
}

document.getElementById('closeBrowserBtn').onclick = document.getElementById('cancelBrowserBtn').onclick = () => {
    document.getElementById('browserModal').style.display = 'none';
    document.getElementById('browserModal').classList.add('hidden');
};

document.getElementById('confirmBrowserBtn').onclick = () => {
    if (browserTargetInputId && browserCurrentPath) {
        document.getElementById(browserTargetInputId).value = browserCurrentPath;
    }
    document.getElementById('browserModal').style.display = 'none';
    document.getElementById('browserModal').classList.add('hidden');
};
