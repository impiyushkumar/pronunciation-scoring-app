"use client";

interface FeedbackCardProps {
  feedback: string;
}

export default function FeedbackCard({ feedback }: FeedbackCardProps) {
  if (!feedback) return null;

  return (
    <div className="feedback-section">
      <div className="section-label">Feedback</div>
      <div className="feedback-card">
        <p className="feedback-text">{feedback}</p>
      </div>
    </div>
  );
}
