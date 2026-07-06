"use client";

import { useEffect, useState } from "react";

interface LoadingOverlayProps {
  phase: "validating" | "uploading" | "processing";
}

const PHASE_MESSAGES: Record<string, { title: string; detail: string }> = {
  validating: {
    title: "Validating audio...",
    detail: "Checking format and duration",
  },
  uploading: {
    title: "Uploading audio...",
    detail: "Sending to the analysis server",
  },
  processing: {
    title: "Analyzing pronunciation...",
    detail: "Transcribing speech and scoring pronunciation",
  },
};

const COLD_START_THRESHOLD_MS = 10_000;

export default function LoadingOverlay({ phase }: LoadingOverlayProps) {
  const [showColdStart, setShowColdStart] = useState(false);
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const start = Date.now();
    const interval = setInterval(() => {
      const ms = Date.now() - start;
      setElapsed(ms);
      if (ms > COLD_START_THRESHOLD_MS) {
        setShowColdStart(true);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [phase]);

  const { title, detail } = PHASE_MESSAGES[phase] ?? PHASE_MESSAGES.processing;

  return (
    <div className="loading-overlay" role="status" aria-live="polite">
      <div className="loading-spinner" />
      <div className="loading-phase">{title}</div>
      <div className="loading-detail">{detail}</div>
      {elapsed > 0 && phase === "processing" && (
        <div className="loading-detail" style={{ marginTop: "0.5rem" }}>
          {Math.floor(elapsed / 1000)}s elapsed
        </div>
      )}
      {showColdStart && phase === "processing" && (
        <div className="loading-cold-start">
          ⏳ Server is warming up — this may take up to 60 seconds on first use.
        </div>
      )}
    </div>
  );
}
