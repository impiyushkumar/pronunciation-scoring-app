// -----------------------------------------------------------------------
// Shared TypeScript types — mirrors backend Pydantic models
// -----------------------------------------------------------------------

export interface WordResult {
  word: string;
  start: number;
  end: number;
  confidence: number;
  error_type: "mispronunciation" | "unclear" | "omission" | null;
  phonemes: string | null;
}

export interface AnalysisResponse {
  score: number;
  words: WordResult[];
  feedback: string;
  warnings: string[];
  transcript: string;
  language: string | null;
}

export interface ErrorResponse {
  error: string;
  message: string;
  detail?: string;
}

export interface HealthResponse {
  status: string;
  timestamp: number;
  version: string;
}

/** State machine for the upload → analyze flow */
export type AnalysisState =
  | { phase: "idle" }
  | { phase: "validating" }
  | { phase: "uploading"; progress: number }
  | { phase: "processing" }
  | { phase: "done"; result: AnalysisResponse }
  | { phase: "error"; message: string; code?: string };

/** Client-side validation result */
export interface ValidationResult {
  valid: boolean;
  error?: string;
}
