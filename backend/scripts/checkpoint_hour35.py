"""Hour 3.5 checkpoint: feed the full real alarm flood + process data in,
confirm the pipeline correctly identifies "Motor_1 overload" as root cause
with a real SOP citation, and confirms motor_load_pct as the abnormal sensor.

Run from backend/: python scripts/checkpoint_hour35.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json  # noqa: E402

from services import alarm_flood, rag  # noqa: E402
from services.anomaly import IsolationForestDetector, flatten_process_readings  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

# The injected spike window in process_data.json (identified by inspection:
# motor_load_pct ramps from ~55% baseline to ~90% and back within this span).
SPIKE_START = "2026-09-10T14:31:30"
SPIKE_END = "2026-09-10T14:33:15"


def main():
    # 1. Ingest all real SOPs
    total_chunks = 0
    for sop_file in sorted((DATA_DIR / "sops").glob("SOP-*.md")):
        text = sop_file.read_text(encoding="utf-8")
        total_chunks += rag.ingest_sop_text(text, source_name=sop_file.stem)
    print(f"Ingested {total_chunks} SOP chunks total")

    # 2. Load real alarm flood
    alarms = json.loads((DATA_DIR / "alarm_flood.json").read_text())
    print(f"Loaded {len(alarms)} alarms")

    # 3. ISA-18.2 flood + root alarm detection
    flood = alarm_flood.detect_flood(alarms)
    print(f"\nis_flood: {flood['is_flood']}")
    root_alarm = flood["root_alarm"]
    print(f"root_alarm: {root_alarm['tag']} - {root_alarm.get('description')}")
    print(f"suppressed: {len(flood['suppressed'])} alarms")

    # 4. RAG query grounded on the root alarm
    root_desc = root_alarm.get("description") or root_alarm["tag"]
    query = f"Why did {root_desc} ({root_alarm['tag']}) occur? What should the operator do right now?"
    cause = rag.generate_answer(query)
    print(f"\nQ: {query}")
    print(f"A: {cause['answer']}")
    print(f"Citations: {cause['citations']}")

    # 5. Anomaly detection: baseline (outside spike window) vs batch (inside it)
    process_data = json.loads((DATA_DIR / "process_data.json").read_text())
    baseline_rows = [r for r in process_data if not (SPIKE_START <= r["timestamp"] <= SPIKE_END)]
    spike_rows = [r for r in process_data if SPIKE_START <= r["timestamp"] <= SPIKE_END]

    detector = IsolationForestDetector()
    detector.fit(flatten_process_readings(baseline_rows))
    anomaly_results = detector.flag(flatten_process_readings(spike_rows))

    by_tag = {}
    for r in anomaly_results:
        by_tag.setdefault(r["tag"], []).append(r["is_anomaly"])
    print("\nAnomaly confirmation (fraction flagged anomalous, spike window):")
    for tag, flags in by_tag.items():
        print(f"  {tag}: {sum(flags)}/{len(flags)}")

    most_anomalous_tag = max(by_tag, key=lambda t: sum(by_tag[t]) / len(by_tag[t]))

    # --- Checkpoint pass/fail ---
    root_ok = "MTR_01" in root_alarm["tag"] and "overload" in (root_alarm.get("description") or "").lower()
    citation_ok = any("SOP-14" in c for c in cause["citations"])
    anomaly_ok = "motor_load_pct" in most_anomalous_tag
    ok = root_ok and citation_ok and anomaly_ok and flood["is_flood"]

    print(f"\nroot_ok={root_ok}  citation_ok={citation_ok}  anomaly_ok={anomaly_ok} (most anomalous: {most_anomalous_tag})")
    print(f"\nCHECKPOINT {'PASS' if ok else 'FAIL'}")


if __name__ == "__main__":
    main()
