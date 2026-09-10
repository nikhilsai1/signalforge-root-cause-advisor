import { useState, useEffect } from "react";
import AlarmList from "./components/AlarmList";
import GuidanceCard from "./components/GuidanceCard";
import ChatPanel from "./components/ChatPanel";
import ShiftHandoverPanel from "./components/ShiftHandoverPanel";
import { fetchRootCause, explainAlarm, toGuidance } from "./api";
import rawAlarmFlood from "./data/alarmFlood.json";
import "./App.css";

function adaptAlarm(raw) {
  return {
    id: raw.id,
    tag: raw.tag,
    description: raw.description,
    equipment: raw.equipment,
    priority: (raw.priority || "medium").toLowerCase(),
    timestamp: raw.timestamp,
  };
}

export default function App() {
  const [alarms, setAlarms] = useState([]);
  const [alarmsLoading, setAlarmsLoading] = useState(true);
  const [alarmsError, setAlarmsError] = useState(null);

  const [selectedId, setSelectedId] = useState(null);
  const [guidance, setGuidance] = useState(null);
  const [guidanceLoading, setGuidanceLoading] = useState(false);

  const [handoverOpen, setHandoverOpen] = useState(false);

  // Load the synthetic flood once, then hand it to the backend's ISA-18.2
  // detector so the root-cause marker comes from real analysis, not just
  // the seed data's own is_root_cause flag.
  useEffect(() => {
    const adapted = rawAlarmFlood.map(adaptAlarm);
    fetchRootCause(adapted)
      .then((result) => {
        const rootTag = result.root_alarm?.tag;
        const withRoot = adapted.map((a) => ({ ...a, isRootCause: a.tag === rootTag }));
        setAlarms(withRoot);
        setSelectedId(withRoot.find((a) => a.isRootCause)?.id ?? withRoot[0]?.id ?? null);
        setAlarmsError(null);
      })
      .catch((err) => {
        const fallback = adapted.map((a) => ({ ...a, isRootCause: Boolean(a.isRootCause) }));
        setAlarms(fallback);
        setSelectedId(fallback.find((a) => a.isRootCause)?.id ?? fallback[0]?.id ?? null);
        setAlarmsError(err.message);
      })
      .finally(() => setAlarmsLoading(false));
  }, []);

  // Fetch guidance for whichever alarm is selected.
  useEffect(() => {
    const alarm = alarms.find((a) => a.id === selectedId);
    if (!alarm) return;
    setGuidanceLoading(true);
    explainAlarm(alarm.tag)
      .then((rag) => setGuidance(toGuidance(rag, alarm.description || alarm.tag)))
      .catch(() =>
        setGuidance({
          rootCause: alarm.description || alarm.tag,
          fix: "The AI assistant is temporarily unavailable. Please retry, or consult the SOP directly.",
          citation: "",
          cited: false,
          status: "unavailable",
        })
      )
      .finally(() => setGuidanceLoading(false));
  }, [selectedId, alarms]);

  return (
    <div className="hmi-shell">
      <header className="hmi-shell__topbar">
        <div className="hmi-shell__brand">SentinalHMI</div>
        <div className="hmi-shell__line">
          Line 1 · Runtime Copilot
          {alarmsError && <span className="hmi-shell__error"> · backend unreachable</span>}
        </div>
        <button className="handover-button" onClick={() => setHandoverOpen(true)}>
          Generate Shift Handover
        </button>
      </header>

      <main className="hmi-shell__main">
        {alarmsLoading ? (
          <div className="alarm-list alarm-list--loading">Loading alarms…</div>
        ) : (
          <AlarmList alarms={alarms} selectedId={selectedId} onSelect={setSelectedId} />
        )}

        <section className="hmi-shell__center">
          {guidanceLoading ? (
            <div className="guidance-card guidance-card--empty">Loading guidance…</div>
          ) : (
            <GuidanceCard guidance={guidance} />
          )}
          <ChatPanel />
        </section>
      </main>

      {handoverOpen && <ShiftHandoverPanel alarms={alarms} onClose={() => setHandoverOpen(false)} />}
    </div>
  );
}
