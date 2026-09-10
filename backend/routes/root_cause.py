from fastapi import APIRouter

from models.schemas import (
    AlarmItem,
    AnomalyResult,
    RagAnswer,
    RootCauseRequest,
    RootCauseResponse,
)
from services import alarm_flood, rag
from services.anomaly import IsolationForestDetector

router = APIRouter()


@router.post("/root-cause", response_model=RootCauseResponse)
def root_cause(req: RootCauseRequest):
    alarms = [a.model_dump() for a in req.alarms]
    flood = alarm_flood.detect_flood(alarms)

    if not flood["is_flood"]:
        return RootCauseResponse(
            is_flood=False,
            root_alarm=None,
            suppressed_count=0,
            cause=RagAnswer(
                answer="No alarm flood detected (fewer than 10 alarms in any 10-minute window).",
                citations=[],
                no_match=True,
            ),
            anomaly_confirmation=[],
        )

    root_alarm = flood["root_alarm"]
    root_desc = root_alarm.get("description") or root_alarm["tag"]
    query = f"Why did {root_desc} ({root_alarm['tag']}) occur? What should the operator do right now?"
    cause = rag.generate_answer(query)

    anomaly_confirmation = []
    if req.sensor_baseline and req.sensor_batch:
        detector = IsolationForestDetector()
        detector.fit([r.model_dump() for r in req.sensor_baseline])
        anomaly_confirmation = detector.flag([r.model_dump() for r in req.sensor_batch])

    return RootCauseResponse(
        is_flood=True,
        root_alarm=AlarmItem(**root_alarm),
        suppressed_count=len(flood["suppressed"]),
        cause=RagAnswer(**cause),
        anomaly_confirmation=[AnomalyResult(**a) for a in anomaly_confirmation],
    )
