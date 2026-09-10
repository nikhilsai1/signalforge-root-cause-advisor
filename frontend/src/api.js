// API client — talks to Nikhil's FastAPI backend (backend/main.py + routes/*.py).
// No /api prefix, no /alarms or /chat endpoints exist server-side — the
// real routes are /explain-alarm, /root-cause, /ask, /shift-handover,
// /feedback, confirmed by reading routes/*.py and models/schemas.py directly.

// Override per-machine with a .env.local file: VITE_API_URL=http://localhost:8001
// (needed on machines where port 8000 is taken by something else, e.g. Docker).
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function postJSON(path, body) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${path} failed: ${res.status}`);
  return res.json();
}

// Backend's AlarmItem schema: tag, timestamp, priority, message, description, equipment.
function toAlarmItem(alarm) {
  return {
    tag: alarm.tag,
    timestamp: alarm.timestamp,
    priority: alarm.priority,
    description: alarm.description,
    equipment: alarm.equipment,
  };
}

// Runs ISA-18.2 flood detection over a set of alarms, returns which one is
// the root cause plus a grounded RAG answer for it.
export async function fetchRootCause(alarms) {
  return postJSON("/root-cause", { alarms: alarms.map(toAlarmItem) });
}

// Grounded answer for a single alarm tag (defaults to "why did it trip and
// what do I do" if no question is given).
export async function explainAlarm(alarmTag, question) {
  return postJSON("/explain-alarm", { alarm_tag: alarmTag, question });
}

// Free-text operator question, not tied to a specific alarm.
export async function askQuestion(question) {
  return postJSON("/ask", { question });
}

export async function generateShiftHandover(alarms, notes = []) {
  const data = await postJSON("/shift-handover", { alarms: alarms.map(toAlarmItem), notes });
  return data.summary;
}

export async function submitFeedback(alarmTag, note) {
  return postJSON("/feedback", { alarm_tag: alarmTag, note });
}

// Adapts a RagAnswer ({answer, citations, no_match, error}) into the shape
// GuidanceCard expects. `status` distinguishes the three real states so the
// UI can render each cleanly instead of collapsing them into one "Error"
// field: a genuine grounded answer, a clean "nothing matched" result (still
// HTTP 200, the guardrail working as intended), or the AI backend being
// degraded/unreachable (error="ollama_unavailable" from the server, or the
// request never reaching it at all - see the catch handler in App.jsx).
export function toGuidance(ragAnswer, rootCauseLabel) {
  const status = ragAnswer.error ? "unavailable" : ragAnswer.no_match ? "no_match" : "ok";
  return {
    rootCause: rootCauseLabel,
    fix: ragAnswer.answer,
    citation: ragAnswer.citations.join(", "),
    cited: !ragAnswer.no_match && ragAnswer.citations.length > 0,
    status,
  };
}
