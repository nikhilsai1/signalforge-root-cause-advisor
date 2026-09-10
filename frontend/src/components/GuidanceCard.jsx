export default function GuidanceCard({ guidance }) {
  if (!guidance) {
    return (
      <div className="guidance-card guidance-card--empty">
        Select an alarm to see the guidance card.
      </div>
    );
  }

  return (
    <div className="guidance-card">
      <div className="guidance-card__header">Guidance Card</div>

      <div className="guidance-field">
        <div className="guidance-field__label">Root cause</div>
        <div className="guidance-field__value">{guidance.rootCause}</div>
      </div>

      <div className="guidance-field">
        <div className="guidance-field__label">Fix</div>
        <div className="guidance-field__value">{guidance.fix}</div>
      </div>

      <div className="guidance-card__footer">
        <span className="guidance-card__citation">{guidance.citation}</span>
        {guidance.cited && (
          <span className="guidance-card__cited">
            <span className="guidance-card__check">✓</span> Cited, not guessed
          </span>
        )}
      </div>
    </div>
  );
}
