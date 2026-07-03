// chatbot.js — chatbot bar interaction

document.addEventListener('DOMContentLoaded', () => {
    const input    = document.getElementById('chat-input');
    const btn      = document.getElementById('chat-btn');
    const response = document.getElementById('chat-response');

    if (!input || !btn || !response) return;

    async function submitQuestion() {
        const question = input.value.trim();
        if (!question) return;

        btn.disabled    = true;
        btn.textContent = 'Thinking...';
        response.style.display = 'block';
        response.innerHTML = `
            <div class="chat-answer">
                <span class="chat-q">Q: ${question}</span>
                <span class="chat-status" id="chat-status">⏳ Searching the temple directory...</span>
                <span class="chat-a" id="chat-answer-text" style="display:none"></span>
            </div>`;

        const statusEl = document.getElementById('chat-status');
        const answerEl = document.getElementById('chat-answer-text');

        try {
            const res = await fetch(`${API_BASE}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question })
            });

            if (!res.ok) throw new Error(`API error: ${res.status}`);
            const data = await res.json();

            statusEl.style.display = 'none';
            answerEl.style.display = 'block';
            answerEl.textContent = data.answer;

        } catch (e) {
            statusEl.textContent = 'Sorry, something went wrong. Please try again.';
            statusEl.className = 'chat-error';
        } finally {
            btn.disabled    = false;
            btn.textContent = 'Ask';
        }
    }

    btn.addEventListener('click', submitQuestion);
    input.addEventListener('keydown', e => {
        if (e.key === 'Enter') submitQuestion();
    });
});