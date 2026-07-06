"use client";

import { useState, useCallback } from "react";
import { WordResult } from "../lib/types";

interface TranscriptViewerProps {
  words: WordResult[];
}

export default function TranscriptViewer({ words }: TranscriptViewerProps) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  const getWordClass = useCallback((word: WordResult): string => {
    if (!word.error_type) return "transcript-word word-good";
    return `transcript-word word-${word.error_type}`;
  }, []);

  const formatConfidence = (c: number): string => `${Math.round(c * 100)}%`;

  const formatErrorType = (type: string): string => {
    return type.charAt(0).toUpperCase() + type.slice(1);
  };

  return (
    <div className="transcript-section">
      <div className="section-label">Transcript</div>
      <div className="transcript-words" id="transcript-viewer">
        {words.map((word, idx) => (
          <span
            key={`${word.word}-${idx}`}
            className={getWordClass(word)}
            onMouseEnter={() => setHoveredIndex(idx)}
            onMouseLeave={() => setHoveredIndex(null)}
            data-confidence={word.confidence}
            data-error-type={word.error_type || "none"}
          >
            {word.word}

            {/* Tooltip on hover for flagged words or any word */}
            {hoveredIndex === idx && (
              <div className="word-tooltip">
                {word.error_type && (
                  <div
                    className="tooltip-type"
                    style={{
                      color:
                        word.error_type === "mispronunciation"
                          ? "var(--accent-rose)"
                          : word.error_type === "unclear"
                            ? "var(--accent-amber)"
                            : "var(--text-muted)",
                    }}
                  >
                    {formatErrorType(word.error_type)}
                  </div>
                )}
                <div className="tooltip-confidence">
                  Confidence: {formatConfidence(word.confidence)}
                </div>
                {word.phonemes && (
                  <div className="tooltip-phonemes">/{word.phonemes}/</div>
                )}
              </div>
            )}
          </span>
        ))}
      </div>
    </div>
  );
}
