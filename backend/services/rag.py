import re
from datetime import datetime, timezone

from sentence_transformers import SentenceTransformer

from services.chroma_client import get_sop_collection
from services.ollama_client import OllamaUnavailableError, ollama_client

_embedder = SentenceTransformer("all-MiniLM-L6-v2")

_SECTION_RE_PILCROW = re.compile(r"^¶\s*(\d+)\.?\s*(.*)$", re.MULTILINE)
_SECTION_RE_HASH = re.compile(r"^#\s*(\d+)\s*$", re.MULTILINE)

NO_MATCH_PHRASE = "no matching procedure found"

# Built dynamically per-call by _build_system_prompt() rather than as one
# static prompt. Reason: an earlier version always described the operator-note
# citation convention even when no note was actually retrieved for a given
# query, and the model fabricated a fully-invented "[operator note on ...]"
# citation, with plausible-sounding content, that did not exist anywhere in
# ChromaDB. The concept must only be mentioned to the model when a real one
# is present in that call's context, or it gets treated as a pattern to
# follow rather than a fact to check.
_SYSTEM_PROMPT_INTRO = (
    "You are an industrial operations assistant. Answer the operator's question "
    "using ONLY the context provided below. Synthesize a single, confident, "
    "actionable answer from ALL relevant context, even if the full answer is "
    "spread across multiple sections. For every claim, cite the section it came "
    "from in the form [source ¶section]. Do not hedge or discuss what the "
    "context does or does not cover. Do not invent, reference, or imply any "
    "information - including any \"operator note\" - that is not explicitly "
    "present in the context below."
)

_OPERATOR_NOTE_ADDENDUM = (
    " The context below includes one or more operator notes - free-text "
    "corrections a real operator logged after a static SOP turned out to be "
    "wrong or incomplete, cited as [operator note on <alarm_tag>]. Where an "
    "operator note addresses the same point as a static SOP section, the "
    "operator note is the current, field-verified guidance and takes priority "
    "over the static SOP - follow it, and say so."
)

_SYSTEM_PROMPT_TAIL = (
    "\n\nOnly if NONE of the context is relevant to the question, respond with "
    f"exactly and only: '{NO_MATCH_PHRASE.capitalize()}.' Do not use outside "
    "knowledge, and do not mix this exact phrase into an otherwise-grounded answer."
)


def _build_system_prompt(chunks: list[dict]) -> str:
    prompt = _SYSTEM_PROMPT_INTRO
    if any(c.get("type") == "operator_note" for c in chunks):
        prompt += _OPERATOR_NOTE_ADDENDUM
    return prompt + _SYSTEM_PROMPT_TAIL

# How much a fresh operator note's effective distance is reduced by, decaying
# by half every OPERATOR_NOTE_BOOST_HALFLIFE_HOURS. A note logged seconds ago
# gets nearly the full boost; a week-old note gets almost none - stale
# corrections shouldn't out-rank a static SOP forever.
# 0.5 was too small in practice: a query that names the alarm tag explicitly
# (e.g. "Why did LINE1.MTR_01.OVERLOAD trip?") embeds very close to the SOP
# chunk containing that exact tag (~0.81 distance), and even a fresh note
# only closes about half that gap at 0.5 boost. Raised to 0.9 so a brand-new
# note reliably outranks a well-matched SOP, confirmed via
# /_debug/retrieve against the live tag-heavy query the frontend actually
# sends (not just the informal phrasing used in earlier checkpoint tests).
OPERATOR_NOTE_BOOST_MAX = 0.9
OPERATOR_NOTE_BOOST_HALFLIFE_HOURS = 24.0


def _recency_boost(timestamp_str: str | None) -> float:
    if not timestamp_str:
        return 0.0
    try:
        ts = datetime.fromisoformat(timestamp_str)
    except ValueError:
        return 0.0
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    age_hours = max((datetime.now(timezone.utc) - ts).total_seconds() / 3600, 0.0)
    return OPERATOR_NOTE_BOOST_MAX * (0.5 ** (age_hours / OPERATOR_NOTE_BOOST_HALFLIFE_HOURS))


