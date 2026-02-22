// extension/sidepanel/src/App.tsx
import { useState, useCallback, useRef, useEffect } from "react";
import Transcript, { TranscriptEntry } from "./components/Transcript";
import VoiceControls from "./components/VoiceControls";
import StatusBar from "./components/StatusBar";
import BrowserView from "./components/BrowserView";

function App() {
  const [transcripts, setTranscripts] = useState<TranscriptEntry[]>([]);
  const [status, setStatus] = useState("Disconnected");
  const [screenshot, setScreenshot] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isSessionActive, setIsSessionActive] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const textInputRef = useRef<HTMLInputElement>(null);

  const addTranscript = useCallback((text: string, role: TranscriptEntry["role"]) => {
    setTranscripts((prev) => [...prev, { text, role, timestamp: Date.now() }]);
  }, []);

  // Listen for messages from background service worker
  useEffect(() => {
    const listener = (message: Record<string, unknown>) => {
      switch (message.type) {
        case "connection_status":
          setIsConnected(message.connected as boolean);
          setStatus((message.connected as boolean) ? "Connected" : "Disconnected");
          break;
        case "transcript": {
          const data = message.data as { text: string; role: string };
          addTranscript(data.text, data.role as TranscriptEntry["role"]);
          break;
        }
        case "status": {
          const data = message.data as { message: string };
          setStatus(data.message);
          break;
        }
        case "screenshot": {
          const data = message.data as { image: string };
          setScreenshot(data.image);
          break;
        }
        case "session_started":
          setIsSessionActive(true);
          setStatus("Listening...");
          break;
        case "session_stopped":
          setIsSessionActive(false);
          setIsRecording(false);
          setStatus("Session ended");
          break;
        case "error": {
          const data = message.data as { message: string };
          addTranscript(data.message, "system");
          break;
        }
      }
    };

    chrome.runtime.onMessage.addListener(listener);
    // Request connection on mount
    chrome.runtime.sendMessage({ type: "connect" });
    return () => chrome.runtime.onMessage.removeListener(listener);
  }, [addTranscript]);

  const handleToggleSession = useCallback(() => {
    if (isSessionActive) {
      if (isRecording) {
        chrome.runtime.sendMessage({ type: "stop_recording" });
        setIsRecording(false);
      }
      chrome.runtime.sendMessage({ type: "stop_session" });
    } else {
      chrome.runtime.sendMessage({ type: "start_session" });
    }
  }, [isSessionActive, isRecording]);

  const handleToggleRecording = useCallback(() => {
    if (isRecording) {
      chrome.runtime.sendMessage({ type: "stop_recording" });
      setIsRecording(false);
    } else {
      chrome.runtime.sendMessage({ type: "start_recording" });
      setIsRecording(true);
    }
  }, [isRecording]);

  const handleTextSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      const input = textInputRef.current;
      if (!input || !input.value.trim() || !isSessionActive) return;
      const text = input.value.trim();
      addTranscript(text, "user");
      chrome.runtime.sendMessage({ type: "text_input", text });
      input.value = "";
    },
    [isSessionActive, addTranscript]
  );

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.shiftKey && e.key === "S") {
        e.preventDefault();
        handleToggleSession();
      }
      if (e.ctrlKey && e.shiftKey && e.key === "M" && isSessionActive) {
        e.preventDefault();
        handleToggleRecording();
      }
      if (e.ctrlKey && e.shiftKey && e.key === "T" && isSessionActive) {
        e.preventDefault();
        textInputRef.current?.focus();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleToggleSession, handleToggleRecording, isSessionActive]);

  return (
    <div className="app-container">
      <header className="app-header" role="banner">
        <h1 className="app-title">AccessBrowse</h1>
        <p className="app-subtitle">Voice-driven web browsing powered by Gemini</p>
        <StatusBar status={status} isConnected={isConnected} isRecording={isRecording} />
      </header>

      <main className="app-main" role="main">
        <BrowserView screenshot={screenshot} />
        <Transcript entries={transcripts} />

        <form className="text-input-form" onSubmit={handleTextSubmit} role="search">
          <label htmlFor="text-input" className="sr-only">Type a command</label>
          <input
            ref={textInputRef}
            id="text-input"
            type="text"
            className="text-input"
            placeholder={isSessionActive ? "Type a command..." : "Start a session first"}
            disabled={!isSessionActive}
            autoComplete="off"
          />
          <button type="submit" className="btn btn-send" disabled={!isSessionActive}>
            Send
          </button>
        </form>
      </main>

      <footer className="app-footer" role="contentinfo">
        <VoiceControls
          isSessionActive={isSessionActive}
          isRecording={isRecording}
          isConnected={isConnected}
          onToggleSession={handleToggleSession}
          onToggleRecording={handleToggleRecording}
        />
        <div className="keyboard-hints" aria-hidden="true">
          <kbd>Ctrl+Shift+S</kbd> Session &middot;
          <kbd>Ctrl+Shift+M</kbd> Mic &middot;
          <kbd>Ctrl+Shift+T</kbd> Text
        </div>
      </footer>
    </div>
  );
}

export default App;
