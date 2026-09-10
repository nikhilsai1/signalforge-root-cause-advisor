export default function ShiftHandoverPanel({ onClose }) {
  return (
    <div className="handover-overlay" onClick={onClose}>
      <div className="handover-panel" onClick={(e) => e.stopPropagation()}>
        <div className="handover-panel__header">
          <span>Shift Handover — Line 1</span>
          <button className="handover-panel__close" onClick={onClose}>
            ×
          </button>
        </div>
        <div className="handover-panel__body">
          <p>
            <strong>1 root-cause event</strong> this shift: Motor_1 overload trip at 14:32,
            42 related alarms clustered under it, not treated as separate issues.
          </p>
          <p>
            Resolved per SOP-14 §3 after clearing a jam on Conveyor_2. Drive reset with a
            ramped start, load confirmed normal.
          </p>
          <p>
            5 lower-priority alarms open at shift end (sensor comm loss, tank level, valve
            position, fan temperature, pump flow), none require immediate action, see alarm
            list for detail.
          </p>
          <p className="handover-panel__note">
            This is placeholder text for the visual shell. The real version will be generated
            from the shift's actual alarm and action logs.
          </p>
        </div>
      </div>
    </div>
  );
}
