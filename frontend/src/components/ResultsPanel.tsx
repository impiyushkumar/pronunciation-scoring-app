"use client";

import { AnalysisResponse } from "../lib/types";
import ScoreGauge from "./ScoreGauge";
import TranscriptViewer from "./TranscriptViewer";
import FeedbackCard from "./FeedbackCard";

interface ResultsPanelProps {
  result: AnalysisResponse;
  onRetry: () => void;
}

export default function ResultsPanel({ result, onRetry }: ResultsPanelProps) {
  return (
    <div className="results-panel glass-card" id="results-panel">
      <div className="results-header">
        <h2 className="results-title">Your Results</h2>
        <button
          className="results-retry-btn"
          onClick={onRetry}
          id="retry-btn"
        >
          ↻ Try Again
        </button>
      </div>

      <ScoreGauge score={result.score} />
      <TranscriptViewer words={result.words} />
      <FeedbackCard feedback={result.feedback} />

      {result.warnings.length > 0 && (
        <div className="warnings-section">
          <div className="section-label">Warnings</div>
          {result.warnings.map((warning, idx) => (
            <div className="warning-item" key={idx}>
              <span>⚠️</span>
              <span>{warning}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
