document.getElementById('startDownloadBtn').onclick = async () => {
    const url = document.getElementById('urlInput').value.trim();
    if (!url) { alert(_('enter_url_or_code')); return; }
    const btn = document.getElementById('startDownloadBtn');
    btn.disabled = true; btn.innerHTML = `⬇️ ${_('loading')}`;
    try {
        const res = await fetch('/api/download', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });
        if (res.ok) {
            document.getElementById('urlInput').value = '';
            if(typeof fetchTasks === 'function') fetchTasks();
            alert(_('added_to_queue'));
        } else alert(_('error'));
    } catch(e) { alert('Error: ' + e.message); } 
    finally { btn.disabled = false; btn.innerHTML = `⬇️ <span data-i18n="download_now">${_('download_now') || 'Download'}</span>`; }
};

document.getElementById('batchBtn').onclick = () => document.getElementById('batchPanel').classList.toggle('hidden');
document.getElementById('cancelBatchBtn').onclick = () => {
    document.getElementById('batchPanel').classList.add('hidden');
    document.getElementById('batchUrls').value = '';
};

document.getElementById('addBatchBtn').onclick = async () => {
    const text = document.getElementById('batchUrls').value;
    const urls = text.split('\n').filter(l => l.trim());
    if (urls.length === 0) return;
    const res = await fetch('/api/batch', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ urls })
    });
    const data = await res.json();
    alert(_('batch_added', { count: data.count }));
    document.getElementById('batchPanel').classList.add('hidden');
    document.getElementById('batchUrls').value = '';
    if(typeof fetchTasks === 'function') fetchTasks();
};
