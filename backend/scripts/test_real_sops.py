"""Ad-hoc test: ingest ALL real SOPs from data/sops/ and ask real questions.
Not a formal checkpoint script - just verifying the pipeline against Mahesh's
actual deliverable instead of the throwaway fixture.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services import rag  # noqa: E402

SOPS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "sops"

QUESTIONS = [
    "LINE1.MTR_01.OVERLOAD just fired and motor_load_pct was trending above 90%. What do I do right now?",
    "A VFD current high alarm fired but motor load was normal before the trip. What should I do?",
    "Why is Pump_07 showing a cavitation alarm?",  # expect no_match - not in any SOP
]


def main():
    total_chunks = 0
    for sop_file in sorted(SOPS_DIR.glob("SOP-*.md")):
        text = sop_file.read_text(encoding="utf-8")
        n = rag.ingest_sop_text(text, source_name=sop_file.stem)
        print(f"Ingested {n} chunks from {sop_file.stem}")
        total_chunks += n
    print(f"\nTotal chunks ingested: {total_chunks}\n")

    for q in QUESTIONS:
        result = rag.generate_answer(q)
        print(f"Q: {q}")
        print(f"A: {result['answer']}")
        print(f"Citations: {result['citations']}")
        print(f"No match: {result['no_match']}")
        print()


if __name__ == "__main__":
    main()
