import { useState, useEffect } from "react";
import { generateShiftHandover } from "../api";

export default function ShiftHandoverPanel({ alarms, onClose }) {
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    generateShiftHandover(alarms)
      .then(setSummary)
      .catch(() =>
        setError("The AI assistant is temporarily unavailable. Please retry, or consult the SOP directly.")
      );
  }, [alarms]);

  return (
    <div className="handover-overlay" onClick={onClose}>
      <div className="handover-panel" onClick={(e) => e.stopPropagation()}>
        <div className="handover-panel__header">
          <span>Shift Handover — Line 1</span>
          <button className="handover-panel__close" onClick={onClose}>×</button>
        </div>
        <div className="handover-panel__body">
          {error && <p className="handover-panel__note">{error}</p>}
          {!error && !summary && <p>Generating handover summary…</p>}
          {summary && <p>{summary}</p>}
        </div>
      </div>
    </div>
  );
}
