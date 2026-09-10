from fastapi import APIRouter

from models.schemas import RagAnswer, RootCauseRequest, RootCauseResponse

router = APIRouter()


@router.post("/root-cause", response_model=RootCauseResponse)
def root_cause(req: RootCauseRequest):
    # TODO(Phase 3): wire to services.alarm_flood + services.rag + services.anomaly
    return RootCauseResponse(
        is_flood=False,
        root_alarm=None,
        suppressed_count=0,
        cause=RagAnswer(answer="not implemented yet", citations=[], no_match=True),
        anomaly_confirmation=[],
    )
