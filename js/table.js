// table.js — temple table rendering and pagination

// ── Opening hours compressor ──────────────────────────────────────────────────

function compactHours(opening_hours) {
    if (!opening_hours) return '—';
    const days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
    const short = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];

    // Build list of [dayIndex, hours] for days that have hours
    const entries = days
        .map((d, i) => ({ i, hours: opening_hours[d] }))
        .filter(e => e.hours);

    if (entries.length === 0) return '—';

    // Group consecutive days with the same hours
    const groups = [];
    let current = { start: entries[0].i, end: entries[0].i, hours: entries[0].hours };

    for (let k = 1; k < entries.length; k++) {
        const e = entries[k];
        if (e.hours === current.hours && e.i === current.end + 1) {
            current.end = e.i;
        } else {
            groups.push({ ...current });
            current = { start: e.i, end: e.i, hours: e.hours };
        }
    }
    groups.push(current);

    return groups.map(g => {
        const label = g.start === g.end
            ? short[g.start]
            : `${short[g.start]}–${short[g.end]}`;
        return `${label}: ${g.hours}`;
    }).join('<br>');
}


// ── Contact details cell ──────────────────────────────────────────────────────

function formatContactDetails(contact) {
    const rows = [];

    if (contact.email?.length) {
        contact.email.forEach(v => {
            rows.push(`<a href="mailto:${v}" class="contact-detail-row">
                <i class="fa-solid fa-envelope contact-icon"></i>${v}
            </a>`);
        });
    }
    if (contact.website?.length) {
        contact.website.forEach(v => {
            rows.push(`<a href="${v}" target="_blank" rel="noopener" class="contact-detail-row">
                <i class="fa-solid fa-globe contact-icon"></i>${v.replace(/^https?:\/\/(www\.)?/, '')}
            </a>`);
        });
    }
    if (contact.facebook?.length) {
        contact.facebook.forEach(v => {
            rows.push(`<a href="${v}" target="_blank" rel="noopener" class="contact-detail-row">
                <i class="fa-brands fa-facebook contact-icon"></i>${v.replace(/^https?:\/\/(www\.)?/, '')}
            </a>`);
        });
    }
    if (contact.instagram?.length) {
        contact.instagram.forEach(v => {
            rows.push(`<a href="${v}" target="_blank" rel="noopener" class="contact-detail-row">
                <i class="fa-brands fa-instagram contact-icon"></i>${v.replace(/^https?:\/\/(www\.)?/, '')}
            </a>`);
        });
    }

    return rows.length ? `<div class="contact-details">${rows.join('')}</div>` : '—';
}


// ── Table rendering ───────────────────────────────────────────────────────────

function renderTable(temples, onRowClick, pageOffset = 0) {
    const tbody = document.getElementById('temple-tbody');
    if (!temples || temples.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="loading">No temples found.</td></tr>';
        return;
    }

    tbody.innerHTML = temples.map((t, idx) => {
        const address = [t.street, t.city, t.postal_code].filter(Boolean).join(', ');
        const mapsUrl = t.google_maps_url;
        const serial  = pageOffset + idx + 1;

        return `
        <tr data-id="${t.id}">
            <td class="serial-col">${serial}</td>
            <td class="temple-name">${t.name}</td>
            <td class="temple-address">
                ${mapsUrl
                    ? `<a href="${mapsUrl}" target="_blank" rel="noopener">${address}</a>`
                    : address || '—'
                }
                <br><small style="color:var(--colour-text-muted)">${t.state || ''}</small>
            </td>
            <td class="phone-col">${t.contact.phone?.length
                ? t.contact.phone.map(p => `<div>${p}</div>`).join('')
                : '—'
            }</td>
            <td>${formatContactDetails(t.contact)}</td>
            <td class="hours-cell">${compactHours(t.opening_hours)}</td>
        </tr>`;
    }).join('');

    // Attach row click listeners
    tbody.querySelectorAll('tr[data-id]').forEach(row => {
        row.addEventListener('click', () => onRowClick(parseInt(row.dataset.id)));
    });
}


// ── Row highlight ─────────────────────────────────────────────────────────────

function setActiveRow(templeId) {
    document.querySelectorAll('.temple-table tr').forEach(r => r.classList.remove('active'));
    if (!templeId) return;
    const row = document.querySelector(`.temple-table tr[data-id="${templeId}"]`);
    if (row) {
        row.classList.add('active');
        row.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}


// ── Pagination ────────────────────────────────────────────────────────────────

function renderPagination(total, page, pageSize, onPageChange) {
    const pages     = Math.ceil(total / pageSize);
    const container = document.getElementById('pagination');
    if (!container) return;

    if (pages <= 1) {
        container.innerHTML = '';
        return;
    }

    container.innerHTML = '';

    const addBtn = (label, targetPage, isActive = false, isDisabled = false) => {
        const btn = document.createElement('button');
        btn.className = `page-btn${isActive ? ' active' : ''}`;
        btn.textContent = label;
        btn.disabled = isDisabled;
        if (!isDisabled) btn.addEventListener('click', () => onPageChange(targetPage));
        container.appendChild(btn);
    };

    const addEllipsis = () => {
        const span = document.createElement('span');
        span.textContent = '…';
        span.style.cssText = 'color:var(--colour-text-muted);padding:0 0.25rem';
        container.appendChild(span);
    };

    addBtn('←', page - 1, false, page === 1);
    for (let i = 1; i <= pages; i++) {
        addBtn(i, i, i === page);
    }
    addBtn('→', page + 1, false, page === pages);
}


// ── Temple count ──────────────────────────────────────────────────────────────

function updateTempleCount(total, filtered = false) {
    const el = document.getElementById('temple-count');
    if (el) {
        el.textContent = filtered
            ? `${total} temple${total !== 1 ? 's' : ''} found`
            : `${total} temple${total !== 1 ? 's' : ''} across Germany`;
    }
}