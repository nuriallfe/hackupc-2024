const { ipcRenderer } = require('electron');
const showdown = require('showdown'); // Import the Showdown library for Markdown conversion

document.addEventListener('DOMContentLoaded', () => {
    const processButton = document.getElementById('process-button');
    const imageUploadInput = document.getElementById('image-upload');
    const descriptionEntry = document.getElementById('description-entry');
    const sidebar = document.getElementById('sidebar');
    let generatedImageElement = null; // Variable to hold the reference to the generated image element

    document.getElementById('description-entry').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            processButton.click();
        }
    });

    processButton.addEventListener('click', () => {
        const userInput = document.getElementById('description-entry').value.trim();
        const imageURL = imageUploadInput.files.length > 0 ? imageUploadInput.files[0].path : null;

        if (!userInput && !imageURL) {
            displayMessage("Please, enter a description or upload an image.", "system");
            return;
        }

        // Disable the input and button
        descriptionEntry.disabled = true;
        processButton.disabled = true;
        imageUploadInput.disabled = true;
        processButton.classList.add('button-disabled');

        if (userInput) {
            displayMessage(`<span style="color:#25733f">**You:** ${userInput}</span>`, "user");
            ipcRenderer.send('process-description', userInput);
            document.getElementById('description-entry').value = ''; // Clear input field
        }

        if (imageURL) {
            displayMessage(`<span style="color:#25733f">**You sent an image** ${imageURL}</span>`, "user");
            ipcRenderer.send('process-image', imageURL);
            imageUploadInput.value = ''; // Clear the file input
        }
    });

    ipcRenderer.on('display-conversation', (event, text, sender, imageUrl) => {
        displayMessage(text, sender);
        // Re-enable the input and button
        descriptionEntry.disabled = false;
        processButton.disabled = false;
        imageUploadInput.disabled = false;
        processButton.classList.remove('button-disabled');

        // Display or update generated image in the sidebar
        if (imageUrl) {
            if (generatedImageElement) {
                sidebar.removeChild(generatedImageElement);
            } 
            generatedImageElement = document.createElement('img');
            generatedImageElement.src = `${imageUrl}?_=${new Date().getTime()}`;
            sidebar.appendChild(generatedImageElement);
            
        }
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
