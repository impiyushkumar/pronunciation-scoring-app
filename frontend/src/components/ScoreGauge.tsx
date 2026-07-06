"use client";

import { useMemo } from "react";

interface ScoreGaugeProps {
  score: number; // 0-100
}

export default function ScoreGauge({ score }: ScoreGaugeProps) {
  const { color, label } = useMemo(() => {
    if (score >= 76) return { color: "var(--score-excellent)", label: "Excellent" };
    if (score >= 61) return { color: "var(--score-good)", label: "Good" };
    if (score >= 41) return { color: "var(--score-fair)", label: "Fair" };
    return { color: "var(--score-poor)", label: "Needs Work" };
  }, [score]);

  // SVG circle math
  const radius = 72;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="score-section">
      <div className="score-gauge">
        <svg viewBox="0 0 160 160">
          <circle
            className="score-gauge-track"
            cx="80"
            cy="80"
            r={radius}
          />
          <circle
            className="score-gauge-fill"
            cx="80"
            cy="80"
            r={radius}
            stroke={color}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
          />
        </svg>
        <div className="score-value">
          <span className="score-number" style={{ color }}>
            {Math.round(score)}
          </span>
          <span className="score-label-text" style={{ color }}>
            {label}
          </span>
          <span className="score-out-of">out of 100</span>
        </div>
      </div>
    </div>
  );
}
