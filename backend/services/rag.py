import re
from datetime import datetime, timezone

from sentence_transformers import SentenceTransformer

from services.chroma_client import get_sop_collection
from services.ollama_client import ollama_client

_embedder = SentenceTransformer("all-MiniLM-L6-v2")

_SECTION_RE_PILCROW = re.compile(r"^¶\s*(\d+)\.?\s*(.*)$", re.MULTILINE)
_SECTION_RE_HASH = re.compile(r"^#\s*(\d+)\s*$", re.MULTILINE)

NO_MATCH_PHRASE = "no matching procedure found"

SYSTEM_PROMPT = (
    "You are an industrial operations assistant. Answer the operator's question "
    "using ONLY the context provided below. Synthesize a single, confident, "
    "actionable answer from ALL relevant context, even if the full answer is "
    "spread across multiple entries. Context comes in two kinds: static SOP "
    "sections, cited as [source ¶section], and operator notes - free-text "
    "corrections a real operator logged after a static SOP turned out to be "
    "wrong or incomplete, cited as [operator note on <alarm_tag>]. If an "
    "operator note addresses the same point as a static SOP section, the "
    "operator note is the current, field-verified guidance and takes "
    "priority over the static SOP - follow it, and say so. Cite every claim "
    "in the appropriate form. Do not hedge or discuss what the context does "
    "or does not cover.\n\n"
    "Only if NONE of the context is relevant to the question, respond with exactly "
    f"and only: '{NO_MATCH_PHRASE.capitalize()}.' Do not use outside knowledge, and "
    "do not mix this exact phrase into an otherwise-grounded answer."
)

# How much a fresh operator note's effective distance is reduced by, decaying
# by half every OPERATOR_NOTE_BOOST_HALFLIFE_HOURS. A note logged seconds ago
# gets nearly the full boost; a week-old note gets almost none - stale
# corrections shouldn't out-rank a static SOP forever.
OPERATOR_NOTE_BOOST_MAX = 0.5
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
    collection = get_sop_collection()
    embedding = _embedder.encode([note_text]).tolist()
    note_id = f"note-{alarm_tag}-{datetime.now(timezone.utc).isoformat()}"
    collection.upsert(
        ids=[note_id],
        documents=[note_text],
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
    collection = get_sop_collection()
    if collection.count() == 0:
        return []

    query_embedding = _embedder.encode([query]).tolist()
    n_results = min(max(top_k * 3, top_k), collection.count())
    results = collection.query(query_embeddings=query_embedding, n_results=n_results)

    hits = []
    for text, meta, distance in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
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

    Returns {answer, citations, no_match}.
    """
    chunks = retrieve(query, top_k=top_k)
    relevant_chunks = [c for c in chunks if c["distance"] <= RELEVANCE_DISTANCE_THRESHOLD]

    if not relevant_chunks:
        return {
            "answer": "No matching procedure found in the SOP knowledge base.",
            "citations": [],
            "no_match": True,
        }

    context = "\n\n".join(
        f"{_format_citation(c)}\n{c['text']}" for c in relevant_chunks
    )
    prompt = f"Context:\n{context}\n\nOperator question: {query}"

    answer = ollama_client.generate(prompt, system=SYSTEM_PROMPT)
    # Only treat as a true no-match if the phrase leads the answer, not if the
    # model mentions it in passing while still giving grounded content.
    no_match = answer.strip().lower().lstrip("'\"").startswith(NO_MATCH_PHRASE)

    citations = [] if no_match else sorted({_format_citation(c) for c in relevant_chunks})

    return {"answer": answer, "citations": citations, "no_match": no_match}
