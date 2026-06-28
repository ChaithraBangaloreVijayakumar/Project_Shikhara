// sidebar.js — temple detail sidebar logic

function openSidebar(temple) {
    document.getElementById('sidebar-name').textContent = temple.name;
    document.getElementById('sidebar-body').innerHTML   = buildSidebarHTML(temple);
    document.getElementById('sidebar').classList.add('open');
}

function closeSidebar() {
    document.getElementById('sidebar').classList.remove('open');
    resetActiveMarker();
    setActiveRow(null);
}

// Close button
document.addEventListener('DOMContentLoaded', () => {
    const closeBtn = document.getElementById('sidebar-close');
    if (closeBtn) closeBtn.addEventListener('click', closeSidebar);
});


function buildSidebarHTML(t) {
    const days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
    const address = [t.street, t.city, t.postal_code].filter(Boolean).join(', ');

    let html = '';

    // Address
    html += `
    <div class="sidebar-section">
        <p class="sidebar-section-title">Address</p>
        <p class="sidebar-address">
            ${t.google_maps_url
                ? `<a href="${t.google_maps_url}" target="_blank" rel="noopener">${address}</a>`
                : address || '—'
            }
        </p>
        ${t.state ? `<p style="font-size:0.8rem;color:var(--colour-text-muted);margin-top:0.25rem">${t.state}</p>` : ''}
    </div>`;

    // Contact
    const hasContact = Object.values(t.contact).some(v => v.length > 0);
    if (hasContact) {
        html += `<div class="sidebar-section"><p class="sidebar-section-title">Contact</p>`;
        const contactTypes = [
            { key: 'phone',     label: 'Phone',     isLink: false },
            { key: 'email',     label: 'Email',     isLink: true,  prefix: 'mailto:' },
            { key: 'website',   label: 'Website',   isLink: true },
            { key: 'facebook',  label: 'Facebook',  isLink: true },
            { key: 'instagram', label: 'Instagram', isLink: true },
        ];
        contactTypes.forEach(({ key, label, isLink, prefix = '' }) => {
            const values = t.contact[key];
            if (!values || values.length === 0) return;
            values.forEach(v => {
                html += `
                <div class="sidebar-contact-row">
                    <span class="contact-type">${label}</span>
                    ${isLink
                        ? `<a href="${prefix}${v}" target="_blank" rel="noopener">${v.replace(/^https?:\/\/(www\.)?/, '')}</a>`
                        : `<span>${v}</span>`
                    }
                </div>`;
            });
        });
        html += `</div>`;
    }

    // Opening hours
    const hasHours = days.some(d => t.opening_hours[d]);
    if (hasHours) {
        html += `<div class="sidebar-section"><p class="sidebar-section-title">Opening Hours</p>`;
        days.forEach(day => {
            if (!t.opening_hours[day]) return;
            html += `
            <div class="sidebar-hours-row">
                <span class="day">${day}</span>
                <span class="hours">${t.opening_hours[day]}</span>
            </div>`;
        });
        html += `</div>`;
    }

    // Note
    if (t.note) {
        html += `
        <div class="sidebar-section">
            <p class="sidebar-section-title">Note</p>
            <p class="sidebar-note">${t.note}</p>
        </div>`;
    }

    return html;
}