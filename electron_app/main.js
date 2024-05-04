// main.js

const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
            preload: path.join(__dirname, 'preload.js')
        }
    });
    mainWindow.webContents.openDevTools();

    mainWindow.loadFile('index.html');

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

app.on('ready', createWindow);

ipcMain.on('process-description', (event, userInput) => {
    // Execute Python code
    const pythonProcess = spawn('python', ['../python_script.py', userInput]);

    // Handle stdout data
    pythonProcess.stdout.on('data', (data) => {
        const result = data.toString();
        mainWindow.webContents.send('display-conversation', result, 'system');
    });
    console.log("hola")

    // Handle errors
    pythonProcess.on('error', (error) => {
        console.error('Error executing Python script:', error);
    });
});

ipcMain.on('process-image', (event, imageURL) => {
    console.log(imageURL)
    // Execute Python code
    const pythonProcess = spawn('python', ['../python_image_script.py', imageURL]);

    // Handle stdout data
    pythonProcess.stdout.on('data', (data) => {
        const result = data.toString();
        mainWindow.webContents.send('display-conversation', result, 'system');
    });

    // Handle errors
    pythonProcess.on('error', (error) => {
        console.error('Error executing Python script:', error);
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (mainWindow === null) {
        createWindow();
    }
});
