import { useState } from "react";
import AlarmList from "./components/AlarmList";
import GuidanceCard from "./components/GuidanceCard";
import ChatPanel from "./components/ChatPanel";
import ShiftHandoverPanel from "./components/ShiftHandoverPanel";
import { guidanceByAlarmId } from "./data/mockData";
import "./App.css";

export default function App() {
  const [selectedId, setSelectedId] = useState(1);
  const [handoverOpen, setHandoverOpen] = useState(false);

  return (
    <div className="hmi-shell">
      <header className="hmi-shell__topbar">
        <div className="hmi-shell__brand">SentinalHMI</div>
        <div className="hmi-shell__line">Line 1 · Runtime Copilot</div>
        <button className="handover-button" onClick={() => setHandoverOpen(true)}>
          Generate Shift Handover
        </button>
      </header>

      <main className="hmi-shell__main">
        <AlarmList selectedId={selectedId} onSelect={setSelectedId} />

        <section className="hmi-shell__center">
          <GuidanceCard guidance={guidanceByAlarmId[selectedId]} />
          <ChatPanel />
        </section>
      </main>

      {handoverOpen && <ShiftHandoverPanel onClose={() => setHandoverOpen(false)} />}
    </div>
  );
}
