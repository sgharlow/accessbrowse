const WebSocket = require("ws");

class TestClient {
  constructor(url = "ws://localhost:8080/ws") {
    this.url = url;
    this.ws = null;
    this.messages = [];
    this._handlers = {};
  }

  async connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.url);
      this.ws.on("open", () => resolve());
      this.ws.on("error", reject);
      this.ws.on("message", (data) => {
        const msg = JSON.parse(data);
        this.messages.push(msg);
        const handler = this._handlers[msg.type];
        if (handler) handler(msg);
      });
    });
  }

  send(msg) { this.ws.send(JSON.stringify(msg)); }

  waitFor(type, timeout = 30000) {
    const existing = this.messages.find((m) => m.type === type);
    if (existing) return Promise.resolve(existing);
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        delete this._handlers[type];
        reject(new Error(`Timeout waiting for "${type}" after ${timeout}ms`));
      }, timeout);
      this._handlers[type] = (msg) => {
        clearTimeout(timer);
        delete this._handlers[type];
        resolve(msg);
      };
    });
  }

  close() { if (this.ws) this.ws.close(); }
}

module.exports = { TestClient };
