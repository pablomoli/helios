// public/js/chat.js

document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');

    // Function to add a message to the chat window
    function appendMessage(content, isUser) {
        const alignment = isUser ? 'justify-content-end' : 'justify-content-start';
        const bgColor = isUser ? 'bg-primary text-white' : 'bg-light';

        const messageHtml = `
            <div class="d-flex ${alignment} mb-3">
                <div class="p-3 ${bgColor} rounded-3 shadow-sm" style="max-width: 80%;">
                    ${content}
                </div>
            </div>
        `;
        chatMessages.insertAdjacentHTML('beforeend', messageHtml);

        // Auto-scroll to the bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const message = userInput.value.trim();
        if (!message) return;

        // 1. Display the user's message immediately
        appendMessage(message, true);

        // Clear the input field
        userInput.value = '';

        // Add a "typing" indicator (optional but good for UX)
        const typingIndicator = '<div id="typing-indicator" class="d-flex justify-content-start mb-3"><div class="p-3 bg-light rounded-3 shadow-sm">...typing</div></div>';
        chatMessages.insertAdjacentHTML('beforeend', typingIndicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            // 2. Make the API call to your Express backend
            const response = await fetch('/snowflake/complete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: message })
            });

            // 3. Handle the response
            if (!response.ok) {
                throw new Error(`Server returned an error: ${response.status} ${response.statusText}`);
            }


            const data = await response.json();

            // 4. Remove typing indicator
            document.getElementById('typing-indicator')?.remove();

            // 5. Display the bot's response
            appendMessage(data.botResponse, false);

        } catch (error) {
            // Remove typing indicator on error
            document.getElementById('typing-indicator')?.remove();
            console.error('Fetch error:', error);
            appendMessage('Sorry, I am unable to connect to the assistant right now.', false);
        }
    });
});
