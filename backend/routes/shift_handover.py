from fastapi import APIRouter

from models.schemas import ShiftHandoverRequest, ShiftHandoverResponse

router = APIRouter()


@router.post("/shift-handover", response_model=ShiftHandoverResponse)
def shift_handover(req: ShiftHandoverRequest):
    # TODO(Phase 5): wire to services.ollama_client for a real summary
    return ShiftHandoverResponse(summary="not implemented yet")
