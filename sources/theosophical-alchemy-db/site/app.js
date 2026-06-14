/* =====================================================================
   TheosophicalAlchemyDB — app.js
   Features: search, filter/sort, relational modal chaining, emblems, map
   ===================================================================== */

'use strict';

// ─── State ────────────────────────────────────────────────────────────────────

let allData = { figures: [], concepts: [], texts: [], essays: [], emblems: [] };

// Track active section for context-aware UI
let activeSection = 'figures';

// Per-section filter state
const filterState = {
    figures:      { sort: 'default', nationality: '', scholar: '', century: '' },
    concepts:     { sort: 'default', category: '' },
    texts:        { sort: 'default', language: '', century: '' },
    essays:       { sort: 'default' },
    emblems:      { sort: 'default', source_book: '', type: '' },
    'emblem-books': { sort: 'default', source_book: '', theme: '' }
};

// Modal navigation stack: [{section, id}]
const modalStack = [];

// ─── Boot ─────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch('./data/prototype_data.json');
        allData = await response.json();
        allData.emblems = allData.emblems || [];

        updateStats();
        populateFilterDropdowns();

        ['figures', 'concepts', 'texts', 'essays', 'emblems'].forEach(s => renderGallery(s));
        renderEmblemBooks();

        initializeMap();
        renderTimeline();
        setupNavigation();
        setupModal();
        setupSearch();
        setupFilterListeners();
        setupTimelineFilters();
    } catch (err) {
        console.error('Error loading data:', err);
        document.body.innerHTML =
            `<div style="padding:2rem;color:red"><h2>Error Loading Portal</h2><p>${err.message}</p></div>`;
    }
});

// ─── Stats ────────────────────────────────────────────────────────────────────

function updateStats() {
    document.getElementById('stat-figures').textContent  = allData.figures.length;
    document.getElementById('stat-concepts').textContent = allData.concepts.length;
    document.getElementById('stat-texts').textContent    = allData.texts.length;
    document.getElementById('stat-emblems').textContent  = allData.emblems.length;
    // Note: essays not shown in header stats but displayed in Essays section
}

// ─── Filter dropdown population ───────────────────────────────────────────────

function populateFilterDropdowns() {
    // Figures: nationality
    const nats = [...new Set(allData.figures.map(f => f.nationality).filter(Boolean))].sort();
    fillSelect('[data-filter="nationality"][data-section="figures"]', nats);

    // Figures: scholar
    const scholars = [...new Set(allData.figures.flatMap(f => f.scholars || []).filter(Boolean))].sort();
    fillSelect('[data-filter="scholar"][data-section="figures"]', scholars);

    // Figures: century
    const figCenturies = centuriesFrom(allData.figures.map(f => f.birth_year));
    fillSelect('[data-filter="century"][data-section="figures"]', figCenturies, c => `${c}th century`);

    // Concepts: category — humanise and dedupe
    const cats = [...new Set(allData.concepts.map(c => c.category).filter(Boolean))].sort();
    fillSelect('[data-filter="category"][data-section="concepts"]', cats, humaniseCategory);

    // Texts: language
    const langs = [...new Set(allData.texts.map(t => t.language).filter(Boolean))].sort();
    fillSelect('[data-filter="language"][data-section="texts"]', langs);

    // Texts: century
    const txtCenturies = centuriesFrom(allData.texts.map(t => Number(t.year)));
    fillSelect('[data-filter="century"][data-section="texts"]', txtCenturies, c => `${c}th century`);
}

function fillSelect(selector, values, labelFn = v => v) {
    const sel = document.querySelector(selector);
    if (!sel) return;
    values.forEach(v => {
        const opt = document.createElement('option');
        opt.value = v;
        opt.textContent = labelFn(v);
        sel.appendChild(opt);
    });
}

function centuriesFrom(years) {
    const cs = [...new Set(years
        .filter(y => y && y > 0)
        .map(y => Math.ceil(y / 100))
    )].sort((a, b) => a - b);
    return cs;
}

