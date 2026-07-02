/**
 * Lil Arrow Pip — Browser Extension Popup Script
 */

const WS_URL = 'ws://127.0.0.1:8766';

function updateStatus() {
  const ws = new WebSocket(WS_URL);
  const dot = document.getElementById('statusDot');
  const text = document.getElementById('statusText');

  ws.onopen = () => {
    dot.className = 'status-dot connected';
    text.textContent = 'Connected to desktop droid';
    ws.close();
  };

  ws.onerror = () => {
    dot.className = 'status-dot disconnected';
    text.textContent = 'Droid not running — start Lil Pip';
  };
}

function loadCurrentTab() {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs.length > 0) {
      document.getElementById('tabTitle').textContent = tabs[0].title || 'Untitled';
      document.getElementById('tabUrl').textContent = tabs[0].url || '';
    }
  });
}

document.getElementById('btnSendContext').addEventListener('click', () => {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs.length > 0) {
      const ws = new WebSocket(WS_URL);
      ws.onopen = () => {
        ws.send(JSON.stringify({
          type: 'tab_change',
          url: tabs[0].url || '',
          title: tabs[0].title || '',
          timestamp: new Date().toISOString()
        }));
        document.getElementById('statusText').textContent = 'Context sent!';
        ws.close();
      };
      ws.onerror = () => {
        document.getElementById('statusText').textContent = 'Failed — is Pip running?';
      };
    }
  });
});

document.getElementById('btnOpenHome').addEventListener('click', () => {
  chrome.tabs.create({ url: 'file://~/LilPipHome' });
});

updateStatus();
loadCurrentTab();
