# Root Cause Advisor — Technical Deep Dive

A reference for answering judge questions in depth. Every section pairs a **plain-English** explanation with the **technical** version underneath, plus *why we built it this way* and *why it actually helped*. Section 4 covers real bugs we found and fixed while testing — worth reading before Q&A, since "how do you know it works" is a likely question and the honest answer is "we broke it on purpose and checked."

---

## 1. The problem, in one paragraph

**Plain English:** When one piece of equipment fails on a factory floor, it doesn't fail quietly — it triggers a cascade of 40+ related alarms within minutes as the fault ripples through connected systems. An operator staring at that alarm list has no way to tell which one is the actual cause versus which 44 are just noise from the same root problem. Senior operators learn to filter this by experience; when they retire or change shifts, that judgment leaves with them.

**Technical:** This is a known industrial automation problem with a named standard response — ISA-18.2 defines an "alarm flood" as more than 10 alarms in a 10-minute window, and prescribes root-cause identification as the correct operator response, not alarm-by-alarm triage. Our system implements that standard programmatically instead of relying on tribal knowledge.

---

## 2. System architecture

**Plain English:** Four pieces talk to each other: a backend that does the thinking (Python/FastAPI), a knowledge base of standard operating procedures (SOPs) it searches through, a small AI model that writes the actual answer, and a web dashboard the operator looks at. When an alarm flood comes in, the backend figures out which alarm is the real root cause, looks up the matching procedure, asks the AI to write a grounded answer citing that procedure, and checks live sensor data to confirm which sensor is actually behaving abnormally.

**Technical:**
```
Alarm flood (JSON) → ISA-18.2 flood detector (sliding 10-min window, Python)
                            │
                            ▼ root alarm (earliest in window)
              ChromaDB vector search over embedded SOP chunks
                            │
                            ▼ top-k relevant chunks (distance-filtered)
        Ollama (llama3.2:3b, local, temperature=0.1) generates the answer
                            │
                            ▼
        IsolationForest (scikit-learn) scores live sensor readings
                            │
                            ▼
   FastAPI returns {answer, citations, no_match, error} → React UI renders it
```
Everything after "alarm flood JSON" runs locally — no network call leaves the machine except a one-time embedding-model download from Hugging Face (cached forever after).

**Why this shape:** we deliberately split "find the relevant text" (ChromaDB, a vector database) from "write the answer" (the LLM). This is a RAG (Retrieval-Augmented Generation) architecture — the LLM never has to *remember* facts, it only has to *summarize* facts we hand it in the prompt. That's the single biggest lever against hallucination: a small 3B model is bad at recalling facts from its training data, but genuinely good at summarizing text placed directly in front of it.

---

## 3. Component deep-dives

### 3.1 Alarm flood clustering (ISA-18.2)

**Plain English:** Given a pile of alarms with timestamps, find the earliest one in any cluster of more than 10 alarms within 10 minutes — that's almost always the actual root cause, since everything after it is usually a downstream symptom.

**Technical:** `services/alarm_flood.py::detect_flood()`. Sorts alarms by timestamp, slides a 10-minute window across them, and the first window containing more than 10 alarms is flagged as a flood; the earliest alarm in that window is the root alarm, the rest are marked suppressed.

**Why we built it this way:** ISA-18.2 defines the flood threshold and the "earliest = root" heuristic explicitly — we didn't invent this, we implemented the actual industry standard so the logic is defensible, not a guess.

**Why it helped:** verified against Mahesh's real 45-alarm synthetic flood — the detected root alarm matched the dataset's own ground-truth `is_root_cause` flag exactly, on the first try, every time we re-ran it.

### 3.2 RAG pipeline — grounded, cited answers

**Plain English:** The system never lets the AI answer from memory. It first searches the actual SOP documents for the most relevant passage, hands that passage to the AI, and tells it: "answer using only this text, and cite which section it came from." If nothing relevant is found, it says so explicitly instead of making something up.

**Technical:** SOPs are chunked by section marker (`¶N.` in the real documents), embedded with `sentence-transformers/all-MiniLM-L6-v2`, and stored in ChromaDB. At query time we embed the question, retrieve the closest chunks by cosine/L2 distance, and only pass chunks under a calibrated distance threshold (0.95) into the LLM prompt. The system prompt explicitly forbids answering from outside knowledge and mandates the exact phrase `"No matching procedure found"` when nothing qualifies.

