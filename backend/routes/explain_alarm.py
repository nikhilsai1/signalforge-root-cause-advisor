from fastapi import APIRouter

from models.schemas import ExplainAlarmRequest, RagAnswer

router = APIRouter()


@router.post("/explain-alarm", response_model=RagAnswer)
def explain_alarm(req: ExplainAlarmRequest):
    # TODO(Phase 2): wire to services.rag.generate_answer
    return RagAnswer(answer="not implemented yet", citations=[], no_match=True)
