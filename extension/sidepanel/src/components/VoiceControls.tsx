// extension/sidepanel/src/components/VoiceControls.tsx
interface VoiceControlsProps {
  isSessionActive: boolean;
  isRecording: boolean;
  isConnected: boolean;
  onToggleSession: () => void;
  onToggleRecording: () => void;
}

export default function VoiceControls({
  isSessionActive, isRecording, isConnected, onToggleSession, onToggleRecording,
}: VoiceControlsProps) {
  return (
    <div className="voice-controls" role="toolbar" aria-label="Voice controls">
      <button
        className={`btn ${isSessionActive ? "btn-stop" : "btn-start"}`}
        onClick={onToggleSession}
        disabled={!isConnected}
        aria-label={isSessionActive ? "End session" : "Start session"}
      >
        {isSessionActive ? "End Session" : "Start Session"}
      </button>

      {isSessionActive && (
        <button
          className={`btn btn-mic ${isRecording ? "btn-mic-active" : ""}`}
          onClick={onToggleRecording}
          aria-label={isRecording ? "Mute microphone" : "Unmute microphone"}
          aria-pressed={isRecording}
        >
          {isRecording ? "Mute" : "Speak"}
        </button>
      )}
    </div>
  );
}
