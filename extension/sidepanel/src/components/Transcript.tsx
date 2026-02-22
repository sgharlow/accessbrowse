// extension/sidepanel/src/components/Transcript.tsx
import { useEffect, useRef } from "react";

export interface TranscriptEntry {
  text: string;
  role: "user" | "assistant" | "system";
  timestamp: number;
}

interface TranscriptProps {
  entries: TranscriptEntry[];
}

export default function Transcript({ entries }: TranscriptProps) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [entries]);

  return (
    <div className="transcript-panel" role="log" aria-label="Conversation" aria-live="polite">
      {entries.length === 0 ? (
        <p className="transcript-empty">Conversation will appear here...</p>
      ) : (
        entries.map((entry, i) => (
          <div key={i} className={`transcript-entry transcript-${entry.role}`}>
            <span className="transcript-role">
              {entry.role === "user" ? "You" : entry.role === "assistant" ? "AccessBrowse" : "System"}
            </span>
            <span className="transcript-text">{entry.text}</span>
          </div>
        ))
      )}
      <div ref={endRef} />
    </div>
  );
}
