// extension/sidepanel/src/components/StatusBar.tsx
interface StatusBarProps {
  status: string;
  isConnected: boolean;
  isRecording: boolean;
}

export default function StatusBar({ status, isConnected, isRecording }: StatusBarProps) {
  const dotClass = isRecording ? "dot recording" : isConnected ? "dot connected" : "dot disconnected";

  return (
    <div className="status-bar" role="status" aria-live="polite">
      <span className={dotClass} aria-hidden="true" />
      <span className="status-text">{status}</span>
    </div>
  );
}
