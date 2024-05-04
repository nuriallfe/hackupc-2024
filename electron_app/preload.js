// preload.js

const { ipcRenderer } = require('electron');

// Expose ipcRenderer to the window object
window.ipcRenderer = ipcRenderer;
