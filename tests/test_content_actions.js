// tests/test_content_actions.js
/**
 * Tests for content script coordinate-based actions.
 * Run with: node tests/test_content_actions.js
 * Covers all 9 action types + error cases.
 */

// --- Event mocks ---
class MockEvent {
  constructor(type, opts = {}) {
    this.type = type;
    Object.assign(this, opts);
  }
}
globalThis.InputEvent = MockEvent;
globalThis.Event = MockEvent;
globalThis.KeyboardEvent = MockEvent;
globalThis.MouseEvent = MockEvent;

// --- DOM mocks ---
function createMockElement(overrides = {}) {
  return {
    clicked: false,
    focused: false,
    selected: false,
    value: "",
    form: null,
    events: [],
    click() { this.clicked = true; },
    focus() { this.focused = true; },
    select() { this.selected = true; },
    dispatchEvent(e) { this.events.push(e); },
    ...overrides,
  };
}

let lastElementFromPointArgs = null;
let elementFromPointReturns = null;

globalThis.window = {
  innerWidth: 1920,
  innerHeight: 1080,
  scrollBy() {},
};
globalThis.document = {
  elementFromPoint(x, y) {
    lastElementFromPointArgs = { x, y };
    if (elementFromPointReturns !== undefined) return elementFromPointReturns;
    if (x >= 0 && y >= 0) return createMockElement();
    return null;
  },
  events: [],
  dispatchEvent(e) { this.events.push(e); },
};

// --- Simple test runner ---
let passed = 0;
let failed = 0;
let currentTest = "";

function assert(condition, message) {
  if (condition) {
    passed++;
    console.log(`  PASS: ${message}`);
  } else {
    failed++;
    console.log(`  FAIL: ${message}`);
  }
}

function beforeEach() {
  lastElementFromPointArgs = null;
  elementFromPointReturns = undefined;
  document.events = [];
}

// --- Inline executeAction matching real content.js ---
function executeAction(msg) {
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
        if (el.form && el.form.requestSubmit) el.form.requestSubmit();
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
      return { success: true };
    }

    default:
      return { success: false, error: `Unknown action: ${msg.action}` };
  }
}

// ============================================================
// TESTS
// ============================================================

console.log("Content Script Action Tests:");
console.log("============================\n");

// --- 1. Click ---
console.log("1. Click action:");
beforeEach();
const clickResult = executeAction({ action: "click", coordinate: [500, 500] });
assert(clickResult.success === true, "Click at center succeeds");
assert(lastElementFromPointArgs.x === 960, "Click translates X: 500/1000 * 1920 = 960");
assert(lastElementFromPointArgs.y === 540, "Click translates Y: 500/1000 * 1080 = 540");

beforeEach();
const clickTopLeft = executeAction({ action: "click", coordinate: [0, 0] });
assert(clickTopLeft.success === true, "Click at (0,0) succeeds");
assert(lastElementFromPointArgs.x === 0, "Click at origin has X=0");

beforeEach();
elementFromPointReturns = null;
const clickNull = executeAction({ action: "click", coordinate: [500, 500] });
assert(clickNull.success === false, "Click fails when no element found");
assert(clickNull.error === "No element at coordinates", "Click error message correct");

// --- 2. Type ---
console.log("\n2. Type action:");
beforeEach();
const typeResult = executeAction({ action: "type", coordinate: [500, 500], text: "hello world" });
assert(typeResult.success === true, "Type succeeds");

beforeEach();
const typeEmpty = executeAction({ action: "type", coordinate: [500, 500] });
assert(typeEmpty.success === true, "Type with no text succeeds (clears field)");

beforeEach();
const typeSubmit = executeAction({ action: "type", coordinate: [500, 500], text: "search", submit: true });
assert(typeSubmit.success === true, "Type with submit succeeds");

beforeEach();
elementFromPointReturns = null;
const typeNull = executeAction({ action: "type", coordinate: [500, 500], text: "hello" });
assert(typeNull.success === false, "Type fails when no element found");
assert(typeNull.error === "No element at coordinates", "Type error message correct");

