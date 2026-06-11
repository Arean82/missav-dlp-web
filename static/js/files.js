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
                    <a href="/api/files/${encodeURIComponent(f.name)}/download" download style="color: var(--accent-color, #00d9ff); margin-right:10px">⬇ ${_('downloads')}</a>
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

async function purgeAllFiles() {
    if (confirm(_('purge_files_confirm'))) {
        const res = await fetch('/api/files/purge', { method: 'POST' });
        const data = await res.json();
        alert(_('files_deleted_count', { count: data.deleted }));
        fetchFiles();
    }
}

document.getElementById('purgeFilesBtn').onclick = purgeAllFiles;
document.getElementById('fileSearch').addEventListener('input', fetchFiles);
document.getElementById('selectAllFiles').onclick = (e) => {
    document.querySelectorAll('.file-checkbox').forEach(cb => { cb.checked = e.target.checked; });
};
document.getElementById('deleteSelectedFilesBtn').onclick = async () => {
    const selected = Array.from(document.querySelectorAll('.file-checkbox:checked')).map(cb => cb.getAttribute('data-filename'));
    if (selected.length === 0) return alert(_('select_one_file') || 'Please select at least one file');
    if (confirm(_('delete_selected_confirm', { count: selected.length }) || `Delete ${selected.length} selected files?`)) {
        await fetch('/api/files/batch_delete', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filenames: selected })
        });
        fetchFiles();
        document.getElementById('selectAllFiles').checked = false;
    }
};

fetchFiles();
