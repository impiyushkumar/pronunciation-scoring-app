"use client";

import { useAnalysis } from "../hooks/useAnalysis";
import UploadZone from "../components/UploadZone";
import ConsentCheckbox from "../components/ConsentCheckbox";
import LoadingOverlay from "../components/LoadingOverlay";
import ErrorBanner from "../components/ErrorBanner";
import ResultsPanel from "../components/ResultsPanel";

export default function Home() {
  const {
    state,
    selectedFile,
    consent,
    setConsent,
    selectFile,
    analyze,
    reset,
    dismissError,
    canAnalyze,
    isProcessing,
  } = useAnalysis();

  return (
    <div className="app-container">
      {/* ---- Header ---- */}
      <header className="app-header">
        <div className="app-logo" aria-hidden="true">
          🎯
        </div>
        <h1 className="app-title">PronounceAI</h1>
        <p className="app-subtitle">
          Upload your English speech and get instant AI-powered pronunciation
          scoring with word-by-word feedback.
        </p>
      </header>

      {/* ---- Main Content ---- */}
      <main>
        {state.phase === "done" ? (
          /* ---- Results View ---- */
          <ResultsPanel result={state.result} onRetry={reset} />
        ) : isProcessing ? (
          /* ---- Loading View ---- */
          <div className="glass-card">
            <LoadingOverlay
              phase={
                state.phase as "validating" | "uploading" | "processing"
              }
            />
          </div>
        ) : (
          /* ---- Upload View ---- */
          <div className="glass-card">
            <UploadZone
              onFileSelect={selectFile}
              selectedFile={selectedFile}
              disabled={isProcessing}
            />

            {/* Error Banner */}
            {state.phase === "error" && (
              <ErrorBanner
                message={state.message}
                onDismiss={dismissError}
              />
            )}

            {/* Consent */}
            <ConsentCheckbox
              checked={consent}
              onChange={setConsent}
              disabled={isProcessing}
            />

            {/* Analyze Button */}
            <div className="analyze-section">
              <button
                className="analyze-btn"
                onClick={analyze}
                disabled={!canAnalyze}
                id="analyze-btn"
              >
                {isProcessing ? "Analyzing..." : "🔍 Analyze Pronunciation"}
              </button>
            </div>
          </div>
        )}
      </main>

      {/* ---- Footer ---- */}
      <footer className="app-footer">
        <p>
          Built with Whisper + Gemini Flash · No audio stored ·{" "}
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
          >
            Architecture Doc
          </a>
        </p>
      </footer>
    </div>
  );
}
