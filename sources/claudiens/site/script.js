// AtalantaClaudiens — Gallery, Filters & Lightbox

let allEntries = [];
let filteredEntries = [];
let currentIndex = 0;
const activeFilters = { stage: '', source: '', search: '' };

async function loadData() {
    const resp = await fetch('data.json');
    const data = await resp.json();
    allEntries = data.entries || [];
    filteredEntries = [...allEntries];
    renderStats(data.stats || {});
    bindFilterUI();
    applyHashFilter();
    applyFilters();
}

function renderStats(stats) {
    const container = document.getElementById('stats');
    if (!container) return;
    container.innerHTML = `
        <div class="stat-card"><span class="stat-number">${stats.total_emblems || 0}</span><span class="stat-label">Emblems</span></div>
        <div class="stat-card"><span class="stat-number">${stats.with_motto || 0}</span><span class="stat-label">With Motto</span></div>
        <div class="stat-card"><span class="stat-number">${stats.scholarly_refs || 0}</span><span class="stat-label">Scholarly References</span></div>
        <div class="stat-card"><span class="stat-number">${stats.source_links || 0}</span><span class="stat-label">Source Links</span></div>
    `;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function bindFilterUI() {
    const bar = document.getElementById('filter-bar');
    if (!bar) return;
    bar.addEventListener('click', (e) => {
        const chip = e.target.closest('.filter-chip');
        if (!chip) return;
        const type = chip.dataset.filterType;
        const value = chip.dataset.filterValue;
        if (activeFilters[type] === value) {
            activeFilters[type] = '';
        } else {
            activeFilters[type] = value;
        }
        applyFilters();
    });
    const search = document.getElementById('gallery-search');
    if (search) {
        search.addEventListener('input', (e) => {
            activeFilters.search = e.target.value.trim().toLowerCase();
            applyFilters();
        });
    }
}

function applyHashFilter() {
    if (!window.location.hash) return;
    const hash = window.location.hash.slice(1);
    hash.split('&').forEach(pair => {
        const [k, v] = pair.split('=');
        if (k && v && Object.prototype.hasOwnProperty.call(activeFilters, k)) {
            activeFilters[k] = decodeURIComponent(v);
        }
    });
}

function applyFilters() {
    const { stage, source, search } = activeFilters;
    filteredEntries = allEntries.filter(entry => {
        if (stage && entry.stage !== stage) return false;
        if (source && !(entry.sources || []).includes(source)) return false;
        if (search) {
            const haystack = [
                entry.label || '',
                entry.motto || '',
                entry.discourse || '',
                entry.roman || '',
            ].join(' ').toLowerCase();
            if (!haystack.includes(search)) return false;
        }
        return true;
    });
    document.querySelectorAll('.filter-chip').forEach(chip => {
        const type = chip.dataset.filterType;
        const value = chip.dataset.filterValue;
        const isAll = chip.classList.contains('filter-chip-all');
        const isActive = isAll
            ? !activeFilters[type]
            : activeFilters[type] === value;
        chip.classList.toggle('active', isActive);
    });
    const status = document.getElementById('filter-status');
    if (status) {
        const parts = [];
        if (stage) parts.push(`stage <strong>${stage}</strong>`);
        if (source) parts.push(`source <strong>${escapeHtml(source)}</strong>`);
        if (search) parts.push(`text <strong>"${escapeHtml(search)}"</strong>`);
        if (parts.length || filteredEntries.length !== allEntries.length) {
            status.innerHTML = `Showing <strong>${filteredEntries.length}</strong> of ${allEntries.length} emblems` +
                (parts.length ? ' — filtered by ' + parts.join(', ') + ' <a href="#" class="filter-clear" id="filter-clear">clear all</a>' : '');
            const clearLink = document.getElementById('filter-clear');
            if (clearLink) {
                clearLink.addEventListener('click', (e) => {
                    e.preventDefault();
                    clearFilters();
                });
            }
        } else {
            status.innerHTML = '';
        }
    }
    renderGallery();
}

function clearFilters() {
    activeFilters.stage = '';
    activeFilters.source = '';
    activeFilters.search = '';
    const search = document.getElementById('gallery-search');
    if (search) search.value = '';
    if (window.history && window.history.replaceState) {
        window.history.replaceState(null, '', window.location.pathname);
    }
    applyFilters();
}

function renderGallery() {
    const gallery = document.getElementById('gallery');
    if (!gallery) return;
    if (!filteredEntries.length) {
        gallery.innerHTML = '<p style="grid-column:1/-1;text-align:center;color:var(--text-muted);padding:3rem 1rem">No emblems match these filters.</p>';
        return;
    }
    gallery.innerHTML = filteredEntries.map((entry, i) => `
        <div class="card" onclick="openLightbox(${i})">
            ${entry.image
                ? `<img src="${entry.image}" alt="Emblem ${entry.roman || 'F'}" style="width:100%;display:block">`
                : `<div class="card-placeholder">${entry.roman || 'F'}</div>`}
            <div class="card-body">
                <div class="card-sig">${entry.roman ? 'Emblem ' + entry.roman : 'Frontispiece'}${entry.stage ? ' <span class="badge badge-stage" style="font-size:0.6rem;vertical-align:middle">' + entry.stage + '</span>' : ''}</div>
                <div class="card-label">${escapeHtml(entry.label)}</div>
                <div class="card-desc">${escapeHtml(entry.motto || '')}</div>
            </div>
        </div>
    `).join('');
}

function openLightbox(index) {
    currentIndex = index;
    const entry = filteredEntries[index];
    const lb = document.getElementById('lightbox');
    const details = lb.querySelector('.lightbox-details');
    details.innerHTML = `
        <h3>${entry.roman ? 'Emblem ' + entry.roman : 'Frontispiece'} — ${escapeHtml(entry.label)}</h3>
        ${entry.motto ? `<div class="lightbox-motto">${escapeHtml(entry.motto)}</div>` : ''}
        ${entry.discourse ? `<div class="lightbox-desc">${escapeHtml(entry.discourse).substring(0, 600)}${entry.discourse.length > 600 ? '...' : ''}</div>` : ''}
        <p style="margin-top:1rem"><a href="emblems/${entry.page}" style="color:var(--accent-light)">View full emblem page &rarr;</a></p>
    `;
    lb.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeLightbox() {
    document.getElementById('lightbox').classList.remove('active');
    document.body.style.overflow = '';
}

function navigateLightbox(dir) {
    const newIndex = currentIndex + dir;
    if (newIndex >= 0 && newIndex < filteredEntries.length) {
        openLightbox(newIndex);
    }
}

document.addEventListener('keydown', (e) => {
    const lb = document.getElementById('lightbox');
    if (!lb || !lb.classList.contains('active')) return;
    if (e.key === 'Escape') closeLightbox();
    if (e.key === 'ArrowLeft') navigateLightbox(-1);
    if (e.key === 'ArrowRight') navigateLightbox(1);
});

window.addEventListener('hashchange', () => {
    activeFilters.stage = '';
    activeFilters.source = '';
    applyHashFilter();
    applyFilters();
});

function bindRandomButton() {
    const btn = document.getElementById('random-emblem');
    if (!btn) return;
    btn.addEventListener('click', () => {
        const pool = filteredEntries.length > 1 ? filteredEntries : allEntries;
        if (!pool.length) return;
        const idx = Math.floor(Math.random() * pool.length);
        const entry = pool[idx];
        if (entry && entry.page) {
            window.location.href = 'emblems/' + entry.page;
        }
    });
}

document.addEventListener('DOMContentLoaded', async () => {
    await loadData();
    bindRandomButton();
});
