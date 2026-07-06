import { contextBridge, ipcRenderer } from 'electron'

const desktopWindowApi = {
  minimize: () => ipcRenderer.send('window:minimize'),
  maximize: () => ipcRenderer.send('window:maximize'),
  close: () => ipcRenderer.send('window:close'),
}

contextBridge.exposeInMainWorld('desktopWindow', desktopWindowApi)
