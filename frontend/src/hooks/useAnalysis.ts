"use client";

import { useState, useCallback, useRef } from "react";
import { AnalysisState, AnalysisResponse } from "../lib/types";
import { validateFileBasic, validateDuration } from "../lib/validation";
import { analyzeAudio, ApiError } from "../lib/api";

/**
 * State machine hook for the upload → validate → analyze → results flow.
 * Handles double-submit prevention, abort on unmount, and all error paths.
 */
export function useAnalysis() {
  const [state, setState] = useState<AnalysisState>({ phase: "idle" });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [consent, setConsent] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const processingRef = useRef(false); // double-submit guard

  /**
   * Handle file selection from either drag-drop or file picker.
   * Runs synchronous validation immediately.
   */
  const selectFile = useCallback((file: File | null) => {
    if (!file) {
      setSelectedFile(null);
      setState({ phase: "idle" });
      return;
    }

    // Synchronous validation (type + size)
    const basicResult = validateFileBasic(file);
    if (!basicResult.valid) {
      setState({ phase: "error", message: basicResult.error! });
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
    setState({ phase: "idle" });
  }, []);

  /**
   * Submit the file for analysis.
   * Runs async duration validation, then uploads to backend.
   */
  const analyze = useCallback(async () => {
    if (!selectedFile || !consent) return;

    // Double-submit guard
    if (processingRef.current) return;
    processingRef.current = true;

    // Create abort controller for this request
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      // Phase: Validating (async duration check)
      setState({ phase: "validating" });

      const durationResult = await validateDuration(selectedFile);
      if (!durationResult.valid) {
        setState({ phase: "error", message: durationResult.error! });
        return;
      }

      // Phase: Uploading
      setState({ phase: "uploading", progress: 0 });

      // Phase: Processing (server-side)
      setState({ phase: "processing" });

      const result: AnalysisResponse = await analyzeAudio(
        selectedFile,
        controller.signal
      );

      // Phase: Done
      setState({ phase: "done", result });
    } catch (error) {
      if (controller.signal.aborted) return; // Don't update state if aborted

      const message =
        error instanceof ApiError
          ? error.message
          : "An unexpected error occurred. Please try again.";
      const code = error instanceof ApiError ? error.code : "unknown";

      setState({ phase: "error", message, code });
    } finally {
      processingRef.current = false;
    }
  }, [selectedFile, consent]);

  /**
   * Reset everything for a fresh attempt.
   */
  const reset = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    processingRef.current = false;
    setSelectedFile(null);
    setConsent(false);
    setState({ phase: "idle" });
  }, []);

  /**
   * Dismiss an error and go back to idle (keep the file selected).
   */
  const dismissError = useCallback(() => {
    setState({ phase: "idle" });
  }, []);

  const canAnalyze =
    selectedFile !== null &&
    consent &&
    state.phase !== "validating" &&
    state.phase !== "uploading" &&
    state.phase !== "processing";

  const isProcessing =
    state.phase === "validating" ||
    state.phase === "uploading" ||
    state.phase === "processing";

  return {
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
  };
}