function humaniseCategory(raw) {
    return raw.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

// ─── Filter listeners ─────────────────────────────────────────────────────────

function setupFilterListeners() {
    document.querySelectorAll('.filter-select').forEach(sel => {
        sel.addEventListener('change', () => {
            const section = sel.dataset.section;
            const filter  = sel.dataset.filter;
            filterState[section][filter] = sel.value;
            if (section === 'emblem-books') {
                renderEmblemBooks();
            } else {
                renderGallery(section);
            }
        });
    });

    document.querySelectorAll('.filter-reset').forEach(btn => {
        btn.addEventListener('click', () => {
            const section = btn.dataset.section;
            // Reset state
            Object.keys(filterState[section]).forEach(k => filterState[section][k] = k === 'sort' ? 'default' : '');
            // Reset selects
            document.querySelectorAll(`.filter-select[data-section="${section}"]`).forEach(s => s.value = s.options[0].value);
            if (section === 'emblem-books') {
                renderEmblemBooks();
            } else {
                renderGallery(section);
            }
        });
    });
}

// ─── Data filtering & sorting ─────────────────────────────────────────────────

function applyFiltersAndSort(section) {
    let items = [...allData[section]];
    const state = filterState[section];

    // ── Filters ──
    if (section === 'figures') {
        if (state.nationality)
            items = items.filter(f => f.nationality === state.nationality);
        if (state.scholar)
            items = items.filter(f => (f.scholars || []).includes(state.scholar));
        if (state.century)
            items = items.filter(f => f.birth_year && Math.ceil(f.birth_year / 100) === Number(state.century));
    }
    if (section === 'concepts') {
        if (state.category)
            items = items.filter(c => c.category === state.category);
    }
    if (section === 'texts') {
        if (state.language)
            items = items.filter(t => t.language === state.language);
        if (state.century)
            items = items.filter(t => t.year && Math.ceil(Number(t.year) / 100) === Number(state.century));
    }
    if (section === 'emblems') {
        if (state.source_book)
            items = items.filter(e => e.source_book === state.source_book);
        if (state.type)
            items = items.filter(e => e.type === state.type);
    }

    // ── Sort ──
    switch (state.sort) {
        case 'alpha':
            items.sort((a, b) => (a.name || a.title || '').localeCompare(b.name || b.title || ''));
            break;
        case 'alpha-rev':
            items.sort((a, b) => (b.name || b.title || '').localeCompare(a.name || a.title || ''));
            break;
        case 'chrono':
            items.sort((a, b) => (a.birth_year || a.year || 9999) - (b.birth_year || b.year || 9999));
            break;
        case 'chrono-rev':
            items.sort((a, b) => (b.birth_year || b.year || 0) - (a.birth_year || a.year || 0));
            break;
    }

    return items;
}

// ─── Gallery rendering ────────────────────────────────────────────────────────

function renderGallery(section) {
    const items   = applyFiltersAndSort(section);
    const gallery = document.getElementById(`${section}-gallery`);
    if (!gallery) return;
    const counter = document.getElementById(`${section}-count`);
    const total   = (allData[section] || []).length;

    if (counter) {
        counter.textContent = items.length < total
            ? `Showing ${items.length} of ${total}`
            : `${total} entries`;
    }

    if (!items.length) {
        gallery.innerHTML = '<p class="no-results">No entries match the current filters.</p>';
        return;
    }

    gallery.innerHTML = items.map(item => buildCard(section, item, section)).join('');

    gallery.querySelectorAll('.card').forEach(card => {
        card.addEventListener('click', e => {
            if (e.target.closest('a, button')) return;
            openModal(card.dataset.section, card.dataset.id, true);
        });
    });
}

function buildCard(section, item, currentContext = activeSection) {
    const id    = item.id;
    const name  = item.name || item.title || '—';
    const meta  = buildCardMeta(section, item);
    const badge = buildBadgeInline(section, currentContext);
    const imageHtml = (section === 'figures' || section === 'emblems' || section === 'essays') && item.image_url
        ? `<img src="${item.image_url}" alt="${name}" class="card-image">`
        : '';

    return `
        <div class="card card-${section}" data-section="${section}" data-id="${id}">
            ${imageHtml}
            <div class="card-header">
                <div class="card-title">${name}</div>
                <div class="card-meta-inline">${meta}</div>
            </div>
            <div class="card-summary">${item.summary || ''}</div>
            <div class="card-footer">
                <span class="card-read-more">Read full essay →</span>
                ${badge}
            </div>
        </div>`;
}

function buildCardMeta(section, item) {
    if (section === 'figures') {
        const years = item.birth_year
            ? `${item.birth_year}–${item.death_year || '?'}`
            : '';
        return `<div class="card-meta">${[years, item.nationality, item.location].filter(Boolean).join(' · ')}</div>`;
    }
    if (section === 'texts') {
        return `<div class="card-meta">${[item.year, item.language, item.location].filter(Boolean).join(' · ')}</div>`;
    }
    if (section === 'concepts') {
        return item.category
            ? `<div class="card-meta">${humaniseCategory(item.category)}</div>`
            : '';
    }
    if (section === 'emblems') {
        return `<div class="card-meta">${[item.source_book, item.year].filter(Boolean).join(' · ')}</div>`;
    }
    if (section === 'essays') {
        return item.period
            ? `<div class="card-meta">${item.period}</div>`
            : '';
    }
    return '';
}

function buildBadgeInline(section, currentContext = activeSection) {
    // Hide badge when viewing items from their own section (context already clear)
    // Always show badge when viewing items in modals (different context)
    if (currentContext === section && !modalStack.length) {
        return '';
    }
    return `<span class="card-badge card-badge-inline badge-${section}"></span>`;
}

function buildBadge(section, item) {
    const labels = { figures: 'Figure', concepts: 'Concept', texts: 'Text', essays: 'Essay', emblems: 'Emblem' };
    return `<span class="card-badge badge-${section}">${labels[section]}</span>`;
}

// ─── Emblem Books (grouped view) ───────────────────────────────────────────────

function renderEmblemBooks() {
    const container = document.getElementById('emblem-books-container');
    if (!container) return;
    const state = filterState['emblem-books'];

    // Filter and sort emblems
    let emblems = [...allData.emblems];

    if (state.source_book) {
        emblems = emblems.filter(e => e.source_book === state.source_book);
    }

    if (state.theme) {
        emblems = emblems.filter(e => {
            const conceptIds = e.concepts || [];
            const themeConceptMap = {
                'nigredo': [1],
                'albedo': [2],
                'rubedo': [3],
                'hermetic': [14, 15, 16],
                'rosy-cross': [30]
            };
            const targetConceptIds = themeConceptMap[state.theme] || [];
            return conceptIds.some(cid => targetConceptIds.includes(cid));
        });
    }

    // Sort emblems
    switch (state.sort) {
        case 'alpha':
            emblems.sort((a, b) => (a.title || '').localeCompare(b.title || ''));
            break;
        case 'theme':
            emblems.sort((a, b) => {
                const aTheme = getEmblemTheme(a);
                const bTheme = getEmblemTheme(b);
                return (aTheme || '').localeCompare(bTheme || '');
            });
            break;
        case 'visual':
            emblems.sort((a, b) => {
                const aVisual = (a.visual_elements || []).join(',');
                const bVisual = (b.visual_elements || []).join(',');
                return aVisual.localeCompare(bVisual);
            });
            break;
    }

    if (!emblems.length) {
        container.innerHTML = '<p class="no-results">No emblems match the current filters.</p>';
        return;
    }

    // Group by source_book
    const grouped = {};
    emblems.forEach(e => {
        const book = e.source_book || 'Unknown';
        if (!grouped[book]) grouped[book] = [];
        grouped[book].push(e);
    });

    // Render grouped sections
    let html = '';
    const bookOrder = ['Rosicrucian Emblems', 'Atalanta Fugiens', 'Hermetic Garden'];
    const orderedBooks = bookOrder.filter(b => grouped[b]).concat(
        Object.keys(grouped).filter(b => !bookOrder.includes(b))
    );

    orderedBooks.forEach(bookName => {
        const bookEmblems = grouped[bookName];
        const bookInfo = {
            'Rosicrucian Emblems': { author: 'Cramer', year: 1617, count: bookEmblems.length },
            'Atalanta Fugiens': { author: 'Maier', year: 1617, count: bookEmblems.length },
            'Hermetic Garden': { author: 'Stolcius', year: 1624, count: bookEmblems.length }
        }[bookName] || { author: '—', year: '—', count: bookEmblems.length };

        html += `
            <div class="emblem-book-section">
                <div class="emblem-book-header">
                    <h3>${bookName}</h3>
                    <div class="emblem-book-meta">${bookInfo.author} (${bookInfo.year}) — ${bookInfo.count} emblems</div>
                </div>
                <div class="emblem-gallery">
                    ${bookEmblems.map(emblem => buildCard('emblems', emblem)).join('')}
                </div>
            </div>`;
    });

    container.innerHTML = html;

    // Wire up card clicks
    container.querySelectorAll('.card').forEach(card => {
        card.addEventListener('click', e => {
            if (e.target.closest('a, button')) return;
            openModal(card.dataset.section, card.dataset.id, true);
        });
    });
}

function getEmblemTheme(emblem) {
    const conceptIds = emblem.concepts || [];
    const themeConcepts = {
        'Nigredo': [1],
        'Albedo': [2],
        'Rubedo': [3],
        'Theosis': [4],
        'Hieros Gamos': [5]
    };
    for (const [theme, ids] of Object.entries(themeConcepts)) {
        if (conceptIds.some(cid => ids.includes(cid))) {
            return theme;
        }
    }
    return 'Other';
}

// ─── Modal system ─────────────────────────────────────────────────────────────

function setupModal() {
    const closeBtn = document.getElementById('modal-close');
    const backBtn  = document.getElementById('modal-back');
    const overlay  = document.getElementById('modal');
    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    if (backBtn)  backBtn.addEventListener('click', modalBack);
    if (overlay)  overlay.addEventListener('click', e => {
        if (e.target === overlay) closeModal();
    });
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape') closeModal();
    });
}

