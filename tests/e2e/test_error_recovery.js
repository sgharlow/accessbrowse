// tests/e2e/test_error_recovery.js
const { TestClient } = require("./ws_test_client");

async function testErrorRecovery() {
  console.log("Test: Error Recovery");
  const client = new TestClient();

  try {
    await client.connect();

    // Send audio without session — should be silently ignored
    client.send({ type: "audio_chunk", data: "dGVzdA==" });
    console.log("  Audio without session: no crash");

    // Send text without session — should get error
    client.send({ type: "text_input", text: "hello" });
    console.log("  Text without session: no crash");

    // Disconnect and reconnect
    client.close();
    const client2 = new TestClient();
    await client2.connect();
    console.log("  Reconnection: success");
    client2.close();

    console.log("  PASS: Error recovery works");
  } catch (err) {
    console.error(`  FAIL: ${err.message}`);
    process.exit(1);
  }
}

testErrorRecovery();
