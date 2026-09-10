from fastapi import APIRouter

from models.schemas import FeedbackRequest, FeedbackResponse
from services import rag

router = APIRouter()


@router.post("/feedback", response_model=FeedbackResponse)
def feedback(req: FeedbackRequest):
    rag.add_operator_note(req.alarm_tag, req.note)
    return FeedbackResponse(status="stored")
