import { useState } from "react";
import { askQuestion } from "../api";

export default function ChatPanel() {
  const [log, setLog] = useState([]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);

  async function handleSend() {
    const text = draft.trim();
    if (!text || sending) return;
    setLog((prev) => [...prev, { role: "operator", text }]);
    setDraft("");
    setSending(true);
    try {
      const rag = await askQuestion(text);
      const reply = rag.citations.length ? `${rag.answer} (${rag.citations.join(", ")})` : rag.answer;
      setLog((prev) => [...prev, { role: "copilot", text: reply }]);
    } catch (err) {
      setLog((prev) => [...prev, { role: "copilot", text: `Couldn't reach the backend: ${err.message}` }]);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="chat-panel">
      <div className="chat-panel__header">Ask the copilot</div>

      <div className="chat-panel__log">
        {log.map((msg, i) => (
          <div key={i} className={`chat-msg chat-msg--${msg.role}`}>
            <span className="chat-msg__role">{msg.role === "operator" ? "You" : "Copilot"}</span>
            <span className="chat-msg__text">{msg.text}</span>
          </div>
        ))}
        {sending && (
          <div className="chat-msg chat-msg--copilot">
            <span className="chat-msg__role">Copilot</span>
            <span className="chat-msg__text">Thinking…</span>
          </div>
        )}
      </div>

      <div className="chat-panel__input">
        <input
          type="text"
          placeholder="Why did this alarm fire, and what do I do?"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          disabled={sending}
        />
        <button onClick={handleSend} disabled={sending}>
          Send
        </button>
      </div>
    </div>
  );
}
