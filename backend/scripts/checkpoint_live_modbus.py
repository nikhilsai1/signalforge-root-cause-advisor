"""Checkpoint (Hour 3.5): confirm real Modbus data can substitute for/
supplement Mahesh's synthetic process data - i.e. a detector trained purely
on data/process_data.json can meaningfully score a live reading pulled
through Manjunath's Modbus bridge.

Requires integration/modbus_sim_server.py and integration/telemetry_bridge.py
already running (or data/live_telemetry.json already populated by them).

Run from backend/: python scripts/checkpoint_live_modbus.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.anomaly import (  # noqa: E402
    IsolationForestDetector,
    flatten_live_telemetry,
    flatten_process_readings,
)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
SPIKE_START, SPIKE_END = "2026-09-10T14:31:30", "2026-09-10T14:33:15"


def main():
    live_path = DATA_DIR / "live_telemetry.json"
    if not live_path.exists():
        print("FAIL: data/live_telemetry.json not found - start "
              "integration/modbus_sim_server.py and telemetry_bridge.py first.")
        sys.exit(1)

    process_data = json.loads((DATA_DIR / "process_data.json").read_text())
    baseline_rows = [r for r in process_data if not (SPIKE_START <= r["timestamp"] <= SPIKE_END)]

    detector = IsolationForestDetector()
    detector.fit(flatten_process_readings(baseline_rows))
    print(f"Trained on {len(baseline_rows)} baseline rows from Mahesh's process_data.json")

    live_reading = json.loads(live_path.read_text())
    print(f"\nLive Modbus reading: {live_reading}")

    live_flat = flatten_live_telemetry(live_reading)
    results = detector.flag(live_flat)

    print("\nScored against synthetic-data-trained baseline:")
    for r in results:
        print(f"  {r['tag']}: value={r['value']}  score={r['score']:.3f}  is_anomaly={r['is_anomaly']}")

    scored_tags = {r["tag"] for r in results}
    ok = len(results) > 0 and scored_tags <= {"MTR_01.motor_load_pct", "MTR_01.temperature", "MTR_01.tank_level_pct"}
    print(f"\nCHECKPOINT {'PASS' if ok else 'FAIL'}: real Modbus data scored "
          f"{len(results)} readings against Mahesh's synthetic baseline")


if __name__ == "__main__":
    main()
