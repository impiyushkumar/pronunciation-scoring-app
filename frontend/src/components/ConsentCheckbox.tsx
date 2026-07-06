"use client";

interface ConsentCheckboxProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
}

export default function ConsentCheckbox({
  checked,
  onChange,
  disabled = false,
}: ConsentCheckboxProps) {
  return (
    <div className="consent-wrapper">
      <label className="consent-label" htmlFor="consent-checkbox">
        <input
          type="checkbox"
          id="consent-checkbox"
          className="consent-checkbox"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          disabled={disabled}
        />
        <span>
          I consent to my audio being processed for pronunciation scoring.{" "}
          <strong>No audio is stored</strong> — it is processed in memory and
          discarded immediately after scoring. Only the text transcript is
          analyzed by AI; raw audio never leaves the processing server.
        </span>
      </label>
    </div>
  );
}
