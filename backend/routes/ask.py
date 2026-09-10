from fastapi import APIRouter

from models.schemas import AskRequest, RagAnswer

router = APIRouter()


@router.post("/ask", response_model=RagAnswer)
def ask(req: AskRequest):
    # TODO(Phase 5): wire to services.rag.generate_answer
    return RagAnswer(answer="not implemented yet", citations=[], no_match=True)
