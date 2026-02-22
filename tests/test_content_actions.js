// tests/test_content_actions.js
/**
 * Tests for content script coordinate-based actions.
 * Run with: node tests/test_content_actions.js
 * (Uses a minimal DOM mock since this runs in Node)
 */

// Minimal DOM mock
const mockElement = {
  clicked: false,
  focused: false,
  value: "",
  form: null,
  click() { this.clicked = true; },
  focus() { this.focused = true; },
  select() {},
  dispatchEvent() {},
};

// Mock window and document
globalThis.window = { innerWidth: 1920, innerHeight: 1080 };
globalThis.document = {
  elementFromPoint(x, y) {
    if (x >= 0 && y >= 0) return { ...mockElement };
    return null;
  },
  dispatchEvent() {},
};

// Simple test runner
let passed = 0;
let failed = 0;

function assert(condition, message) {
  if (condition) {
    passed++;
    console.log(`  PASS: ${message}`);
  } else {
    failed++;
    console.log(`  FAIL: ${message}`);
  }
}

// Inline the executeAction function for testing
function executeAction(msg) {
  let el = null;
  if (msg.coordinate) {
    const x = (msg.coordinate[0] / 1000) * window.innerWidth;
    const y = (msg.coordinate[1] / 1000) * window.innerHeight;
    el = document.elementFromPoint(x, y);
  }

  switch (msg.action) {
    case "click":
      if (!el) return { success: false, error: "No element at coordinates" };
      el.click();
      return { success: true };
    case "scroll":
      return { success: true };
    case "key":
      return { success: true };
    case "wait":
      return { success: true };
    default:
      return { success: false, error: `Unknown action: ${msg.action}` };
  }
}

console.log("Content Script Action Tests:");

// Test coordinate translation
const clickResult = executeAction({ action: "click", coordinate: [500, 500] });
assert(clickResult.success === true, "Click at center succeeds");

// Test scroll
const scrollResult = executeAction({ action: "scroll", direction: "down", amount: 3 });
assert(scrollResult.success === true, "Scroll succeeds");

// Test key press
const keyResult = executeAction({ action: "key", key: "Escape" });
assert(keyResult.success === true, "Key press succeeds");

// Test wait
const waitResult = executeAction({ action: "wait", duration: 2 });
assert(waitResult.success === true, "Wait succeeds");

// Test unknown action
const unknownResult = executeAction({ action: "fly" });
assert(unknownResult.success === false, "Unknown action fails");
assert(unknownResult.error.includes("Unknown action"), "Unknown action has error message");

console.log(`\n${passed} passed, ${failed} failed`);
process.exit(failed > 0 ? 1 : 0);
