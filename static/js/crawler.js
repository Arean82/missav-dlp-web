// crawler.js - Multi-step custom crawler

let crawlerVideos = [];
let currentFilters = {};
let currentCleanBaseUrl = '';
let selectedFilter = null;
let totalPages = 1;

// Modal elements
const filterModal = document.getElementById('filterModal');
const pageModal = document.getElementById('pageModal');
const crawlerModal = document.getElementById('crawlerModal');
const crawlerSelectAll = document.getElementById('crawlerSelectAll');

// Step 1: Show filter selection
async function openCrawlerModal() {
    const urlInput = document.getElementById('urlInput').value.trim();
    
    if (!urlInput) {
        alert(_('enter_url_first'));
        return;
    }

    // Show filter modal
    filterModal.classList.remove('hidden');
    filterModal.style.display = 'flex';
    document.getElementById('filterList').innerHTML = '<div style="text-align:center; padding:20px;">' + _('fetching_filters') + '</div>';

    try {
        const res = await fetch('/api/crawl/filters', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: urlInput })
        });
        const data = await res.json();
        
        if (data.status === 'success') {
            currentFilters = data.filters;
            currentCleanBaseUrl = data.clean_base_url;
            renderFilterList(data.filters, data.current_filter);
        } else {
            document.getElementById('filterList').innerHTML = '<div style="text-align:center; padding:20px; color:#ff4757;">' + _('error') + ': ' + data.message + '</div>';
        }
    } catch (err) {
        document.getElementById('filterList').innerHTML = '<div style="text-align:center; padding:20px; color:#ff4757;">' + _('error') + ': ' + err.message + '</div>';
    }
}

function renderFilterList(filters, currentFilterValue) {
    const container = document.getElementById('filterList');
    const filterNames = Object.keys(filters);
    
    if (filterNames.length === 0) {
        container.innerHTML = '<div style="text-align:center; padding:20px;">' + _('no_filters') + '</div>';
        return;
    }
    
    let html = '<div class="filter-group" style="margin-bottom: 10px;">';
    filterNames.forEach((name, idx) => {
        const filterValue = filters[name];
        const isChecked = (currentFilterValue && filterValue === currentFilterValue) || (idx === 0 && !currentFilterValue);
        html += `
            <label style="display: block; padding: 8px; margin: 5px 0; background: #0f3460; border-radius: 5px; cursor: pointer;">
                <input type="radio" name="filter" value="${filterValue !== null ? filterValue : 'all'}" data-filter-name="${name}" ${isChecked ? 'checked' : ''}>
                <span style="margin-left: 10px;">${escapeHtml(name)}</span>
            </label>
        `;
    });
    html += '</div>';
    container.innerHTML = html;
}

// Step 2: After filter selected, show page selection
async function onFilterConfirmed() {
    const selectedRadio = document.querySelector('#filterList input[type="radio"]:checked');
    if (!selectedRadio) {
        alert(_('select_filter_first'));
        return;
    }
    
    const filterValue = selectedRadio.value;
    const filterName = selectedRadio.getAttribute('data-filter-name');
    
    selectedFilter = (filterValue === 'all') ? null : filterValue;
    
    // Close filter modal
    filterModal.style.display = 'none';
    filterModal.classList.add('hidden');
    
    // Build URL with selected filter
    let targetUrl = currentCleanBaseUrl;
    if (selectedFilter) {
        targetUrl = currentCleanBaseUrl.includes('?') 
            ? `${currentCleanBaseUrl}&filters=${selectedFilter}`
            : `${currentCleanBaseUrl}?filters=${selectedFilter}`;
    }
    
    // Show page modal and fetch max pages
    pageModal.classList.remove('hidden');
    pageModal.style.display = 'flex';
    document.getElementById('totalPagesDisplay').innerHTML = '<span data-i18n="fetching">Fetching...</span>';
    
    try {
        // --- FIX IS HERE: pages: 0 ---
        // Fetch metadata only (0 pages) to get max page count quickly
        const scrapeRes = await fetch('/api/crawl', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                url: targetUrl, 
                filter: selectedFilter,
                pages: 0  // Changed from 1 to 0 to signal "metadata only"
            })
        });
        const data = await scrapeRes.json();
        
        if (data.status === 'success' && data.max_pages) {
            totalPages = data.max_pages;
            document.getElementById('totalPagesDisplay').innerHTML = totalPages;
            document.getElementById('pagesInput').value = totalPages;
            document.getElementById('pagesInput').max = totalPages;
        } else {
            document.getElementById('totalPagesDisplay').innerHTML = _('unknown');
            document.getElementById('pagesInput').value = 1;
        }
    } catch (err) {
        document.getElementById('totalPagesDisplay').innerHTML = _('error');
        document.getElementById('pagesInput').value = 1;
    }
}

