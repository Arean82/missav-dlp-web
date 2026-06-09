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
        } else { docsContent.textContent = _('failed_load_doc'); }
    } catch(e) { docsContent.textContent = _('error'); }
    docsSelect.value = "";
};

document.getElementById('closeDocsBtn').onclick = () => docsModal.style.display = 'none';

window.addEventListener('click', function(event) {
    if (event.target === document.getElementById('settingsModal')) document.getElementById('settingsModal').style.display = 'none';
    if (event.target === docsModal) docsModal.style.display = 'none';
    if (event.target === document.getElementById('browserModal')) document.getElementById('browserModal').style.display = 'none';
});
