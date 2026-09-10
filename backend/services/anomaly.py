import numpy as np
from sklearn.ensemble import IsolationForest


class IsolationForestDetector:
    """Flags anomalous sensor readings against a fitted baseline."""

    def __init__(self, contamination: float = 0.05, random_state: int = 42):
        self._model = IsolationForest(
            contamination=contamination, random_state=random_state
        )
        self._fitted = False

    def fit(self, baseline: list[dict]) -> None:
        """baseline: list of {tag, value} readings representing normal operation."""
        values = np.array([[r["value"]] for r in baseline])
        self._model.fit(values)
        self._fitted = True

    def flag(self, batch: list[dict]) -> list[dict]:
        """batch: list of {tag, value} readings to check.

        Returns one result per reading: {tag, value, score, is_anomaly}.
        """
        if not self._fitted:
            raise RuntimeError("Detector must be fit() on baseline data before flag()")

        values = np.array([[r["value"]] for r in batch])
        predictions = self._model.predict(values)  # -1 anomaly, 1 normal
        scores = self._model.decision_function(values)  # higher = more normal

        results = []
        for reading, pred, score in zip(batch, predictions, scores):
            results.append(
                {
                    "tag": reading["tag"],
                    "value": reading["value"],
                    "score": float(score),
                    "is_anomaly": bool(pred == -1),
                }
            )
        return results
