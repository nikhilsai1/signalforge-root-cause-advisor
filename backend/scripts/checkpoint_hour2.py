"""Hour 2 checkpoint: ingest a fake SOP, ask a question, confirm a grounded,
cited answer comes back (not a hallucination, not a crash).

Run from backend/: python scripts/checkpoint_hour2.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services import rag  # noqa: E402

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "fake_sop.txt"


def main():
    text = FIXTURE_PATH.read_text()
    n_chunks = rag.ingest_sop_text(text, source_name="SOP-14")
    print(f"Ingested {n_chunks} chunks from SOP-14")

    question = "Why did Motor_1 trip? What do I do right now?"
    result = rag.generate_answer(question)

    print(f"\nQ: {question}")
    print(f"A: {result['answer']}")
    print(f"Citations: {result['citations']}")
    print(f"No match: {result['no_match']}")

    ok = (not result["no_match"]) and len(result["citations"]) > 0
    print(f"\nCHECKPOINT {'PASS' if ok else 'FAIL'}")


if __name__ == "__main__":
    main()
