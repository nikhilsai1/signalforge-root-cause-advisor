import { useState } from "react";
import { initialChatLog } from "../data/mockData";

export default function ChatPanel() {
  const [log, setLog] = useState(initialChatLog);
  const [draft, setDraft] = useState("");

  function handleSend() {
    const text = draft.trim();
    if (!text) return;
    setLog((prev) => [
      ...prev,
      { role: "operator", text },
      {
        role: "copilot",
        text: "No backend connected yet, this is placeholder shell text. Real answers will be grounded in retrieved SOPs once the RAG endpoint is wired in.",
      },
    ]);
    setDraft("");
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
      </div>

      <div className="chat-panel__input">
        <input
          type="text"
          placeholder="Why did this alarm fire, and what do I do?"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
        />
        <button onClick={handleSend}>Send</button>
      </div>
    </div>
  );
}
