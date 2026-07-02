/**
 * Lil Arrow Pip — Browser Extension Background Script
 * Tracks tabs and sends context to the desktop droid via WebSocket.
 */

const WS_URL = 'ws://127.0.0.1:8766';
let ws = null;
let reconnectTimer = null;
let currentTab = null;

function connect() {
  if (ws && (ws.readyState === WebSocket.CONNECTING || ws.readyState === WebSocket.OPEN)) {
    return;
  }
  console.log('[Pip Bridge] Connecting to desktop droid...');
  ws = new WebSocket(WS_URL);

  ws.onopen = () => {
    console.log('[Pip Bridge] Connected to Lil Pip!');
    sendCurrentTab();
  };

  ws.onclose = () => {
    console.log('[Pip Bridge] Disconnected. Retrying in 5s...');
    scheduleReconnect();
  };

  ws.onerror = (err) => {
    console.error('[Pip Bridge] WebSocket error:', err);
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      console.log('[Pip Bridge] From droid:', data);
    } catch (e) {
      console.log('[Pip Bridge] Raw message:', event.data);
    }
  };
}

function scheduleReconnect() {
  if (reconnectTimer) clearTimeout(reconnectTimer);
  reconnectTimer = setTimeout(connect, 5000);
}

function sendMessage(data) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(data));
  }
}

function sendCurrentTab() {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs.length > 0) {
      const tab = tabs[0];
      currentTab = tab;
      sendMessage({
        type: 'tab_change',
        url: tab.url || '',
        title: tab.title || '',
        timestamp: new Date().toISOString()
      });
    }
  });
}

chrome.tabs.onActivated.addListener((activeInfo) => {
  chrome.tabs.get(activeInfo.tabId, (tab) => {
    if (chrome.runtime.lastError) return;
    currentTab = tab;
    sendMessage({
      type: 'tab_active',
      url: tab.url || '',
      title: tab.title || '',
      timestamp: new Date().toISOString()
    });
  });
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.url || changeInfo.title) {
    currentTab = tab;
    sendMessage({
      type: 'tab_change',
      url: tab.url || '',
      title: tab.title || '',
      timestamp: new Date().toISOString()
    });
  }
});

chrome.tabs.onCreated.addListener((tab) => {
  sendMessage({
    type: 'tab_change',
    url: tab.url || '',
    title: tab.title || 'New Tab',
    timestamp: new Date().toISOString()
  });
});

chrome.downloads.onCreated.addListener((downloadItem) => {
  sendMessage({
    type: 'download_started',
    filename: downloadItem.filename || 'unknown',
    url: downloadItem.url || '',
    fileSize: downloadItem.fileSize || 0,
    timestamp: new Date().toISOString()
  });
});

setInterval(() => {
  sendMessage({ type: 'ping' });
}, 30000);

connect();
console.log('[Pip Bridge] Lil Arrow Pip browser bridge loaded');
