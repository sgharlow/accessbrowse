// extension/sidepanel/src/components/BrowserView.tsx
interface BrowserViewProps {
  screenshot: string | null;
}

export default function BrowserView({ screenshot }: BrowserViewProps) {
  return (
    <div className="browser-view" role="img" aria-label={screenshot ? "Current webpage" : "No page loaded"}>
      {screenshot ? (
        <img src={`data:image/jpeg;base64,${screenshot}`} alt="Current webpage" className="browser-screenshot" />
      ) : (
        <div className="browser-placeholder">
          <p>Start a session and ask me to browse a website</p>
          <p className="placeholder-hint">Try: "Search for apartments in Seattle on Zillow"</p>
        </div>
      )}
    </div>
  );
}
