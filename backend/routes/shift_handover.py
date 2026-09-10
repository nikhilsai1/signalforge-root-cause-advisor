from fastapi import APIRouter

from models.schemas import ShiftHandoverRequest, ShiftHandoverResponse
from services import rag

router = APIRouter()


@router.post("/shift-handover", response_model=ShiftHandoverResponse)
def shift_handover(req: ShiftHandoverRequest):
    alarms = [a.model_dump() for a in req.alarms]
    result = rag.summarize_shift_handover(alarms, req.notes)
    return ShiftHandoverResponse(summary=result["summary"])
