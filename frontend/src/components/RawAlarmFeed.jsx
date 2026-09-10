// The "before" screen for the demo's opening contrast moment: a bare,
// legacy-style alarm banner with no clustering, no root-cause detection,
// no guidance, no chat. Every alarm from the flood shown flat, exactly as
// a raw EcoStruxure/SCADA alarm summary would dump them on an operator.

function formatTime(timestamp) {
  return timestamp?.includes("T") ? timestamp.split("T")[1].slice(0, 8) : timestamp;
}

export default function RawAlarmFeed({ alarms, onLaunch }) {
  const sorted = [...alarms].sort((a, b) => (a.timestamp < b.timestamp ? -1 : 1));

  return (
    <div className="raw-feed">
      <div className="raw-feed__topbar">
        <span className="raw-feed__title">LINE 1 — ALARM SUMMARY</span>
        <span className="raw-feed__count">{sorted.length} ACTIVE</span>
        <button className="raw-feed__launch" onClick={onLaunch}>
          Launch SentinalHMI →
        </button>
      </div>

      <div className="raw-feed__scroll">
        <table className="raw-feed__table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Tag</th>
              <th>Description</th>
              <th>Priority</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((a) => (
              <tr key={a.id} className={`raw-feed__row raw-feed__row--${a.priority}`}>
                <td>{formatTime(a.timestamp)}</td>
                <td>{a.tag}</td>
                <td>{a.description}</td>
                <td>{a.priority.toUpperCase()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
