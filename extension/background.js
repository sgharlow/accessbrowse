// extension/background.js — Service Worker
// Manages WebSocket connection to backend, screenshot relay, and action dispatch.
// Key change from AccessVoice: native WebSocket instead of Socket.IO.

const BACKEND_URL_KEY = "backend_url";
const DEFAULT_BACKEND_URL = "ws://localhost:8080/ws";

let ws = null;
let reconnectAttempts = 0;
const MAX_RECONNECT = 10;

// --- Offscreen Document Management ---

async function ensureOffscreen() {
  try {
    const existing = await chrome.offscreen.hasDocument();
    if (!existing) {
      await chrome.offscreen.createDocument({
        url: "offscreen.html",
        reasons: ["AUDIO_PLAYBACK", "USER_MEDIA"],
        justification: "Microphone capture and audio playback for voice assistant",
      });
    }
  } catch (err) {
    console.error("[AB] ensureOffscreen error:", err);
  }
}

// --- WebSocket Connection ---

async function getBackendUrl() {
  const result = await chrome.storage.local.get(BACKEND_URL_KEY);
  return result[BACKEND_URL_KEY] || DEFAULT_BACKEND_URL;
}

async function connect() {
  if (ws && ws.readyState === WebSocket.OPEN) return;

  const url = await getBackendUrl();
  ws = new WebSocket(url);

  ws.onopen = () => {
    reconnectAttempts = 0;
    broadcastToSidepanel({ type: "connection_status", connected: true });
    console.log("[AB] WebSocket connected");
  };

  ws.onmessage = (event) => {
    let msg;
    try {
      msg = JSON.parse(event.data);
    } catch {
      return;
    }

    switch (msg.type) {
      case "audio":
        chrome.runtime.sendMessage({ type: "play_audio", data: msg.data });
        break;
      case "transcript":
        broadcastToSidepanel({ type: "transcript", data: msg });
        break;
      case "status":
        broadcastToSidepanel({ type: "status", data: msg });
        break;
      case "session_started":
        broadcastToSidepanel({ type: "session_started", data: msg });
        break;
      case "session_stopped":
        broadcastToSidepanel({ type: "session_stopped", data: {} });
        break;
      case "error":
        broadcastToSidepanel({ type: "error", data: msg });
        break;
      case "request_screenshot":
        handleScreenshotRequest();
        break;
      case "execute_action":
        handleActionRequest(msg);
        break;
    }
  };

  ws.onclose = () => {
    broadcastToSidepanel({ type: "connection_status", connected: false });
    if (reconnectAttempts < MAX_RECONNECT) {
      const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
      setTimeout(connect, delay);
      reconnectAttempts++;
    }
  };

  ws.onerror = (err) => {
    console.error("[AB] WebSocket error:", err);
  };
}

function wsSend(msg) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(msg));
  }
}

// --- Screenshot Handling ---

async function handleScreenshotRequest() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) {
      wsSend({ type: "page_screenshot", image: null, url: "", title: "", error: "No active tab" });
      return;
    }
    const dataUrl = await chrome.tabs.captureVisibleTab(null, { format: "jpeg", quality: 60 });
    const base64 = dataUrl.split(",")[1];
    wsSend({
      type: "page_screenshot",
      image: base64,
      url: tab.url,
      title: tab.title,
    });
  } catch (err) {
    wsSend({ type: "page_screenshot", image: null, url: "", title: "", error: err.message });
  }
}

// --- Action Dispatch ---

async function handleActionRequest(msg) {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) {
      wsSend({ type: "action_result", success: false, error: "No active tab" });
      return;
    }

    if (msg.action === "navigate") {
      await chrome.tabs.update(tab.id, { url: msg.url });
      await waitForPageLoad(tab.id);
      wsSend({ type: "action_result", success: true });
    } else if (msg.action === "go_back") {
      await chrome.tabs.goBack(tab.id);
      await waitForPageLoad(tab.id);
      wsSend({ type: "action_result", success: true });
    } else if (msg.action === "go_forward") {
      await chrome.tabs.goForward(tab.id);
      await waitForPageLoad(tab.id);
      wsSend({ type: "action_result", success: true });
    } else {
      // DOM actions: click, type, scroll, hover, key, drag, select, wait
      const response = await chrome.tabs.sendMessage(tab.id, {
        type: "execute_action",
        action: msg.action,
        ...msg,
      });
      wsSend({ type: "action_result", ...(response || { success: false, error: "No response" }) });
    }
  } catch (err) {
    wsSend({ type: "action_result", success: false, error: err.message });
  }
}

function waitForPageLoad(tabId, timeout = 15000) {
  return new Promise((resolve) => {
    const listener = (tid, changeInfo) => {
      if (tid === tabId && changeInfo.status === "complete") {
        chrome.tabs.onUpdated.removeListener(listener);
        resolve();
      }
    };
    chrome.tabs.onUpdated.addListener(listener);
    setTimeout(() => {
      chrome.tabs.onUpdated.removeListener(listener);
      resolve();
    }, timeout);
  });
}

// --- Sidepanel Communication ---

function broadcastToSidepanel(message) {
  chrome.runtime.sendMessage(message).catch(() => {});
}

// --- Message Listener ---

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "connect") {
    ensureOffscreen().then(() => connect()).catch(console.error);
    sendResponse({ ok: true });
  } else if (message.type === "start_session") {
    wsSend({ type: "start_session" });
  } else if (message.type === "stop_session") {
    wsSend({ type: "stop_session" });
  } else if (message.type === "text_input") {
    wsSend({ type: "text_input", text: message.text });
  } else if (message.type === "audio_chunk") {
    wsSend({ type: "audio_chunk", data: message.data });
  } else if (message.type === "set_backend_url") {
    chrome.storage.local.set({ [BACKEND_URL_KEY]: message.url });
    sendResponse({ ok: true });
  }
  return true;
});

// --- Lifecycle ---

chrome.action.onClicked.addListener((tab) => {
  chrome.sidePanel.open({ windowId: tab.windowId });
});

chrome.runtime.onInstalled.addListener(() => {
  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true });
  chrome.alarms.create("keepalive", { periodInMinutes: 1 });
});

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "keepalive" && ws?.readyState === WebSocket.OPEN) {
    // Ping keeps service worker alive
  }
});
