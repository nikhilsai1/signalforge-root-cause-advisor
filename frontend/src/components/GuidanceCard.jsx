import { useState } from "react";
import { submitFeedback } from "../api";

export default function GuidanceCard({ guidance, alarmTag, onCorrectionSubmitted }) {
  const [note, setNote] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (!guidance) {
    return (
      <div className="guidance-card guidance-card--empty">
        Select an alarm to see the guidance card.
      </div>
    );
  }

  const status = guidance.status || (guidance.cited ? "ok" : "no_match");

  async function handleSubmitCorrection() {
    const text = note.trim();
    if (!text || submitting) return;
    setSubmitting(true);
    try {
      await submitFeedback(alarmTag, text);
      setNote("");
      onCorrectionSubmitted?.();
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className={`guidance-card guidance-card--${status}`}>
      <div className="guidance-card__header">Guidance Card</div>

      <div className="guidance-field">
        <div className="guidance-field__label">Root cause</div>
        <div className="guidance-field__value">{guidance.rootCause}</div>
      </div>

      <div className="guidance-field">
        <div className="guidance-field__label">
          {status === "unavailable" ? "Status" : status === "no_match" ? "Result" : "Fix"}
        </div>
        <div className="guidance-field__value">{guidance.fix}</div>
      </div>

      <div className="guidance-card__footer">
        <span className="guidance-card__citation">{guidance.citation}</span>
        {status === "ok" && guidance.cited && (
          <span className="guidance-card__cited">
            <span className="guidance-card__check">✓</span> Cited, not guessed
          </span>
        )}
        {status === "no_match" && (
          <span className="guidance-card__status guidance-card__status--no-match">
            No matching SOP found
          </span>
        )}
        {status === "unavailable" && (
          <span className="guidance-card__status guidance-card__status--unavailable">
            ⚠ AI assistant unavailable
          </span>
        )}
      </div>

      {alarmTag && (
        <div className="guidance-card__correction">
          <div className="guidance-field__label">Log a field correction</div>
          <div className="guidance-card__correction-row">
            <input
              type="text"
              placeholder="e.g. actual cause was a failing VFD cooling fan, not a jam"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSubmitCorrection()}
              disabled={submitting}
            />
            <button onClick={handleSubmitCorrection} disabled={submitting || !note.trim()}>
              {submitting ? "Saving…" : "Submit"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