def chunk_sop(text: str, source_name: str) -> list[dict]:
    """Split an SOP into numbered sections.

    Supports two section-marker styles:
      - '¶<n>. <Title>' inline paragraph markers (the real SOP format used
        under data/sops/), where <Title> is folded into the chunk body.
      - A line containing only '# <n>' (e.g. '# 3'), used by throwaway
        test fixtures.
    Returns a list of {source, section, text} dicts, one per section.
    """
    matches = list(_SECTION_RE_PILCROW.finditer(text))
    pilcrow = bool(matches)
    if not matches:
        matches = list(_SECTION_RE_HASH.finditer(text))

    chunks = []
    for i, m in enumerate(matches):
        section = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if pilcrow:
            title = m.group(2).strip()
            if title:
                body = f"{title}\n{body}" if body else title
        if body:
            chunks.append({"source": source_name, "section": section, "text": body})
    return chunks


def ingest_sop_text(text: str, source_name: str) -> int:
    """Chunk, embed, and store an SOP document in ChromaDB. Returns chunk count."""
    chunks = chunk_sop(text, source_name)
    if not chunks:
        return 0

    collection = get_sop_collection()
    embeddings = _embedder.encode([c["text"] for c in chunks]).tolist()
    collection.upsert(
        ids=[f"{source_name}-sop-{c['section']}" for c in chunks],
        documents=[c["text"] for c in chunks],
        embeddings=embeddings,
        metadatas=[
            {"source": c["source"], "section": c["section"], "type": "sop"}
            for c in chunks
        ],
    )
    return len(chunks)


