const { ipcRenderer } = require('electron');
const showdown = require('showdown'); // Import the Showdown library for Markdown conversion

document.addEventListener('DOMContentLoaded', () => {
    const processButton = document.getElementById('process-button');

    processButton.addEventListener('click', () => {
        const userInput = document.getElementById('description-entry').value.trim();
        if (!userInput) {
            displayMessage("Please, enter a description.", "system");
            return;
        }
        displayMessage(`<span style="color:#25733f">**You:** ${userInput}<\span>`, "user");
        ipcRenderer.send('process-description', userInput);
        document.getElementById('description-entry').value = ''; // Clear input field
    });

    ipcRenderer.on('display-conversation', (event, text, sender) => {
        displayMessage(text, sender);
    });

    function displayMessage(text, sender) {
        const chatDisplay = document.getElementById('chat-display');
        const message = document.createElement('div');
        message.classList.add(sender === "system" ? "system-message" : "user-message");

        // Convert Markdown to HTML
        const converter = new showdown.Converter({ encoding: 'utf-16' });
        const htmlText = converter.makeHtml(text);

        // Apply Helvetica font
        message.innerHTML = `<span style="font-family: Helvetica">${htmlText}</span>`;
        chatDisplay.appendChild(message);
        chatDisplay.scrollTop = chatDisplay.scrollHeight; // Scroll to bottom
    }
});