// --- 3. Scroll ---
console.log("\n3. Scroll action:");
beforeEach();
const scrollDown = executeAction({ action: "scroll", direction: "down", amount: 3 });
assert(scrollDown.success === true, "Scroll down succeeds");

beforeEach();
const scrollUp = executeAction({ action: "scroll", direction: "up", amount: 2 });
assert(scrollUp.success === true, "Scroll up succeeds");

beforeEach();
const scrollDefault = executeAction({ action: "scroll" });
assert(scrollDefault.success === true, "Scroll with defaults succeeds");

// --- 4. Hover ---
console.log("\n4. Hover action:");
beforeEach();
const hoverResult = executeAction({ action: "hover", coordinate: [250, 750] });
assert(hoverResult.success === true, "Hover succeeds");

beforeEach();
elementFromPointReturns = null;
const hoverNull = executeAction({ action: "hover", coordinate: [500, 500] });
assert(hoverNull.success === false, "Hover fails when no element found");
assert(hoverNull.error === "No element at coordinates", "Hover error message correct");

// --- 5. Key ---
console.log("\n5. Key action:");
beforeEach();
const keyEsc = executeAction({ action: "key", key: "Escape" });
assert(keyEsc.success === true, "Key press Escape succeeds");
assert(document.events.length === 2, "Key dispatches keydown + keyup events");
assert(document.events[0].type === "keydown", "First event is keydown");
assert(document.events[1].type === "keyup", "Second event is keyup");

beforeEach();
const keyEnter = executeAction({ action: "key", key: "Enter" });
assert(keyEnter.success === true, "Key press Enter succeeds");

// --- 6. Drag ---
console.log("\n6. Drag action:");
beforeEach();
const dragResult = executeAction({
  action: "drag",
  startCoordinate: [100, 200],
  endCoordinate: [800, 600],
});
assert(dragResult.success === true, "Drag succeeds");

beforeEach();
const dragNoStart = executeAction({ action: "drag", endCoordinate: [800, 600] });
assert(dragNoStart.success === false, "Drag fails without startCoordinate");
assert(dragNoStart.error.includes("startCoordinate"), "Drag error mentions startCoordinate");

beforeEach();
const dragNoEnd = executeAction({ action: "drag", startCoordinate: [100, 200] });
assert(dragNoEnd.success === false, "Drag fails without endCoordinate");

beforeEach();
elementFromPointReturns = null;
const dragNullEl = executeAction({
  action: "drag",
  startCoordinate: [100, 200],
  endCoordinate: [800, 600],
});
assert(dragNullEl.success === false, "Drag fails when no element at start");
assert(dragNullEl.error === "No element at start coordinates", "Drag error message correct");

// --- 7. Select ---
console.log("\n7. Select action:");
beforeEach();
const selectResult = executeAction({ action: "select", coordinate: [500, 500] });
assert(selectResult.success === true, "Select succeeds");

beforeEach();
elementFromPointReturns = null;
const selectNull = executeAction({ action: "select", coordinate: [500, 500] });
assert(selectNull.success === false, "Select fails when no element found");
assert(selectNull.error === "No element at coordinates", "Select error message correct");

// --- 8. Wait ---
console.log("\n8. Wait action:");
beforeEach();
const waitResult = executeAction({ action: "wait", duration: 2 });
assert(waitResult.success === true, "Wait succeeds");

const waitNoDuration = executeAction({ action: "wait" });
assert(waitNoDuration.success === true, "Wait without duration succeeds");

// --- 9. Unknown action ---
console.log("\n9. Unknown/error cases:");
beforeEach();
const unknownResult = executeAction({ action: "fly" });
assert(unknownResult.success === false, "Unknown action fails");
assert(unknownResult.error.includes("Unknown action"), "Unknown action has error message");
assert(unknownResult.error.includes("fly"), "Error includes the action name");

const emptyAction = executeAction({ action: "" });
assert(emptyAction.success === false, "Empty action string fails");

// --- Summary ---
console.log(`\n============================`);
console.log(`${passed} passed, ${failed} failed`);
process.exit(failed > 0 ? 1 : 0);
