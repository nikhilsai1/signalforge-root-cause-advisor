from collections import defaultdict

import numpy as np
from sklearn.ensemble import IsolationForest


class IsolationForestDetector:
    """Flags anomalous sensor readings against a fitted baseline.

    Fits one IsolationForest per distinct tag, since different sensors
    (temperature, pressure, motor load %, ...) have unrelated scales and
    distributions and must not be mixed into a single model.
    """

    def __init__(self, contamination: float = 0.1, random_state: int = 42):
        self._contamination = contamination
        self._random_state = random_state
        self._models: dict[str, IsolationForest] = {}

    def fit(self, baseline: list[dict]) -> None:
        """baseline: list of {tag, value} readings representing normal operation."""
        by_tag = defaultdict(list)
        for r in baseline:
            by_tag[r["tag"]].append(r["value"])

        for tag, values in by_tag.items():
            model = IsolationForest(
                contamination=self._contamination, random_state=self._random_state
            )
            model.fit(np.array(values).reshape(-1, 1))
            self._models[tag] = model

    def flag(self, batch: list[dict]) -> list[dict]:
        """batch: list of {tag, value} readings to check.

        Returns one result per reading with a fitted model for its tag:
        {tag, value, score, is_anomaly}. Readings for a tag with no
        baseline are skipped (no model to score them against).
        """
        if not self._models:
            raise RuntimeError("Detector must be fit() on baseline data before flag()")

        results = []
        for reading in batch:
            tag, value = reading["tag"], reading["value"]
            model = self._models.get(tag)
            if model is None:
                continue

            x = np.array([[value]])
            pred = model.predict(x)[0]  # -1 anomaly, 1 normal
            score = model.decision_function(x)[0]  # higher = more normal

            results.append(
                {
                    "tag": tag,
                    "value": value,
                    "score": float(score),
                    "is_anomaly": bool(pred == -1),
                }
            )
        return results


def flatten_process_readings(
    rows: list[dict], metrics: tuple[str, ...] = ("temperature", "pressure", "motor_load_pct")
) -> list[dict]:
    """Adapt multi-metric process-data rows (one row per equipment+timestamp,
    with several sensor columns) into the flat {tag, timestamp, value} shape
    IsolationForestDetector expects - one entry per (equipment, metric).

    e.g. {"equipment": "MTR_01", "temperature": 61.8, "motor_load_pct": 54.7, ...}
    becomes {"tag": "MTR_01.temperature", "value": 61.8, ...} and
            {"tag": "MTR_01.motor_load_pct", "value": 54.7, ...}
    """
    flat = []
    for row in rows:
        for metric in metrics:
            if metric not in row:
                continue
            flat.append(
                {
                    "tag": f"{row['equipment']}.{metric}",
                    "timestamp": row.get("timestamp"),
                    "value": row[metric],
                }
            )
    return flat
