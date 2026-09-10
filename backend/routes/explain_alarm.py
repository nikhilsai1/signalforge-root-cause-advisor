from fastapi import APIRouter

from models.schemas import ExplainAlarmRequest, RagAnswer
from services import rag

router = APIRouter()


@router.post("/explain-alarm", response_model=RagAnswer)
def explain_alarm(req: ExplainAlarmRequest):
    query = req.question or f"Why did {req.alarm_tag} trip and what should the operator do right now?"
    result = rag.generate_answer(query)
    return RagAnswer(**result)