**Why we built it this way:** the distance threshold isn't a guess — we empirically measured it. Genuinely relevant SOP matches scored 0.6–0.91 distance in our real corpus; clearly unrelated questions scored 1.5+. We tested a looser threshold (1.05) to catch more edge cases and it caused the model to **hallucinate a citation to a section that doesn't exist** rather than decline. We tightened it back down — a fabricated citation is a worse failure than an occasional over-cautious "no match."

**Why it helped:** this is the system's core credibility claim — "cited, not guessed" — and it's backed by a real, measured guardrail, not just a prompt instruction (prompt instructions alone don't reliably stop a 3B model from hallucinating; the distance cutoff does the actual work).

### 3.3 Anomaly detection — confirming which sensor is actually wrong

**Plain English:** The AI's text answer says "check the VFD load" — but how do we know that's actually abnormal right now, versus just a guess based on the alarm name? We run the live sensor readings (temperature, pressure, motor load) through a statistical anomaly detector that's been trained on what "normal" looks like, and it independently confirms which specific sensor is out of range.

**Technical:** `services/anomaly.py` — one `IsolationForest` model per sensor tag (not one shared model — different sensors have unrelated scales and distributions, temperature ~60-100°C vs. load ~50-125%, mixing them into one model would be meaningless). Trained on baseline data, scores new readings, flags outliers.

**Why we built it this way:** we initially had a single shared model across all sensors — a real bug we caught and fixed. A shared model can't tell "load is high" from "temperature is high" because it has no concept of which sensor a reading belongs to.

**Why it helped:** tested against a real injected spike in the synthetic dataset — `motor_load_pct` was correctly flagged anomalous 21 out of 22 readings during the fault window, while `temperature` and `pressure` stayed mostly normal (5/22 and 3/22 — background noise, not false alarms). This is the fusion piece that makes the answer *provably* grounded in live data, not just text retrieval.

### 3.4 Self-improving feedback loop

**Plain English:** An operator can tell the system "actually, the real cause was X, not what the manual says" — and the next time that alarm fires, the system remembers the operator's correction and prioritizes it over the generic manual, without anyone having to go edit the SOP document.

**Technical:** Operator notes are embedded and stored in the same ChromaDB collection as static SOPs, tagged `type=operator_note` with a timestamp. Retrieval re-ranks by an "effective distance" — raw semantic distance for SOPs, distance minus a recency boost for notes (boost decays by half every 24 hours, so a week-old correction doesn't dominate forever).

**Why we built it this way — and the real debugging story:** this took three iterations to get right, which is worth mentioning if asked "how confident are you this works":
1. First version: notes were embedded without their alarm tag, so a query naming the exact tag (`"Why did LINE1.MTR_01.OVERLOAD trip?"`) matched the SOP (which literally contains that tag string) far better than the note ever could.
2. Fixed the embedding, but the boost (0.5) still wasn't large enough to close the gap — raised to 0.9, verified against actual measured distance numbers, not guessed.
3. The real root cause: retrieval only asked the database for the 9 nearest neighbors *before* applying any boost. With 40 competing SOP chunks, a note's raw ranking often didn't make that initial window at all — so the boost never got a chance to act, because the note was never even fetched. Fixed by retrieving the whole collection and re-ranking in Python (cheap at this corpus size).

**Why it helped:** this is the single most "wow" moment in the demo, and it's the one we tested most rigorously — because the first version silently didn't work under the exact phrasing the live demo actually uses, and we only caught it by testing through the real UI instead of trusting isolated unit tests with different wording.

### 3.5 Guardrails — nothing crashes, nothing lies

**Plain English:** If the AI model isn't running, or something goes wrong, the operator should see a clean "temporarily unavailable, here's what to check manually" message — never a raw error screen, and never a confident-sounding wrong answer.

**Technical:** `OllamaUnavailableError` wraps connection failures; `generate_answer()` catches it and returns a structured `{no_match: true, error: "ollama_unavailable"}` response (HTTP 200, not 500) that still lists which SOP citations *would* apply, since retrieval doesn't depend on the LLM. A global FastAPI exception handler catches anything unhandled as a last resort. On the frontend, three distinct visual states (grounded / no-match / unavailable) replace what used to be a single generic error field.

**Why we built it this way:** we found this gap by literally killing the Ollama process mid-demo-rehearsal and watching what happened — the first version leaked a raw browser error string ("Failed to fetch") into the UI. We don't guess about failure modes, we induce them and watch.

**Why it helped:** verified live — killed Ollama's server *and* its supervisor process entirely, hit all three AI-backed endpoints, got clean structured responses every time, restarted Ollama, confirmed normal operation resumed. This directly backs the "fully offline, zero cloud calls" claim with a real test, not just an architecture diagram.

### 3.6 Modbus / EcoStruxure integration

**Plain English:** Instead of only working with fake demo data, the system can read live tag values (motor status, load, temperature, alarm codes) from real industrial protocol traffic — the same protocol a real Schneider Electric HMI panel uses — so the same data feed can drive both a real operator display and our AI backend simultaneously.

**Technical:** `modbus_sim_server.py` runs a real, spec-compliant Modbus TCP server (via `pymodbus`) simulating a motor's holding registers; `telemetry_bridge.py` polls it and writes live values to `data/live_telemetry.json`, in the same field-name convention the anomaly detector already understands. A second adapter (`flatten_live_telemetry`) lets one detector trained on synthetic baseline data score live Modbus readings directly, with no separate live-data model needed.

**Why we built it this way:** rather than maintain two separate data pipelines (synthetic for demo, real for "proof"), we designed the live feed to plug into the exact same anomaly-detection code path as the synthetic data.

**Why it helped:** verified end-to-end — ran the simulator, waited for its built-in fault injection to trigger, fed the real live reading through a detector trained purely on synthetic baseline data, and both `motor_load_pct` and `temperature` were correctly flagged anomalous. Real data, scored by a model that never saw real data during training, still worked.

### 3.7 Frontend

**Plain English:** A dark, industrial-style dashboard — alarm list with severity colors, a guidance card showing root cause/fix/citation, a chat box for free-form questions, and a shift-handover summary button.

**Technical:** React + Vite, plain `fetch()` calls (no heavy HTTP client needed), CORS-enabled backend, configurable API URL via `.env.local` for machines where the default port is taken.

**Why it helped:** building it against the real backend contract (not mock data) from early on meant integration issues surfaced and got fixed well before the final rehearsal, not during it.

---

## 4. Real bugs we found and fixed (this is the credibility section)

If a judge asks "how do you know this actually works" or "what could go wrong," this list *is* the answer — every item here was a real, reproducible failure we caught by testing, not a hypothetical:

| # | Bug | How we found it | Fix |
|---|---|---|---|
| 1 | Chunker produced zero chunks against real SOPs (only worked on a fake test fixture) | Tested against Mahesh's actual SOP files instead of trusting the fixture | Support both section-marker formats |
| 2 | A tangential-but-uncovered question got a degenerate non-answer instead of a clean decline | Deliberately asked an out-of-scope question | Added the distance-threshold guardrail |
| 3 | Loosening that guardrail for better recall caused a **fabricated citation to a section that doesn't exist** | Tested the loosened version before shipping it | Reverted to the tighter, measured threshold |
| 4 | Single shared anomaly model couldn't distinguish sensors | Reviewed the math, not just the output | One IsolationForest per tag |
| 5 | System prompt describing operator notes caused the model to **invent a fake note that was never stored** | Caught mid-demo-rehearsal — citation looked plausible but didn't exist in the database | System prompt only mentions the concept when a real note is actually retrieved that call |
| 6 | Operator notes embedded without their alarm tag lost to tag-heavy queries | Tested through the real frontend, not just an isolated query | Embed notes with tag context |
| 7 | Recency boost too weak to overcome a strong SOP match | Measured real distance numbers instead of guessing | Raised and empirically re-verified |
| 8 | Retrieval's over-fetch window excluded notes before boosting could even apply | Traced the actual retrieval code path, found the real root cause | Fetch the whole collection, re-rank in Python |
| 9 | A stale `collection.count()` after a delete crashed the request with a raw Python exception | Happened live while re-testing bug #8's fix | Global exception handler already caught it cleanly (validated the guardrail); added defensive `None` handling |
| 10 | Frontend showed raw JS error strings ("Failed to fetch") instead of a clean message | Killed the backend mid-test on purpose | Unified clean "AI assistant unavailable" state across all 3 components |
| 11 | Modbus simulator crashed on a fresh install — a `pymodbus` library update had renamed/removed the classes the code used | Ran a full clean end-to-end verification from scratch | Pinned to the compatible library version, verified addressing and fault-trigger still correct |

Eleven real, independently-reproducible bugs, found by actually running the system adversarially rather than trusting it — that's the honest story of why we're confident in the demo, not a claim of "it just worked."

---

## 5. Key design decisions and why

**Why a local LLM (Ollama/llama3.2:3b) instead of a cloud API (GPT-4, Claude, etc.)?**
The entire pitch is zero data leaving the OT (operational technology) network — a real requirement for industrial security postures aligned to ISA/IEC 62443. A cloud API call is a network dependency and a data exfiltration point by definition; a local model isn't. The tradeoff is honest: a 3B local model is less capable than a frontier cloud model, which is exactly why the RAG grounding and guardrails matter so much — we're compensating for a smaller model with better retrieval discipline, not hoping the model is smart enough to not need it.

**Why ChromaDB specifically?**
Lightweight, embedded (no separate server process to manage), Python-native, good enough at this corpus scale (tens of documents). At real-plant scale (thousands of SOPs) you'd lean on its approximate-nearest-neighbor indexing rather than our current "fetch everything and re-rank" approach — that's a config change, not a rewrite.

**Why Isolation Forest for anomaly detection, not a neural approach?**
It's an unsupervised method that doesn't need labeled "this was an anomaly" training data — which we don't have for a hackathon-scale synthetic dataset. It's also fast to train and interpretable (you can literally show a distance/score number backing the flag), which matters when you're asking an operator to trust a claim about their equipment.

**Why temperature 0.1, not 0 or default (often ~0.7-0.8)?**
Fully deterministic (temperature 0) can produce repetitive or degenerate text with small models. Default temperature introduced real answer-to-answer variance we observed directly (same question, different section cited between runs). 0.1 was the empirical sweet spot — low variance, not degenerate.

**Why did we build our own guardrails instead of trusting the model's own judgment?**
Because we tested the model's own judgment and it failed — twice (bugs #2 and #5 above). "Trust the prompt instructions" is not a reliable safety strategy for a 3B model; a deterministic, measured, code-level check is.

---

## 6. Honest limitations — what we'd say if asked "what's not done"

- **No formal accuracy percentage.** We didn't compute one, and we're not going to make one up under pressure — the honest position is that the guardrail-based approach (explicit decline vs. confident answer) is the reliability strategy, not a confidence score.
- **Corpus-scale retrieval.** "Fetch the whole collection and re-rank in Python" is correct and fast at our current SOP-library size, but would need approximate-nearest-neighbor indexing at real-plant scale (thousands of documents). ChromaDB supports this natively; it's a config change we haven't needed to make yet.
- **Operator note input isn't hardened against bad-faith input.** Anyone with UI access can submit a "correction" today; a production version would need an approval step or role gating before a note can outrank a validated SOP.
- **EcoStruxure integration is real Modbus protocol work**, verified by the team member who built it, but the deepest verification any of us has done independently is the shared-simulator architecture and register-level data flow — worth being ready to speak to specifics if pressed on exactly what was tested versus configured.
- **Single alarm-type demo depth.** The live demo is deep on one scenario (`Motor_1` overload) because that's what's been most rigorously tested; the underlying pipeline is general (8 SOPs, multiple equipment types), but we haven't rehearsed every alarm type as thoroughly as this one.

---

## 7. Quick-reference answers

| If asked... | Say... |
|---|---|
| "How is this different from ChatGPT + RAG?" | ISA-18.2 flood clustering + anomaly detection fused in, not just Q&A over documents |
| "What stops hallucination?" | Measured distance threshold + explicit decline path, not just a prompt instruction — and we can point to a real bug we caught and fixed |
| "Is it really offline?" | Yes — we killed Ollama mid-test and verified clean degradation, not just designed for it |
| "How confident are you this works?" | We found and fixed 11 real bugs by testing adversarially — that's the actual confidence source |
| "What's next?" | Real Harmony panel deployment, expanded SOP library, ANN indexing at scale, hardened feedback input |
