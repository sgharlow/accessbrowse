// tests/e2e/test_concurrent_sessions.js
const { TestClient } = require("./ws_test_client");

async function testConcurrentSessions() {
  console.log("Test: Concurrent Sessions");

  const clients = [];
  try {
    // Create 3 sessions (max allowed)
    for (let i = 0; i < 3; i++) {
      const client = new TestClient();
      await client.connect();
      client.send({ type: "start_session" });
      await client.waitFor("session_started", 30000);
      clients.push(client);
      console.log(`  Session ${i + 1} started`);
    }

    // 4th should fail
    const overflow = new TestClient();
    await overflow.connect();
    overflow.send({ type: "start_session" });
    const error = await overflow.waitFor("error", 10000);
    console.log(`  4th session rejected: ${error.message}`);
    overflow.close();

    console.log("  PASS: Concurrent session limit enforced");
  } catch (err) {
    console.error(`  FAIL: ${err.message}`);
    process.exit(1);
  } finally {
    clients.forEach((c) => c.close());
  }
}

testConcurrentSessions();