// Step 3: Start scraping with selected pages
async function onPageConfirmed() {
    let pagesToScrape = parseInt(document.getElementById('pagesInput').value);
    
    if (isNaN(pagesToScrape) || pagesToScrape < 1) {
        pagesToScrape = 1;
    }
    
    if (totalPages && pagesToScrape > totalPages) {
        pagesToScrape = totalPages;
    }
    
    // Close page modal
    pageModal.style.display = 'none';
    pageModal.classList.add('hidden');
    
    // Show results modal with loading status
    crawlerModal.classList.remove('hidden');
    crawlerModal.style.display = 'flex';
    crawlerStatus.textContent = _('fetching');
    crawlerTableBody.innerHTML = '<tr><td colspan="3" style="text-align:center; padding:20px;">' + _('scraping_pages', { pages: pagesToScrape }) + '...</td></tr>';
    
    // Build URL with selected filter
    let targetUrl = currentCleanBaseUrl;
    if (selectedFilter) {
        targetUrl = currentCleanBaseUrl.includes('?') 
            ? `${currentCleanBaseUrl}&filters=${selectedFilter}`
            : `${currentCleanBaseUrl}?filters=${selectedFilter}`;
    }
    
    try {
        const res = await fetch('/api/crawl', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                url: targetUrl, 
                filter: selectedFilter,
                pages: pagesToScrape
            })
        });
        const data = await res.json();
        
        if (data.status === 'success') {
            crawlerVideos = data.videos;
            renderResultsTable();
            crawlerStatus.textContent = _('found_count', { count: data.count });
        } else {
            crawlerStatus.textContent = _('error') + ': ' + data.message;
            crawlerTableBody.innerHTML = '<tr><td colspan="3" style="text-align:center; padding:20px;">' + _('error') + ': ' + data.message + '</td></tr>';
        }
    } catch (err) {
        crawlerStatus.textContent = _('error') + ': ' + err.message;
        crawlerTableBody.innerHTML = '<tr><td colspan="3" style="text-align:center; padding:20px;">' + _('error') + ': ' + err.message + '</td></tr>';
    }
}

function renderResultsTable() {
    if (crawlerVideos.length === 0) {
        // Colspan needs to be 4 to match headers
        crawlerTableBody.innerHTML = '<tr><td colspan="4" style="text-align:center; padding:20px;">' + _('no_videos') + '</td></tr>';
        return;
    }
    
    crawlerTableBody.innerHTML = crawlerVideos.map((v, i) => `
        <tr style="border-bottom: 1px solid #333;">
            <td style="text-align: center; padding: 8px;">
                <input type="checkbox" data-index="${i}" class="crawler-checkbox">
            </td>
            <td style="padding: 8px; font-weight: bold; color: #00d9ff;">
                ${escapeHtml(v.code || 'N/A')}
            </td>
            <td style="padding: 8px; max-width: 400px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHtml(v.title)}">
                ${escapeHtml(v.title)}
            </td>
            <td style="padding: 8px; text-align: center;">
                <a href="${v.url}" target="_blank" style="color: #fff; text-decoration: underline;">${_('link')}</a>
            </td>
        </tr>
    `).join('');
    
    document.querySelectorAll('.crawler-checkbox').forEach(cb => {
        cb.onchange = updateSelectAllState;
    });
}

function updateSelectAllState() {
    const total = document.querySelectorAll('.crawler-checkbox').length;
    const checked = document.querySelectorAll('.crawler-checkbox:checked').length;
    if (crawlerSelectAll) crawlerSelectAll.checked = total > 0 && total === checked;
}

function downloadSelected() {
    const selectedUrls = [];
    document.querySelectorAll('.crawler-checkbox:checked').forEach(cb => {
        const index = parseInt(cb.getAttribute('data-index'));
        selectedUrls.push(crawlerVideos[index].url);
    });

    if (selectedUrls.length === 0) {
        alert(_('select_one_video'));
        return;
    }

    fetch('/api/batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ urls: selectedUrls })
    })
    .then(res => res.json())
    .then(data => {
        alert(_('batch_added', { count: data.count }));
        crawlerModal.style.display = 'none';
        crawlerModal.classList.add('hidden');
        if (typeof fetchTasks === 'function') fetchTasks();
    });
}

// Event listeners
document.getElementById('customBtn').onclick = openCrawlerModal;

// Filter modal buttons
document.getElementById('closeFilterBtn').onclick = () => {
    filterModal.style.display = 'none';
    filterModal.classList.add('hidden');
};
document.getElementById('cancelFilterBtn').onclick = () => {
    filterModal.style.display = 'none';
    filterModal.classList.add('hidden');
};
document.getElementById('confirmFilterBtn').onclick = onFilterConfirmed;

// Page modal buttons
document.getElementById('closePageBtn').onclick = () => {
    pageModal.style.display = 'none';
    pageModal.classList.add('hidden');
};
document.getElementById('cancelPageBtn').onclick = () => {
    pageModal.style.display = 'none';
    pageModal.classList.add('hidden');
};
document.getElementById('confirmPageBtn').onclick = onPageConfirmed;

// Results modal buttons
// Event listeners for Crawler Modal buttons
document.getElementById('closeCrawlerBtn').onclick = () => {
    crawlerModal.style.display = 'none';
    crawlerModal.classList.add('hidden');
};
// Select All Button Logic
document.getElementById('crawlerSelectAllBtn').onclick = () => {
    document.querySelectorAll('.crawler-checkbox').forEach(cb => cb.checked = true);
    if (crawlerSelectAll) crawlerSelectAll.checked = true;
};

// Select None Button Logic
document.getElementById('crawlerSelectNoneBtn').onclick = () => {
    document.querySelectorAll('.crawler-checkbox').forEach(cb => cb.checked = false);
    if (crawlerSelectAll) crawlerSelectAll.checked = false;
};

// Download Selected Button Logic
document.getElementById('crawlerDownloadBtn').onclick = downloadSelected;
// Header checkbox logic (selects/deselects all)
if (crawlerSelectAll) {
    crawlerSelectAll.onclick = () => {
        const state = crawlerSelectAll.checked;
        document.querySelectorAll('.crawler-checkbox').forEach(cb => cb.checked = state);
    };
}

// Close modals on outside click
window.addEventListener('click', (e) => {
    if (e.target === filterModal) {
        filterModal.style.display = 'none';
        filterModal.classList.add('hidden');
    }
    if (e.target === pageModal) {
        pageModal.style.display = 'none';
        pageModal.classList.add('hidden');
    }
    if (e.target === crawlerModal) {
        crawlerModal.style.display = 'none';
        crawlerModal.classList.add('hidden');
    }
});