function openModal(section, id, clearStack = false) {
    if (clearStack) modalStack.length = 0;

    const item = allData[section].find(x => String(x.id) === String(id));
    if (!item) return;

    modalStack.push({ section, id });
    renderModal(section, item);
    document.getElementById('modal').classList.add('open');
}

function renderModal(section, item) {
    const body      = document.getElementById('modal-body');
    const backBtn   = document.getElementById('modal-back');
    const crumb     = document.getElementById('modal-breadcrumb');

    backBtn.hidden  = modalStack.length <= 1;
    crumb.textContent = modalStack.length > 1
        ? modalStack.slice(0, -1).map(s => {
            const prev = allData[s.section].find(x => String(x.id) === String(s.id));
            return prev ? (prev.name || prev.title) : '';
          }).join(' › ')
        : '';

    body.innerHTML = buildModalContent(section, item);

    // Wire relational links inside the modal
    body.querySelectorAll('[data-link-section][data-link-id]').forEach(link => {
        link.addEventListener('click', e => {
            e.preventDefault();
            openModal(link.dataset.linkSection, link.dataset.linkId, false);
        });
    });
}

function closeModal() {
    document.getElementById('modal').classList.remove('open');
    modalStack.length = 0;
}

function modalBack() {
    if (modalStack.length <= 1) return;
    modalStack.pop();
    const prev = modalStack[modalStack.length - 1];
    const item = allData[prev.section].find(x => String(x.id) === String(prev.id));
    if (item) renderModal(prev.section, item);
}

