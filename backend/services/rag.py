import re

from sentence_transformers import SentenceTransformer

from services.chroma_client import get_sop_collection
from services.ollama_client import ollama_client

_embedder = SentenceTransformer("all-MiniLM-L6-v2")

_SECTION_RE = re.compile(r"^#\s*(\d+)\s*$", re.MULTILINE)

NO_MATCH_PHRASE = "no matching procedure found"

SYSTEM_PROMPT = (
    "You are an industrial operations assistant. Answer the operator's question "
    "using ONLY the SOP context provided below. For every claim, cite the section "
    "it came from in the form [source §section]. If the context does not contain "
    "an answer to the question, respond with exactly: "
    f"'{NO_MATCH_PHRASE.capitalize()}.' Do not use outside knowledge."
)


def chunk_sop(text: str, source_name: str) -> list[dict]:
    """Split a plain-text SOP into numbered sections.

    Sections are marked by a line containing only '# <n>' (e.g. '# 3').
    Returns a list of {source, section, text} dicts, one per section.
    """
    matches = list(_SECTION_RE.finditer(text))
    chunks = []
    for i, m in enumerate(matches):
        section = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
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


def retrieve(query: str, top_k: int = 3) -> list[dict]:
    """Embed the query and return the top_k most relevant chunks."""
    collection = get_sop_collection()
    if collection.count() == 0:
        return []

    query_embedding = _embedder.encode([query]).tolist()
    n_results = min(top_k, collection.count())
    results = collection.query(query_embeddings=query_embedding, n_results=n_results)

    hits = []
    for text, meta, distance in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        hits.append({**meta, "text": text, "distance": distance})
    return hits


def _format_citation(chunk: dict) -> str:
    if chunk.get("type") == "operator_note":
        return f"[operator note on {chunk['alarm_tag']}]"
    return f"[{chunk['source']} §{chunk['section']}]"


def generate_answer(query: str, top_k: int = 3) -> dict:
    """Retrieve grounding context and generate a cited, grounded answer.

    Returns {answer, citations, no_match}.
    """
    chunks = retrieve(query, top_k=top_k)
    if not chunks:
        return {
            "answer": "No matching procedure found in the SOP knowledge base.",
            "citations": [],
            "no_match": True,
        }

    context = "\n\n".join(
        f"{_format_citation(c)}\n{c['text']}" for c in chunks
    )
    prompt = f"Context:\n{context}\n\nOperator question: {query}"

    answer = ollama_client.generate(prompt, system=SYSTEM_PROMPT)
    no_match = NO_MATCH_PHRASE in answer.lower()

    citations = [] if no_match else sorted({_format_citation(c) for c in chunks})

    return {"answer": answer, "citations": citations, "no_match": no_match}