def add_operator_note(alarm_tag: str, note_text: str) -> None:
    """Store an operator's free-text correction for an alarm type. Embedded
    and stored alongside static SOP chunks, tagged with a timestamp so
    retrieve() can boost it by recency - this is what lets the system
    self-improve: a fresh field correction outranks the static SOP on the
    next matching query without needing to edit the SOP itself.
    """
    # Embed with the alarm tag as context. Without this, a query that names
    # the tag explicitly (e.g. "Why did LINE1.MTR_01.OVERLOAD trip?") embeds
    # very close to the matching SOP chunk (which contains that exact tag
    # string) but not to the note (which usually doesn't repeat the tag),
    # so the fixed recency boost isn't enough to make the note win - found
    # via a live UI test where the note lost against a tag-heavy query
    # despite being brand new. The document stored/embedded includes the
    # tag; the citation shown to the user still comes from the alarm_tag
    # metadata field via _format_citation(), not from this text.
    embed_text = f"{alarm_tag}: {note_text}"
    collection = get_sop_collection()
    embedding = _embedder.encode([embed_text]).tolist()
    note_id = f"note-{alarm_tag}-{datetime.now(timezone.utc).isoformat()}"
    collection.upsert(
        ids=[note_id],
        documents=[embed_text],
        embeddings=embedding,
        metadatas=[
            {
                "type": "operator_note",
                "alarm_tag": alarm_tag,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ],
    )


def retrieve(query: str, top_k: int = 3) -> list[dict]:
    """Embed the query and return the top_k most relevant chunks.

    Over-fetches candidates, then re-ranks by an "effective distance": raw
    semantic distance for static SOP chunks, distance minus a recency boost
    for operator notes. This lets a fresh, relevant operator note out-rank a
    static SOP chunk that's nominally a slightly closer semantic match.
    """
    try:
        collection = get_sop_collection()
        count = collection.count()
        if count == 0:
            return []

        # Fetch the WHOLE collection, not just a small multiple of top_k.
        # ChromaDB's .query() returns nearest neighbors by raw distance
        # before any recency boost is applied - a small over-fetch window
        # (e.g. top_k*3) can exclude an operator note entirely if its raw
        # distance isn't already in that window, even though the boost
        # would make it the best match. At this corpus size (tens of
        # chunks) fetching everything and re-ranking in Python is free;
        # this stops being fine only at a scale this project won't reach.
        query_embedding = _embedder.encode([query]).tolist()
        results = collection.query(query_embeddings=query_embedding, n_results=count)
    except Exception:
        # Chroma unavailable/corrupted - degrade to "nothing retrieved" so
        # generate_answer's existing no-match path handles it cleanly,
        # rather than letting a storage-layer error crash the request.
        return []

    hits = []
    for text, meta, distance in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        # collection.count() can be momentarily stale relative to .query()
        # (e.g. right after a delete elsewhere) - when n_results exceeds
        # what's actually available, Chroma pads the result lists with
        # None rather than truncating. Skip those instead of crashing.
        if meta is None or text is None:
            continue
        effective_distance = distance
        if meta.get("type") == "operator_note":
            effective_distance = distance - _recency_boost(meta.get("timestamp"))
        hits.append({**meta, "text": text, "distance": effective_distance})

    hits.sort(key=lambda h: h["distance"])
    return hits[:top_k]


def _format_citation(chunk: dict) -> str:
    if chunk.get("type") == "operator_note":
        return f"[operator note on {chunk['alarm_tag']}]"
    return f"[{chunk['source']} ¶{chunk['section']}]"


# Empirically calibrated against data/sops/ (see test_real_sops.py):
# clearly relevant chunks scored ~0.6-0.91 distance, clearly unrelated
# questions started at ~1.57. Tangentially-worded but NOT-actually-covered
# questions land right around ~1.0 - tested at 1.05, that band let the LLM
# hallucinate a citation to a section that doesn't exist (SOP-08 has no
# section 3.2) rather than decline. A fabricated citation is a worse demo
# failure than an occasional over-cautious "no match" on a vaguely-worded
# question, so this stays tight even though it costs some recall on very
# short/informal phrasings (confirmed: the team's actual demo phrasing,
# "Why did Motor_1 trip? What do I do right now?", clears this with margin
# at ~0.91).
RELEVANCE_DISTANCE_THRESHOLD = 0.95


def generate_answer(query: str, top_k: int = 3) -> dict:
    """Retrieve grounding context and generate a cited, grounded answer.

    Returns {answer, citations, no_match, error}. Never raises - a down
    Ollama or Chroma degrades to a clean no_match-shaped response instead
    of crashing the request, so the UI never has to render a raw error.
    """
    chunks = retrieve(query, top_k=top_k)
    relevant_chunks = [c for c in chunks if c["distance"] <= RELEVANCE_DISTANCE_THRESHOLD]

    if not relevant_chunks:
        return {
            "answer": "No matching procedure found in the SOP knowledge base.",
            "citations": [],
            "no_match": True,
            "error": None,
        }

    context = "\n\n".join(
        f"{_format_citation(c)}\n{c['text']}" for c in relevant_chunks
    )
    prompt = f"Context:\n{context}\n\nOperator question: {query}"

    try:
        answer = ollama_client.generate(prompt, system=_build_system_prompt(relevant_chunks))
    except OllamaUnavailableError:
        return {
            "answer": "The AI assistant is temporarily unavailable. Please retry, "
            "or consult the SOP directly: "
            + ", ".join(sorted({_format_citation(c) for c in relevant_chunks})),
            "citations": [],
            "no_match": True,
            "error": "ollama_unavailable",
        }

    # Only treat as a true no-match if the phrase leads the answer, not if the
    # model mentions it in passing while still giving grounded content.
    no_match = answer.strip().lower().lstrip("'\"").startswith(NO_MATCH_PHRASE)

    citations = [] if no_match else sorted({_format_citation(c) for c in relevant_chunks})

    return {"answer": answer, "citations": citations, "no_match": no_match, "error": None}


SHIFT_HANDOVER_SYSTEM_PROMPT = (
    "You write concise, professional shift handover summaries for industrial "
    "operators. Use only the alarms and notes provided below - no outside "
    "knowledge. Group related alarms under their likely root cause rather than "
    "listing each one individually. Flag anything still unresolved. Keep it "
    "under 150 words."
)


def summarize_shift_handover(alarms: list[dict], notes: list[str]) -> dict:
    """Summarize recent alarms + operator notes into a shift handover.
    Grounded only in what's passed in, not SOP retrieval. Returns {summary}.
    """
    if not alarms and not notes:
        return {"summary": "No alarms or notes to report for this shift."}

    alarm_lines = "\n".join(
        f"- {a.get('timestamp', '')} {a.get('tag', '')}: "
        f"{a.get('description') or a.get('message') or ''} "
        f"(priority: {a.get('priority', '')})"
        for a in alarms
    )
    notes_block = "\n".join(f"- {n}" for n in notes) if notes else "(none)"

    prompt = (
        f"Alarms this shift:\n{alarm_lines or '(none)'}\n\n"
        f"Operator notes this shift:\n{notes_block}\n\n"
        "Write the shift handover summary."
    )

    try:
        summary = ollama_client.generate(prompt, system=SHIFT_HANDOVER_SYSTEM_PROMPT)
    except OllamaUnavailableError:
        return {
            "summary": "AI summary unavailable (Ollama unreachable). Raw counts for "
            f"this shift: {len(alarms)} alarms, {len(notes)} operator notes."
        }

    return {"summary": summary}