// ─── Modal content builders ───────────────────────────────────────────────────

function buildModalContent(section, item) {
    switch (section) {
        case 'figures':  return buildFigureModal(item);
        case 'concepts': return buildConceptModal(item);
        case 'texts':    return buildTextModal(item);
        case 'essays':   return buildEssayModal(item);
        case 'emblems':  return buildEmblemModal(item);
        default: return '';
    }
}

function relLink(section, id, label) {
    return `<a href="#" class="rel-link" data-link-section="${section}" data-link-id="${id}">${label}</a>`;
}

function buildFigureModal(f) {
    let h = `<h2>${f.name}</h2>`;

    if (f.birth_year) {
        const lifespan = `${f.birth_year}–${f.death_year || '?'}`;
        h += `<div class="modal-meta-row">
            <span class="meta-pill">${lifespan}</span>
            <span class="meta-pill">${f.nationality || ''}</span>
            <span class="meta-pill">${f.primary_discipline || ''}</span>
            ${f.location ? `<span class="meta-pill">📍 ${f.location}</span>` : ''}
        </div>`;
    }

    if (f.essay) h += `<div class="modal-essay">${paragraphify(f.essay)}</div>`;

    if (f.embodied_practice) {
        h += `<h3>Practice &amp; Method</h3><p>${f.embodied_practice}</p>`;
    }

    if (f.scholarly_debates) {
        h += `<h3>Historiographical Debate: ${f.scholarly_debates.topic}</h3><ul>`;
        f.scholarly_debates.positions.forEach(p => { h += `<li>${p}</li>`; });
        h += '</ul>';
    }

    if (f.key_works?.length) {
        h += `<h3>Key Works</h3><ul>${f.key_works.map(w => `<li><em>${w}</em></li>`).join('')}</ul>`;
    }

    // Related concepts — clickable
    if (f.concepts?.length) {
        const links = f.concepts.map(cid => {
            const c = allData.concepts.find(x => x.id === cid);
            return c ? relLink('concepts', cid, c.name) : null;
        }).filter(Boolean);
        if (links.length) h += `<h3>Related Concepts</h3><div class="rel-links">${links.join('')}</div>`;
    }

    if (f.scholars?.length) {
        h += `<h3>Primary Scholars</h3><p class="scholars-list">${f.scholars.join(', ')}</p>`;
    }

    if (f.gender_awareness) {
        h += `<h3>Gender &amp; Access</h3><p class="gender-note">${f.gender_awareness}</p>`;
    }

    if (f.scholarship?.length) {
        h += buildScholarshipSection(f.scholarship);
    }

    return h;
}

function buildConceptModal(c) {
    let h = `<h2>${c.name}</h2>`;
    if (c.category) h += `<div class="modal-meta-row"><span class="meta-pill">${humaniseCategory(c.category)}</span></div>`;

    if (c.essay) h += `<div class="modal-essay">${paragraphify(c.essay)}</div>`;

    if (c.operational_meaning || c.philosophical_meaning || c.spiritual_meaning) {
        h += `<h3>Dimensions of Meaning</h3>`;
        if (c.operational_meaning)   h += `<p><strong>Operational:</strong> ${c.operational_meaning}</p>`;
        if (c.philosophical_meaning) h += `<p><strong>Philosophical:</strong> ${c.philosophical_meaning}</p>`;
        if (c.spiritual_meaning)     h += `<p><strong>Spiritual:</strong> ${c.spiritual_meaning}</p>`;
    }

    if (c.transmission_genealogy) {
        h += `<h3>Transmission</h3><p>${c.transmission_genealogy}</p>`;
    }

    // Related concepts — clickable
    if (c.related_concepts?.length) {
        const links = c.related_concepts.map(rcid => {
            const rc = allData.concepts.find(x => x.id === rcid);
            return rc ? relLink('concepts', rcid, rc.name) : null;
        }).filter(Boolean);
        if (links.length) h += `<h3>Related Concepts</h3><div class="rel-links">${links.join('')}</div>`;
    }

    // Emblems that illustrate this concept — clickable
    if (c.emblems?.length) {
        const links = c.emblems.slice(0, 12).map(eid => {
            const e = allData.emblems.find(x => x.id === eid);
            return e ? relLink('emblems', eid, e.title) : null;
        }).filter(Boolean);
        if (links.length) {
            const more = c.emblems.length > 12 ? ` <span class="rel-more">+${c.emblems.length - 12} more</span>` : '';
            h += `<h3>Illustrated By</h3><div class="rel-links">${links.join('')}${more}</div>`;
        }
    }

    return h;
}

