"use client";

import { useCallback, useRef, useState, DragEvent, ChangeEvent } from "react";

interface UploadZoneProps {
  onFileSelect: (file: File | null) => void;
  selectedFile: File | null;
  disabled?: boolean;
}

export default function UploadZone({
  onFileSelect,
  selectedFile,
  disabled = false,
}: UploadZoneProps) {
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = useCallback(
    (e: DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      if (!disabled) setDragOver(true);
    },
    [disabled]
  );

  const handleDragLeave = useCallback((e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
  }, []);

  const handleDrop = useCallback(
    (e: DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragOver(false);
      if (disabled) return;

      const file = e.dataTransfer.files?.[0] ?? null;
      if (file) onFileSelect(file);
    },
    [disabled, onFileSelect]
  );

  const handleInputChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0] ?? null;
      if (file) onFileSelect(file);
      // Reset input so same file can be re-selected
      if (inputRef.current) inputRef.current.value = "";
    },
    [onFileSelect]
  );

  const handleBrowseClick = useCallback(() => {
    if (!disabled) inputRef.current?.click();
  }, [disabled]);

  const handleRemove = useCallback(() => {
    onFileSelect(null);
  }, [onFileSelect]);

  const formatSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div
      id="upload-zone"
      className={`upload-zone ${dragOver ? "drag-over" : ""} ${disabled ? "disabled" : ""}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={!selectedFile && !disabled ? handleBrowseClick : undefined}
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-label="Upload audio file"
    >
      <input
        ref={inputRef}
        type="file"
        accept="audio/*,.mp3,.wav,.m4a,.ogg,.flac,.aac,.webm"
        onChange={handleInputChange}
        style={{ display: "none" }}
        aria-hidden="true"
        id="audio-file-input"
      />

      {selectedFile ? (
        /* File selected — show preview */
        <div className="file-preview" onClick={(e) => e.stopPropagation()}>
          <span className="file-preview-icon">🎵</span>
          <div className="file-preview-info">
            <div className="file-preview-name">{selectedFile.name}</div>
            <div className="file-preview-meta">
              {formatSize(selectedFile.size)}
              {selectedFile.type ? ` · ${selectedFile.type}` : ""}
            </div>
          </div>
          {!disabled && (
            <button
              className="file-preview-remove"
              onClick={handleRemove}
              aria-label="Remove selected file"
              id="remove-file-btn"
            >
              ✕
            </button>
          )}
        </div>
      ) : (
        /* No file — show upload prompt */
        <>
          <span className="upload-icon">🎙️</span>
          <div className="upload-title">
            Drop your audio file here
          </div>
          <div className="upload-subtitle">
            or click to browse your files
          </div>
          <button
            className="upload-browse-btn"
            onClick={(e) => {
              e.stopPropagation();
              handleBrowseClick();
            }}
            type="button"
            id="browse-files-btn"
          >
            📁 Browse Files
          </button>
          <div className="upload-constraints">
            <span>🕐 30–45 seconds</span>
            <span>📦 Max 20 MB</span>
            <span>🎵 MP3, WAV, M4A, OGG, FLAC</span>
          </div>
        </>
      )}
    </div>
  );
}
