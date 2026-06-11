// Extract URLs Modal Logic

document.addEventListener('DOMContentLoaded', () => {
    const extractModal = document.getElementById('extractModal');
    const closeExtractBtn = document.getElementById('closeExtractBtn');
    const extractBtn = document.getElementById('extractBtn');
    const extractTextArea = document.getElementById('extractTextArea');
    const extractStatusText = document.getElementById('extractStatusText');
    const downloadExtractBtn = document.getElementById('downloadExtractBtn');
    const copyExtractBtn = document.getElementById('copyExtractBtn');

    if (!extractBtn) return; // Might not be on this page

    // Close Modal
    closeExtractBtn.addEventListener('click', () => {
        extractModal.classList.add('hidden');
        setTimeout(() => extractModal.style.display = 'none', 300);
    });

    // Outside click close
    extractModal.addEventListener('click', (e) => {
        if (e.target === extractModal) {
            closeExtractBtn.click();
        }
    });

    // Open Modal and Fetch URLs
    extractBtn.addEventListener('click', async () => {
        extractModal.style.display = 'flex';
        // force reflow
        extractModal.offsetHeight;
        extractModal.classList.remove('hidden');

        extractStatusText.textContent = _('extracting_please_wait') || 'Extracting URLs... Please wait. This may take a while.';
        extractTextArea.value = '';
        extractTextArea.style.opacity = '0.5';
        
        try {
            const res = await fetch('/api/queue/extract_urls', { method: 'POST' });
            const data = await res.json();

            if (data.status === 'success') {
                if (data.urls && data.urls.length > 0) {
                    extractTextArea.value = data.urls.join('\n');
                    extractStatusText.textContent = (_('found_count') || 'Found {count} videos').replace('{count}', data.urls.length);
                } else {
                    extractTextArea.value = '';
                    extractStatusText.textContent = _('extract_no_videos') || 'No waiting videos found.';
                }
            } else {
                extractStatusText.textContent = (_('error') || 'Error') + ': ' + (data.message || 'Unknown error');
            }
        } catch (e) {
            extractStatusText.textContent = (_('error') || 'Error') + ': ' + e.message;
        } finally {
            extractTextArea.style.opacity = '1';
        }
    });

    // Copy to Clipboard
    copyExtractBtn.addEventListener('click', () => {
        if (!extractTextArea.value) return;
        extractTextArea.select();
        document.execCommand('copy');
        
        const originalText = copyExtractBtn.innerHTML;
        copyExtractBtn.innerHTML = '✅ Copied!';
        setTimeout(() => {
            copyExtractBtn.innerHTML = originalText;
        }, 2000);
    });

    // Download .txt
    downloadExtractBtn.addEventListener('click', () => {
        if (!extractTextArea.value) return;
        
        const blob = new Blob([extractTextArea.value], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        
        const dateStr = new Date().toISOString().slice(0, 10).replace(/-/g, '');
        a.href = url;
        a.download = `missav_urls_${dateStr}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });
});
