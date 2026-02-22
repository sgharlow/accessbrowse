// tests/e2e/test_session_lifecycle.js
const { TestClient } = require("./ws_test_client");

async function testSessionLifecycle() {
  console.log("Test: Session Lifecycle");
  const client = new TestClient();

  try {
    await client.connect();
    console.log("  Connected to backend");

    // Start session
    client.send({ type: "start_session" });
    const started = await client.waitFor("session_started", 30000);
    console.log(`  Session started: ${started.session_id}`);

    // Send text input
    client.send({ type: "text_input", text: "Hello, can you help me browse?" });

    // Wait for response (transcript or status)
    // In real test, we'd wait for transcript but Gemini needs GCP creds
    console.log("  Text input sent");

    // Stop session
    client.send({ type: "stop_session" });
    const stopped = await client.waitFor("session_stopped", 10000);
    console.log("  Session stopped");

    console.log("  PASS: Session lifecycle works");
  } catch (err) {
    console.error(`  FAIL: ${err.message}`);
    process.exit(1);
  } finally {
    client.close();
  }
}

testSessionLifecycle();
