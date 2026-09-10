import { alarms } from "../data/mockData";

const PRIORITY_LABEL = {
  critical: "Critical",
  high: "High",
  medium: "Medium",
  low: "Low",
};

export default function AlarmList({ selectedId, onSelect }) {
  const rootAlarm = alarms.find((a) => a.isRootCause);
  const otherAlarms = alarms.filter((a) => !a.isRootCause);

  return (
    <div className="alarm-list">
      <div className="alarm-list__header">
        <span>Active Alarms</span>
        <span className="alarm-list__count">{alarms.length + (rootAlarm?.clusteredCount || 0)}</span>
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
              <span className="alarm-card__time">{rootAlarm.timestamp}</span>
            </div>
            <div className="alarm-card__tag">{rootAlarm.tag}</div>
            <div className="alarm-card__desc">{rootAlarm.description}</div>
          </button>
        )}

        {rootAlarm?.clusteredCount && (
          <div className="cluster-summary">
            <span className="cluster-summary__icon">⤷</span>
            {rootAlarm.clusteredCount} related alarms clustered into this root cause
          </div>
        )}

        <div className="alarm-list__divider">Other lines</div>

        {otherAlarms.map((alarm) => (
          <button
            key={alarm.id}
            className={`alarm-card alarm-card--${alarm.priority} ${
              selectedId === alarm.id ? "alarm-card--selected" : ""
            }`}
            onClick={() => onSelect(alarm.id)}
          >
            <div className="alarm-card__top">
              <span className={`alarm-card__priority alarm-card__priority--${alarm.priority}`}>
                {PRIORITY_LABEL[alarm.priority]}
              </span>
              <span className="alarm-card__time">{alarm.timestamp}</span>
            </div>
            <div className="alarm-card__tag">{alarm.tag}</div>
            <div className="alarm-card__desc">{alarm.description}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