function buildTextModal(t) {
    let h = `<h2>${t.title}</h2>`;
    h += `<div class="modal-meta-row">
        ${t.year ? `<span class="meta-pill">${t.year}</span>` : ''}
        ${t.language ? `<span class="meta-pill">${t.language}</span>` : ''}
        ${t.location ? `<span class="meta-pill">📍 ${t.location}</span>` : ''}
    </div>`;

    if (t.essay) h += `<div class="modal-essay">${paragraphify(t.essay)}</div>`;

    if (t.historical_context) {
        h += `<h3>Historical Context</h3><p>${t.historical_context}</p>`;
    }

    if (t.transmission_history) {
        h += `<h3>Transmission</h3><p>${t.transmission_history}</p>`;
    }

    // Related concepts — clickable
    if (t.concepts?.length) {
        const links = t.concepts.map(cid => {
            const c = allData.concepts.find(x => x.id === cid);
            return c ? relLink('concepts', cid, c.name) : null;
        }).filter(Boolean);
        if (links.length) h += `<h3>Related Concepts</h3><div class="rel-links">${links.join('')}</div>`;
    }

    if (t.scholarship?.length) h += buildScholarshipSection(t.scholarship);

    return h;
}

function buildEssayModal(essay) {
    let h = `<h2>${essay.title}</h2>`;

    h += `<div class="modal-meta-row">
        ${essay.author ? `<span class="meta-pill">${essay.author}</span>` : ''}
        ${essay.period ? `<span class="meta-pill">${essay.period}</span>` : ''}
    </div>`;

    if (essay.essay) {
        h += `<div class="modal-essay">${paragraphify(essay.essay)}</div>`;
    }

    if (essay.related_figures?.length) {
        const links = essay.related_figures.map(fname => {
            const fig = allData.figures.find(f => f.name === fname);
            return fig ? relLink('figures', fig.id, fname) : fname;
        });
        h += `<h3>Related Figures</h3><div class="rel-links">${links.join('')}</div>`;
    }

    if (essay.related_concepts?.length) {
        const links = essay.related_concepts.map(cname => {
            const c = allData.concepts.find(x => x.name === cname);
            return c ? relLink('concepts', c.id, cname) : cname;
        });
        h += `<h3>Related Concepts</h3><div class="rel-links">${links.join('')}</div>`;
    }

    if (essay.scholarship?.length) {
        h += buildScholarshipSection(essay.scholarship);
    }

    if (essay.scholarly_debates) {
        h += `<h3>Historiographical Debate: ${essay.scholarly_debates.topic}</h3><ul>`;
        essay.scholarly_debates.positions.forEach(p => {
            if (typeof p === 'object' && p.scholar) {
                h += `<li><strong>${p.scholar}:</strong> ${p.position}</li>`;
            } else {
                h += `<li>${p}</li>`;
            }
        });
        h += '</ul>';
    }

    return h;
}

function buildEmblemModal(e) {
    let h = `<h2>${e.title}</h2>`;
    h += `<div class="modal-meta-row">
        <span class="meta-pill">${e.source_book}</span>
        ${e.year ? `<span class="meta-pill">${e.year}</span>` : ''}
        ${e.type ? `<span class="meta-pill">${capitalise(e.type)}</span>` : ''}
        ${e.location ? `<span class="meta-pill">📍 ${e.location}</span>` : ''}
    </div>`;

    if (e.summary) h += `<blockquote class="visual-desc">${e.summary}</blockquote>`;

    if (e.essay && e.essay !== `[Essay on ${e.title}]` && !e.essay.startsWith('[')) {
        h += `<div class="modal-essay">${paragraphify(e.essay)}</div>`;
    }

    if (e.visual_elements?.length) {
        h += `<h3>Visual Elements</h3><div class="tag-list">${e.visual_elements.map(v => `<span class="tag">${v}</span>`).join('')}</div>`;
    }

    // Concepts illustrated — clickable
    if (e.concepts?.length) {
        const links = e.concepts.map(cid => {
            const c = allData.concepts.find(x => x.id === cid);
            return c ? relLink('concepts', cid, c.name) : null;
        }).filter(Boolean);
        if (links.length) h += `<h3>Concepts Illustrated</h3><div class="rel-links">${links.join('')}</div>`;
    }

    // Figures associated — clickable
    if (e.figures?.length) {
        const links = e.figures.map(fid => {
            const f = allData.figures.find(x => x.id === fid);
            return f ? relLink('figures', fid, f.name) : null;
        }).filter(Boolean);
        if (links.length) h += `<h3>Creator / Associated Figures</h3><div class="rel-links">${links.join('')}</div>`;
    }

    if (e.authenticity) {
        h += `<p class="authenticity-note">Authenticity: <strong>${capitalise(e.authenticity)}</strong></p>`;
    }

    if (e.scholarship?.length) h += buildScholarshipSection(e.scholarship);

    return h;
}

