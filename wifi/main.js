const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const wifi = require('node-wifi');

// Инициализация Wi-Fi на Windows
wifi.init({ iface: null });

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1600,
    height: 900,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: false
    },
    titleBarStyle: 'hiddenInset',
    backgroundColor: '#1a1a2e'
  });

  mainWindow.loadFile('index.html');
  // mainWindow.webContents.openDevTools(); // Раскомментируйте для отладки
}

// Обработчик сканирования Wi-Fi
ipcMain.handle('scan-wifi', async () => {
  try {
    const networks = await wifi.scan();
    return networks.map(n => ({
      ssid: n.ssid || 'Скрытая сеть',
      mac: n.mac,
      signal: n.signal_level,
      frequency: n.frequency,
      channel: n.channel
    }));
  } catch (error) {
    console.error('Ошибка сканирования:', error);
    return { error: error.message };
  }
});

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
