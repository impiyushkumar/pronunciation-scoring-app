"use client";

interface ErrorBannerProps {
  message: string;
  onDismiss: () => void;
}

export default function ErrorBanner({ message, onDismiss }: ErrorBannerProps) {
  return (
    <div className="error-banner" role="alert" id="error-banner">
      <span className="error-icon">⚠️</span>
      <div className="error-content">
        <div className="error-title">Something went wrong</div>
        <div className="error-message">{message}</div>
      </div>
      <button
        className="error-dismiss"
        onClick={onDismiss}
        aria-label="Dismiss error"
        id="dismiss-error-btn"
      >
        ✕
      </button>
    </div>
  );
}
