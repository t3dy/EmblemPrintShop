// Timeline interactive component
let allEvents = [];
let filteredEvents = [];
let selectedEvent = null;

async function initTimeline() {
    // Fetch timeline data
    try {
        const response = await fetch('./data/timeline_events.json');
        const data = await response.json();
        allEvents = data.timeline_events || [];
        filteredEvents = [...allEvents];

        renderTimeline();
        renderStats();
        setupFilters();
    } catch (error) {
        console.error('Error loading timeline events:', error);
        document.getElementById('eventsContainer').innerHTML =
            '<p style="color: red;">Error loading timeline data</p>';
    }
}

function setupFilters() {
    const categoryFilter = document.getElementById('categoryFilter');
    const centuryFilter = document.getElementById('centuryFilter');
    const searchInput = document.getElementById('searchInput');

    categoryFilter.addEventListener('change', applyFilters);
    centuryFilter.addEventListener('change', applyFilters);
    searchInput.addEventListener('input', applyFilters);
}

function applyFilters() {
    const category = document.getElementById('categoryFilter').value;
    const century = document.getElementById('centuryFilter').value;
    const search = document.getElementById('searchInput').value.toLowerCase();

    filteredEvents = allEvents.filter(event => {
        // Category filter
        if (category && event.category !== category) return false;

        // Century filter
        if (century) {
            const year = parseInt(event.date);
            const centuryStart = parseInt(century);
            const centuryEnd = centuryStart + 99;
            if (year < centuryStart || year > centuryEnd) return false;
        }

        // Search filter
        if (search) {
            const eventText = `${event.event} ${event.significance} ${event.location}`.toLowerCase();
            if (!eventText.includes(search)) return false;
        }

        return true;
    });

    renderTimeline();
}

function renderTimeline() {
    const container = document.getElementById('eventsContainer');
    container.innerHTML = '';

    // Sort by date
    const sorted = [...filteredEvents].sort((a, b) =>
        parseInt(a.date) - parseInt(b.date)
    );

    if (sorted.length === 0) {
        container.innerHTML = '<p style="color: var(--deep-brown); width: 100%; text-align: center; padding: 2rem;">No events match current filters</p>';
        return;
    }

    sorted.forEach(event => {
        const eventEl = document.createElement('div');
        eventEl.className = 'timeline-event';
        eventEl.onclick = () => selectEvent(event);

        const categoryColor = getCategoryColor(event.category);
        eventEl.style.borderLeftColor = categoryColor;

        eventEl.innerHTML = `
            <div class="event-date">${event.date}</div>
            <div class="event-category">${humanizeCategory(event.category)}</div>
            <div class="event-title">${event.event}</div>
            <div class="event-significance">${truncate(event.significance, 80)}</div>
        `;

        container.appendChild(eventEl);
    });

    document.querySelectorAll('.timeline-event').forEach((el, i) => {
        el.style.left = (i * 240) + 'px';
    });
}

function selectEvent(event) {
    selectedEvent = event;
    const panel = document.getElementById('detailsPanel');

    let html = `
        <div class="details-header">
            <h3>${event.event}</h3>
        </div>
        <div class="detail-item">
            <div class="detail-label">Date:</div>
            <div class="detail-value">${event.date}${event.date_precision === 'range' ? ' (range)' : ''}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Location:</div>
            <div class="detail-value">${event.location || 'Unknown'}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Category:</div>
            <div class="detail-value">${humanizeCategory(event.category)}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Significance:</div>
            <div class="detail-value">${event.significance}</div>
        </div>
    `;

    if (event.figure_name) {
        html += `
            <div class="detail-item">
                <div class="detail-label">Figure:</div>
                <div class="detail-value">${event.figure_name}</div>
            </div>
        `;
    }

    if (event.text_title) {
        html += `
            <div class="detail-item">
                <div class="detail-label">Text:</div>
                <div class="detail-value"><em>${event.text_title}</em></div>
            </div>
        `;
    }

    if (event.scholarly_source) {
        html += `
            <div class="detail-item">
                <div class="detail-label">Source:</div>
                <div class="detail-value">${event.scholarly_source}</div>
            </div>
        `;
    }

    if (event.related_concepts && event.related_concepts.length > 0) {
        html += `
            <div class="detail-item">
                <div class="detail-label">Related Concepts:</div>
                <div class="detail-value">${event.related_concepts.slice(0, 5).join(', ')}</div>
            </div>
        `;
    }

    panel.innerHTML = html;
}

function renderStats() {
    const stats = document.getElementById('statsContainer');

    const totalEvents = allEvents.length;
    const dateRange = {
        start: Math.min(...allEvents.map(e => parseInt(e.date))),
        end: Math.max(...allEvents.map(e => parseInt(e.date)))
    };

    const categories = {};
    allEvents.forEach(event => {
        categories[event.category] = (categories[event.category] || 0) + 1;
    });

    const figureEvents = allEvents.filter(e => e.figure_id).length;
    const textEvents = allEvents.filter(e => e.text_id).length;

    stats.innerHTML = `
        <div class="stat-box">
            <div class="stat-number">${totalEvents}</div>
            <div class="stat-label">Total Events</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">${dateRange.end - dateRange.start + 1}</div>
            <div class="stat-label">Years Covered</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">${figureEvents}</div>
            <div class="stat-label">Figure Events</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">${textEvents}</div>
            <div class="stat-label">Publication Events</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">${Object.keys(categories).length}</div>
            <div class="stat-label">Event Categories</div>
        </div>
    `;
}

function getCategoryColor(category) {
    const colors = {
        'figure_birth': '#8b4513',
        'figure_death': '#a0522d',
        'text_publication': '#5c3d2e',
        'movement': '#704214',
        'event': '#6b4423'
    };
    return colors[category] || '#8b4513';
}

function humanizeCategory(category) {
    const names = {
        'figure_birth': 'Birth',
        'figure_death': 'Death',
        'text_publication': 'Publication',
        'movement': 'Movement',
        'event': 'Event'
    };
    return names[category] || category;
}

function truncate(text, length) {
    return text.length > length ? text.substring(0, length) + '...' : text;
}

// Initialize on load
document.addEventListener('DOMContentLoaded', initTimeline);
