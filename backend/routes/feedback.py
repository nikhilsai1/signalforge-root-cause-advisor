from fastapi import APIRouter

from models.schemas import FeedbackRequest, FeedbackResponse

router = APIRouter()


@router.post("/feedback", response_model=FeedbackResponse)
def feedback(req: FeedbackRequest):
    # TODO(Phase 4): wire to services.rag.add_operator_note
    return FeedbackResponse(status="not implemented yet")
