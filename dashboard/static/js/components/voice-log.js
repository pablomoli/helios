// Voice Log Component
class VoiceLog {
    constructor() {
        this.logContainer = document.getElementById('voiceLog');
        this.maxEntries = 10;
    }

    addEntry(command, response, timestamp) {
        const entry = document.createElement('div');
        entry.className = 'voice-entry';

        const time = new Date(timestamp * 1000).toLocaleTimeString();

        entry.innerHTML = `
            <span class="voice-time">${time}</span>
            <span class="voice-text"><strong>User:</strong> ${command}</span>
            <span class="voice-text"><strong>Helios:</strong> ${response}</span>
        `;

        this.logContainer.prepend(entry);

        // Keep only last N entries
        while (this.logContainer.children.length > this.maxEntries) {
            this.logContainer.removeChild(this.logContainer.lastChild);
        }
    }
}

const voiceLog = new VoiceLog();
