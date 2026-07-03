// chatbot.js — streaming chatbot with status updates

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
        let answerStarted = false;

        try {
            const res = await fetch(`${API_BASE}/chat/stream`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question })
            });

            const reader  = res.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });

                // Process complete tokens from buffer
                while (buffer.length > 0) {
                    if (buffer.startsWith('__STATUS__')) {
                        const end = buffer.indexOf('\n') === -1 ? buffer.length : buffer.indexOf('\n');
                        const msg = buffer.slice('__STATUS__'.length, end);
                        statusEl.textContent = `⏳ ${msg}`;
                        buffer = buffer.slice(end + 1);
                    } else if (buffer.startsWith('__ANSWER__')) {
                        // Switch from status to answer display
                        statusEl.style.display = 'none';
                        answerEl.style.display = 'block';
                        answerStarted = true;
                        buffer = buffer.slice('__ANSWER__'.length);
                    } else if (answerStarted) {
                        answerEl.textContent += buffer;
                        buffer = '';
                    } else {
                        break;
                    }
                }
            }
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