function buildScholarshipSection(scholarship) {
    if (!scholarship?.length) return '';
    let h = '<h3>Scholarly Apparatus</h3><div class="scholarship-list">';
    scholarship.forEach(s => {
        if (!s.scholar) return;
        h += `<div class="scholarship-entry">
            <span class="scholar-name">${s.scholar}</span>
            <span class="scholar-ref">${s.reference || ''}</span>
            ${s.quote ? `<blockquote class="scholar-quote">"${s.quote}"</blockquote>` : ''}
        </div>`;
    });
    h += '</div>';
    return h;
}

function paragraphify(text) {
    if (!text) return '';
    return text.split(/\n\n+/).map(p => `<p>${p.trim()}</p>`).join('');
}

function capitalise(s) {
    return s ? s[0].toUpperCase() + s.slice(1) : '';
}

// ─── Global search ────────────────────────────────────────────────────────────

function setupSearch() {
    const input    = document.getElementById('global-search');
    const panel    = document.getElementById('search-results-panel');
    const clearBtn = document.getElementById('search-clear');

    if (!input) return;

    let debounceTimer;

    input.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => runSearch(input.value.trim()), 200);
    });

    if (clearBtn) clearBtn.addEventListener('click', () => {
        input.value = '';
        if (panel) { panel.hidden = true; panel.innerHTML = ''; }
    });

    document.addEventListener('click', e => {
        if (panel && !e.target.closest('.search-bar-container')) panel.hidden = true;
    });

    input.addEventListener('focus', () => {
        if (input.value.trim().length >= 2) runSearch(input.value.trim());
    });
}

function getSearchTypes() {
    return [...document.querySelectorAll('input[name="search-type"]:checked')].map(c => c.value);
}

function runSearch(query) {
    const panel = document.getElementById('search-results-panel');
    if (query.length < 2) { panel.hidden = true; return; }

    const types   = getSearchTypes();
    const qLower  = query.toLowerCase();
    const results = [];

    types.forEach(section => {
        (allData[section] || []).forEach(item => {
            const name    = (item.name || item.title || '').toLowerCase();
            const summary = (item.summary || '').toLowerCase();
            const essay   = (item.essay || '').toLowerCase();

            let score = 0;
            if (name.includes(qLower))    score += 10;
            if (summary.includes(qLower)) score += 5;
            if (essay.includes(qLower))   score += 1;

            if (score > 0) results.push({ section, item, score });
        });
    });

    results.sort((a, b) => b.score - a.score);
    renderSearchResults(results, query, panel);
}

function renderSearchResults(results, query, panel) {
    if (!results.length) {
        panel.innerHTML = '<p class="search-no-results">No results found.</p>';
        panel.hidden = false;
        return;
    }

    const shown = results.slice(0, 30);
    panel.innerHTML = `
        <div class="search-result-header">${results.length} result${results.length !== 1 ? 's' : ''} for "<em>${escHtml(query)}</em>"</div>
        ${shown.map(r => {
            const name = r.item.name || r.item.title || '—';
            const labels = { figures: 'Figure', concepts: 'Concept', texts: 'Text', essays: 'Essay', emblems: 'Emblem' };
            const snippet = highlight(truncate(r.item.summary || '', 120), query);
            return `<div class="search-result-item" data-section="${r.section}" data-id="${r.item.id}">
                <span class="card-badge badge-${r.section}">${labels[r.section]}</span>
                <span class="search-result-name">${highlight(name, query)}</span>
                <span class="search-result-snippet">${snippet}</span>
            </div>`;
        }).join('')}
        ${results.length > 30 ? `<div class="search-result-footer">Showing top 30 of ${results.length}</div>` : ''}
    `;
    panel.hidden = false;

    panel.querySelectorAll('.search-result-item').forEach(el => {
        el.addEventListener('click', () => {
            openModal(el.dataset.section, el.dataset.id, true);
            panel.hidden = true;
            document.getElementById('global-search').value = '';
        });
    });
}

function highlight(text, query) {
    if (!query) return escHtml(text);
    const safe   = escHtml(text);
    const safeQ  = escHtml(query);
    const re     = new RegExp(`(${escRe(safeQ)})`, 'gi');
    return safe.replace(re, '<mark>$1</mark>');
}

function truncate(str, max) {
    return str.length <= max ? str : str.slice(0, max) + '…';
}

function escHtml(s) {
    return String(s)
        .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
        .replace(/"/g,'&quot;');
}

function escRe(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// ─── Navigation ───────────────────────────────────────────────────────────────

function setupNavigation() {
    const navBtns  = document.querySelectorAll('.nav-btn');
    const sections = document.querySelectorAll('.section');

    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            navBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            sections.forEach(s => s.classList.remove('active'));
            const section = btn.dataset.section;
            document.getElementById(section).classList.add('active');

            // Track active section for context-aware UI
            activeSection = section;

            if (section === 'map') {
                setTimeout(() => {
                    if (window._leafletMap) {
                        window._leafletMap.invalidateSize();
                        window._leafletMap.setView([50, 12], 4);
                    }
                }, 150);
            } else if (section === 'emblem-books') {
                renderEmblemBooks();
            }
        });
    });
}

