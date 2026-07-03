// api.js — centralised API calls for Project Shikhara

const API_BASE = 'http://127.0.0.1:8000';


async function apiFetch(path) {
    const response = await fetch(`${API_BASE}${path}`);
    if (!response.ok) throw new Error(`API error: ${response.status}`);
    return response.json();
}


async function fetchTemples({ page = 1, page_size = 15, city = null, state = null } = {}) {
    const params = new URLSearchParams({ page, page_size });
    if (city)  params.set('city', city);
    if (state) params.set('state', state);
    return apiFetch(`/temples?${params}`);
}


async function fetchTemple(id) {
    return apiFetch(`/temples/${id}`);
}


async function fetchCities() {
    return apiFetch('/cities');
}


async function askChatbotStream(question, onToken) {
    const response = await fetch(`${API_BASE}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
    });
    if (!response.ok) throw new Error(`Chat API error: ${response.status}`);

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const token = decoder.decode(value, { stream: true });
        onToken(token);
    }
}