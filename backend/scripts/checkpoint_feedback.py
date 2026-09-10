"""Self-improving feedback loop checkpoint: query an alarm type, show the
baseline static-SOP answer, add an operator correction note, repeat the same
query, and confirm the operator's note now wins over the static SOP.

Run from backend/: python scripts/checkpoint_feedback.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services import rag  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

ALARM_TAG = "LINE1.MTR_01.OVERLOAD"
QUERY = "Why did Motor_1 trip? What do I do right now?"
OPERATOR_NOTE = (
    "Field correction from the night shift, logged after two repeat trips: "
    "on Line 1, Motor_1 overload trips this week were NOT caused by a "
    "conveyor jam. The actual cause was a failing VFD cooling fan letting "
    "the drive overheat under normal load. Before inspecting the conveyor, "
    "check VFD internal temperature on the HMI - if it's elevated, this is "
    "the cooling fan issue, not a mechanical jam, and needs an electrical "
    "tech, not a mechanical clear."
)


def main():
    for sop_file in sorted((DATA_DIR / "sops").glob("SOP-*.md")):
        rag.ingest_sop_text(sop_file.read_text(encoding="utf-8"), source_name=sop_file.stem)

    print(f"Q: {QUERY}\n")

    before = rag.generate_answer(QUERY)
    print("--- BEFORE operator note ---")
    print(f"A: {before['answer']}")
    print(f"Citations: {before['citations']}")
    has_note_before = any("operator note" in c for c in before["citations"])

    print(f"\n--- Operator logs a correction for {ALARM_TAG} ---")
    print(f"Note: {OPERATOR_NOTE}\n")
    rag.add_operator_note(ALARM_TAG, OPERATOR_NOTE)

    after = rag.generate_answer(QUERY)
    print("--- AFTER operator note (same query) ---")
    print(f"A: {after['answer']}")
    print(f"Citations: {after['citations']}")
    has_note_after = any("operator note" in c for c in after["citations"])
    mentions_vfd_fan = "cooling fan" in after["answer"].lower() or "vfd" in after["answer"].lower()

    ok = (not has_note_before) and has_note_after and mentions_vfd_fan
    print(f"\nnote_absent_before={not has_note_before}  note_present_after={has_note_after}  "
          f"answer_reflects_note={mentions_vfd_fan}")
    print(f"\nCHECKPOINT {'PASS' if ok else 'FAIL'}")


if __name__ == "__main__":
    main()
