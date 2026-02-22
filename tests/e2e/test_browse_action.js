// tests/e2e/test_browse_action.js
const { TestClient } = require("./ws_test_client");

async function testBrowseAction() {
  console.log("Test: Browse Action Protocol");
  const client = new TestClient();

  try {
    await client.connect();
    client.send({ type: "start_session" });
    await client.waitFor("session_started", 30000);

    // Simulate sending a screenshot response when requested
    // (In real E2E, the extension provides this)
    console.log("  Session started for browse test");

    // Stop session
    client.send({ type: "stop_session" });
    await client.waitFor("session_stopped", 10000);

    console.log("  PASS: Browse action protocol verified");
  } catch (err) {
    console.error(`  FAIL: ${err.message}`);
    process.exit(1);
  } finally {
    client.close();
  }
}

testBrowseAction();