// ─── Map ──────────────────────────────────────────────────────────────────────

function initializeMap() {
    const map = L.map('map-container').setView([50, 12], 4);
    window._leafletMap = map;

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);

    const figureGroup  = L.featureGroup();
    const textGroup    = L.featureGroup();
    const emblemGroup  = L.featureGroup();
    const centerGroup  = L.featureGroup();

    // ── Figures ──────────────────────────────────────────────────
    allData.figures.forEach(figure => {
        if (!figure.lat || !figure.lng) return;
        const marker = L.circleMarker([figure.lat, figure.lng], {
            radius: 7, fillColor: '#e74c3c', color: '#c0392b',
            weight: 2, opacity: 1, fillOpacity: 0.8
        });
        const dateRange = `${figure.birth_year || '?'}–${figure.death_year || '?'}`;
        marker.bindPopup(buildMapPopup(figure.name, `${dateRange} · ${figure.nationality || ''}`, figure.summary));
        marker.bindTooltip(buildMapTooltip(figure.name, dateRange, figure.scholars), { sticky: true, className: 'map-tooltip' });
        marker.on('click', () => {
            openModal('figures', figure.id, true);
            showMapSidePanel('figures', figure);
        });
        figureGroup.addLayer(marker);
    });

    // ── Texts ────────────────────────────────────────────────────
    allData.texts.forEach(text => {
        if (!text.lat || !text.lng) return;
        const marker = L.circleMarker([text.lat, text.lng], {
            radius: 6, fillColor: '#3498db', color: '#2980b9',
            weight: 2, opacity: 1, fillOpacity: 0.8
        });
        const year = text.year || '?';
        marker.bindPopup(buildMapPopup(text.title, `${year} · ${text.language || ''} · ${text.location || ''}`, text.summary));
        marker.bindTooltip(buildMapTooltip(text.title, year, []), { sticky: true, className: 'map-tooltip' });
        marker.on('click', () => {
            openModal('texts', text.id, true);
            showMapSidePanel('texts', text);
        });
        textGroup.addLayer(marker);
    });

    // ── Emblems (grouped by publication city) ────────────────────
    const emblemCities = {
        'Frankfurt am Main': { lat: 50.1109, lng: 8.6821, books: [] },
        'Oppenheim':         { lat: 49.8612, lng: 8.3699, books: [] },
        'Prague':            { lat: 50.0755, lng: 14.4378, books: [] }
    };

    allData.emblems.forEach(emb => {
        const city = emblemCities[emb.location];
        if (city && !city.books.includes(emb.source_book)) city.books.push(emb.source_book);
    });

    Object.entries(emblemCities).forEach(([city, data]) => {
        if (!data.books.length) return;
        const count = allData.emblems.filter(e => e.location === city).length;
        const marker = L.circleMarker([data.lat, data.lng], {
            radius: 9, fillColor: '#8e44ad', color: '#6c3483',
            weight: 2, opacity: 1, fillOpacity: 0.85
        });
        marker.bindPopup(`<strong>${city}</strong><br><em>Emblem Books:</em><br>${data.books.join('<br>')}<br>${count} emblems`);
        emblemGroup.addLayer(marker);
    });

    // ── Learning centers (from map_centers in data) ───────────────
    const centers = allData.map_centers || [];
    centers.forEach(c => {
        const marker = L.circleMarker([c.lat, c.lng], {
            radius: 10, fillColor: '#f39c12', color: '#d68910',
            weight: 2, opacity: 1, fillOpacity: 0.82
        });
        const popupHtml = `<strong style="font-size:1rem;color:#8b4513">${escHtml(c.name)}</strong>
            <br><em style="font-size:0.8em;color:#5c3d2e">${escHtml(c.role)}</em>
            <br><span style="font-size:0.82em;color:#444;line-height:1.5;display:block;margin-top:0.4rem">${escHtml(truncate(c.description || '', 200))}</span>`;
        marker.bindPopup(popupHtml, { maxWidth: 300 });
        marker.bindTooltip(`<strong>${escHtml(c.name)}</strong>`, { sticky: true, className: 'map-tooltip' });
        marker.on('click', () => showMapSidePanel('center', c));
        centerGroup.addLayer(marker);
    });

    // Add all layers
    [figureGroup, textGroup, emblemGroup, centerGroup].forEach(g => g.addTo(map));

    const all = L.featureGroup([figureGroup, textGroup, emblemGroup, centerGroup]);
    if (all.getLayers().length) map.fitBounds(all.getBounds(), { padding: [50, 50], maxZoom: 6 });

    // Layer toggle checkboxes
    [
        ['layer-figures',  figureGroup],
        ['layer-texts',    textGroup],
        ['layer-emblems',  emblemGroup],
        ['layer-centers',  centerGroup],
    ].forEach(([id, group]) => {
        const cb = document.getElementById(id);
        if (!cb) return;
        cb.addEventListener('change', () => {
            cb.checked ? group.addTo(map) : map.removeLayer(group);
        });
    });
}

