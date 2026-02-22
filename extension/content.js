// extension/content.js — Coordinate-based DOM action execution
// Key improvement over AccessVoice: uses document.elementFromPoint(x, y) instead
// of CSS selector matching. Gemini Computer Use returns coordinates on a 1000x1000
// normalized grid; we translate to viewport pixels.

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type !== "execute_action") return;

  try {
    const result = executeAction(message);
    sendResponse(result);
  } catch (e) {
    sendResponse({ success: false, error: e.message });
  }
  return true; // Keep message channel open for async response
});

function executeAction(msg) {
  // Translate 1000x1000 normalized coordinates to viewport pixels
  let el = null;
  if (msg.coordinate) {
    const x = (msg.coordinate[0] / 1000) * window.innerWidth;
    const y = (msg.coordinate[1] / 1000) * window.innerHeight;
    el = document.elementFromPoint(x, y);
  }

  switch (msg.action) {
    case "click": {
      if (!el) return { success: false, error: "No element at coordinates" };
      el.click();
      return { success: true };
    }

    case "type": {
      if (!el) return { success: false, error: "No element at coordinates" };
      el.focus();
      el.value = "";
      el.value = msg.text || "";
      el.dispatchEvent(new InputEvent("input", { bubbles: true, data: msg.text }));
      el.dispatchEvent(new Event("change", { bubbles: true }));
      if (msg.submit) {
        el.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", code: "Enter", bubbles: true }));
        el.form?.requestSubmit();
      }
      return { success: true };
    }

    case "scroll": {
      const scrollAmount = (msg.amount || 3) * 200;
      const direction = msg.direction === "up" ? -1 : 1;
      window.scrollBy({ top: scrollAmount * direction, behavior: "smooth" });
      return { success: true };
    }

    case "hover": {
      if (!el) return { success: false, error: "No element at coordinates" };
      el.dispatchEvent(new MouseEvent("mouseover", { bubbles: true }));
      el.dispatchEvent(new MouseEvent("mouseenter", { bubbles: true }));
      return { success: true };
    }

    case "key": {
      document.dispatchEvent(new KeyboardEvent("keydown", { key: msg.key, bubbles: true }));
      document.dispatchEvent(new KeyboardEvent("keyup", { key: msg.key, bubbles: true }));
      return { success: true };
    }

    case "drag": {
      if (!msg.startCoordinate || !msg.endCoordinate) {
        return { success: false, error: "Drag requires startCoordinate and endCoordinate" };
      }
      const sx = (msg.startCoordinate[0] / 1000) * window.innerWidth;
      const sy = (msg.startCoordinate[1] / 1000) * window.innerHeight;
      const ex = (msg.endCoordinate[0] / 1000) * window.innerWidth;
      const ey = (msg.endCoordinate[1] / 1000) * window.innerHeight;
      const startEl = document.elementFromPoint(sx, sy);
      if (!startEl) return { success: false, error: "No element at start coordinates" };
      startEl.dispatchEvent(new MouseEvent("mousedown", { clientX: sx, clientY: sy, bubbles: true }));
      startEl.dispatchEvent(new MouseEvent("mousemove", { clientX: ex, clientY: ey, bubbles: true }));
      startEl.dispatchEvent(new MouseEvent("mouseup", { clientX: ex, clientY: ey, bubbles: true }));
      return { success: true };
    }

    case "select": {
      if (!el) return { success: false, error: "No element at coordinates" };
      if (el.select) el.select();
      return { success: true };
    }

    case "wait": {
      // Backend handles the actual wait via asyncio.sleep
      return { success: true };
    }

    default:
      return { success: false, error: `Unknown action: ${msg.action}` };
  }
}
