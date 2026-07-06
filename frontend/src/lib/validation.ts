// -----------------------------------------------------------------------
// Client-side file validation
// Runs BEFORE upload — first line of defense (server validates too)
// -----------------------------------------------------------------------

import { ValidationResult } from "./types";

const ALLOWED_TYPES = new Set([
  "audio/mpeg",
  "audio/mp3",
  "audio/wav",
  "audio/x-wav",
  "audio/ogg",
  "audio/flac",
  "audio/mp4",
  "audio/x-m4a",
  "audio/aac",
  "audio/webm",
]);

const ALLOWED_EXTENSIONS = new Set([
  ".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac", ".webm", ".mp4",
]);

const MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024; // 20 MB
const MIN_DURATION_S = 30;
const MAX_DURATION_S = 45;

/**
 * Validate file type and size synchronously (no decode needed).
 */
export function validateFileBasic(file: File): ValidationResult {
  // --- Size check ---
  if (file.size > MAX_FILE_SIZE_BYTES) {
    const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
    return {
      valid: false,
      error: `File size must be under 20 MB. Yours is ${sizeMB} MB.`,
    };
  }

  if (file.size === 0) {
    return { valid: false, error: "File is empty." };
  }

  // --- Type check (MIME) ---
  if (file.type && !ALLOWED_TYPES.has(file.type)) {
    const ext = getExtension(file.name);
    // Fallback: some browsers don't set MIME correctly, check extension
    if (!ext || !ALLOWED_EXTENSIONS.has(ext.toLowerCase())) {
      return {
        valid: false,
        error: "Please upload a valid audio file (MP3, WAV, M4A, OGG, FLAC, WebM).",
      };
    }
  }

  // --- Extension check (if MIME is empty/generic) ---
  if (!file.type || file.type === "application/octet-stream") {
    const ext = getExtension(file.name);
    if (!ext || !ALLOWED_EXTENSIONS.has(ext.toLowerCase())) {
      return {
        valid: false,
        error: "Please upload a valid audio file (MP3, WAV, M4A, OGG, FLAC, WebM).",
      };
    }
  }

  return { valid: true };
}

/**
 * Validate audio duration using the Web Audio API (async, decodes the file).
 */
export async function validateDuration(file: File): Promise<ValidationResult> {
  try {
    const arrayBuffer = await file.arrayBuffer();
    const audioContext = new AudioContext();
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
    const duration = audioBuffer.duration;
    await audioContext.close();

    if (duration < MIN_DURATION_S) {
      return {
        valid: false,
        error: `Audio must be 30–45 seconds. Yours is ${Math.round(duration)} seconds.`,
      };
    }

    if (duration > MAX_DURATION_S) {
      return {
        valid: false,
        error: `Audio must be 30–45 seconds. Yours is ${Math.round(duration)} seconds.`,
      };
    }

    return { valid: true };
  } catch {
    return {
      valid: false,
      error: "Could not read this audio file. It may be corrupted or in an unsupported format.",
    };
  }
}

function getExtension(filename: string): string | null {
  const dot = filename.lastIndexOf(".");
  if (dot === -1) return null;
  return filename.slice(dot);
}
