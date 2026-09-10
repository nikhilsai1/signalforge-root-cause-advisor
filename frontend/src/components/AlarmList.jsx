import { useState } from "react";

const PRIORITY_LABEL = { critical: "Critical", high: "High", medium: "Medium", low: "Low" };

function formatTime(timestamp) {
  return timestamp?.includes("T") ? timestamp.split("T")[1].slice(0, 8) : timestamp;
}

export default function AlarmList({ alarms, selectedId, onSelect }) {
  const [expanded, setExpanded] = useState(false);

  const rootAlarm = alarms.find((a) => a.isRootCause);
  const clustered = alarms.filter((a) => !a.isRootCause);

  return (
    <div className="alarm-list">
      <div className="alarm-list__header">
        <span>Active Alarms</span>
        <span className="alarm-list__count">{alarms.length}</span>
      </div>

      <div className="alarm-list__scroll">
        {rootAlarm && (
          <button
            className={`alarm-card alarm-card--${rootAlarm.priority} ${
              selectedId === rootAlarm.id ? "alarm-card--selected" : ""
            }`}
            onClick={() => onSelect(rootAlarm.id)}
          >
            <div className="alarm-card__top">
              <span className="alarm-card__badge">Root Cause</span>
              <span className="alarm-card__time">{formatTime(rootAlarm.timestamp)}</span>
            </div>
            <div className="alarm-card__tag">{rootAlarm.tag}</div>
            <div className="alarm-card__desc">{rootAlarm.description}</div>
          </button>
        )}

        {clustered.length > 0 && (
          <button className="cluster-summary cluster-summary--toggle" onClick={() => setExpanded((v) => !v)}>
            <span className="cluster-summary__icon">⤷</span>
            {clustered.length} related alarms clustered into this root cause
            <span className="cluster-summary__chevron">{expanded ? "▲" : "▼"}</span>
          </button>
        )}

        {expanded &&
          clustered.map((alarm) => (
            <button
              key={alarm.id}
              className={`alarm-card alarm-card--${alarm.priority} alarm-card--nested ${
                selectedId === alarm.id ? "alarm-card--selected" : ""
              }`}
              onClick={() => onSelect(alarm.id)}
            >
              <div className="alarm-card__top">
                <span className={`alarm-card__priority alarm-card__priority--${alarm.priority}`}>
                  {PRIORITY_LABEL[alarm.priority] || alarm.priority}
                </span>
                <span className="alarm-card__time">{formatTime(alarm.timestamp)}</span>
              </div>
              <div className="alarm-card__tag">{alarm.tag}</div>
              <div className="alarm-card__desc">{alarm.description}</div>
            </button>
          ))}
      </div>
    </div>
  );
}
