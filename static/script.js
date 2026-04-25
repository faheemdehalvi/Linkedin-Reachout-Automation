document.addEventListener('DOMContentLoaded', () => {
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const messagesArea = document.getElementById('chat-messages');
    
    // Auto-resize textarea
    chatInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        if (this.value === '') {
            this.style.height = 'auto';
        }
    });

    // Enter to send (Shift+Enter for newline)
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    sendBtn.addEventListener('click', sendMessage);

    // Sidebar buttons
    document.getElementById('btn-suggestions').addEventListener('click', () => {
        chatInput.value = "Suggest people to contact";
        sendMessage();
    });

    document.getElementById('btn-analyze').addEventListener('click', () => {
        chatInput.value = "Analyze patterns in my reference DMs";
        sendMessage();
    });

    document.getElementById('btn-voice').addEventListener('click', () => {
        chatInput.value = "Show my voice profile";
        sendMessage();
    });

    async function sendMessage() {
        const text = chatInput.value.trim();
        if (!text) return;

        // Reset input
        chatInput.value = '';
        chatInput.style.height = 'auto';

        // Add user message
        appendMessage('user', text);

        // Show typing indicator
        const typingId = showTypingIndicator();

        try {
            // Send to backend
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: text })
            });

            const data = await response.json();
            
            // Remove typing indicator
            removeElement(typingId);

            // Add AI response parsed as markdown
            appendMessage('ai', data.response || "Sorry, I couldn't process that.");
            
        } catch (error) {
            removeElement(typingId);
            appendMessage('ai', "Error connecting to the server. Is the FastAPI backend running?");
        }
    }

    function appendMessage(sender, text) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}-message fade-in`;

        const avatar = document.createElement('div');
        avatar.className = 'avatar';
        avatar.innerHTML = sender === 'ai' ? '<i class="fa-solid fa-brain"></i>' : '<i class="fa-solid fa-user"></i>';

        const content = document.createElement('div');
        content.className = 'message-content';
        
        if (sender === 'ai') {
            // Parse Markdown
            content.innerHTML = marked.parse(text);
        } else {
            content.innerHTML = `<p>${text.replace(/\n/g, '<br>')}</p>`;
        }

        msgDiv.appendChild(avatar);
        msgDiv.appendChild(content);
        messagesArea.appendChild(msgDiv);

        scrollToBottom();
    }

    function showTypingIndicator() {
        const id = 'typing-' + Date.now();
        const msgDiv = document.createElement('div');
        msgDiv.id = id;
        msgDiv.className = `message ai-message fade-in`;

        const avatar = document.createElement('div');
        avatar.className = 'avatar';
        avatar.innerHTML = '<i class="fa-solid fa-brain"></i>';

        const content = document.createElement('div');
        content.className = 'message-content';
        content.innerHTML = `
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;

        msgDiv.appendChild(avatar);
        msgDiv.appendChild(content);
        messagesArea.appendChild(msgDiv);

        scrollToBottom();
        return id;
    }

    function removeElement(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    function scrollToBottom() {
        messagesArea.scrollTo({
            top: messagesArea.scrollHeight,
            behavior: 'smooth'
        });
    }
});