function buildMapTooltip(name, dateOrYear, scholars) {
    let tip = `<strong>${escHtml(name)}</strong><br><em>${escHtml(dateOrYear)}</em>`;
    if (scholars?.length) tip += `<br><span style="font-size:0.8em">Scholars: ${escHtml(scholars.join(', '))}</span>`;
    return tip;
}

function buildMapPopup(title, meta, summary) {
    return `<strong>${escHtml(title)}</strong><br>
            <em style="font-size:0.85em">${escHtml(meta)}</em><br>
            <span style="font-size:0.85em;color:#555">${escHtml(truncate(summary || '', 120))}</span>`;
}

function showMapSidePanel(section, item) {
    const panel = document.getElementById('map-side-panel');
    const title = document.getElementById('map-side-title');
    const content = document.getElementById('map-side-content');

    const name = item.name || item.title || '—';
    title.textContent = name;

    let html = '';
    if (section === 'figures') {
        html = `<p><strong>Life Span:</strong> ${item.birth_year || '?'}–${item.death_year || '?'}</p>
                <p><strong>Nationality:</strong> ${escHtml(item.nationality || 'Unknown')}</p>
                <p><strong>Location:</strong> ${escHtml(item.location || 'Unknown')}</p>
                ${item.primary_discipline ? `<p><strong>Discipline:</strong> ${escHtml(item.primary_discipline)}</p>` : ''}
                <p class="map-side-summary">${paragraphify(item.summary || '')}</p>`;
    } else if (section === 'texts') {
        html = `<p><strong>Year:</strong> ${item.year || '?'}</p>
                <p><strong>Language:</strong> ${escHtml(item.language || 'Unknown')}</p>
                <p><strong>Location:</strong> ${escHtml(item.location || 'Unknown')}</p>
                <p class="map-side-summary">${paragraphify(item.summary || '')}</p>
                ${item.historical_context ? `<p><em>${escHtml(item.historical_context)}</em></p>` : ''}`;
    } else if (section === 'center') {
        html = `<p><em style="color:var(--burnt-sienna)">${escHtml(item.role || '')}</em></p>
                <p class="map-side-summary">${paragraphify(item.description || '')}</p>`;
    }

    content.innerHTML = html;
    panel.classList.add('open');

    // Re-attach close listener cleanly
    const closeBtn = document.getElementById('map-side-close');
    if (closeBtn) {
        closeBtn.onclick = () => panel.classList.remove('open');
    }
}

// ─── Timeline ─────────────────────────────────────────────────────────────────

function renderTimeline(activeCategory = 'all') {
    const container = document.getElementById('timeline-container');
    if (!container) return;

    const events = (allData.timeline || []).slice().sort((a, b) => a.year - b.year);

    container.innerHTML = '';

    events.forEach(ev => {
        const visible = activeCategory === 'all' || ev.category === activeCategory;
        const div = document.createElement('div');
        div.className = `tl-event ${ev.category}${visible ? '' : ' hidden'}`;

        const relatedFigs = (ev.related_figures || []).filter(Boolean);
        const relatedTexts = (ev.related_texts || []).filter(Boolean);
        const relatedHtml = (relatedFigs.length || relatedTexts.length)
            ? `<div class="tl-related">
                ${relatedFigs.length ? `<strong>Figures:</strong> ${escHtml(relatedFigs.join(', '))}` : ''}
                ${relatedFigs.length && relatedTexts.length ? ' &nbsp;·&nbsp; ' : ''}
                ${relatedTexts.length ? `<strong>Texts:</strong> ${escHtml(relatedTexts.join(', '))}` : ''}
               </div>`
            : '';

        const badgeLabels = { historical: 'Historical', text: 'Publication', figure: 'Figure', discovery: 'Discovery' };

        div.innerHTML = `
            <span class="tl-dot ${ev.category}"></span>
            <div class="tl-card">
                <div class="tl-header">
                    <span class="tl-year">${ev.year}</span>
                    <span class="tl-title">${escHtml(ev.title)}</span>
                    <span class="tl-badge ${ev.category}">${badgeLabels[ev.category] || ev.category}</span>
                </div>
                <div class="tl-desc">${escHtml(ev.description)}</div>
                ${relatedHtml}
            </div>`;

        container.appendChild(div);
    });
}

function setupTimelineFilters() {
    document.querySelectorAll('.tl-filter').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tl-filter').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const cat = btn.dataset.category;
            document.querySelectorAll('.tl-event').forEach(ev => {
                ev.classList.toggle('hidden', cat !== 'all' && !ev.classList.contains(cat));
            });
        });
    });
}
