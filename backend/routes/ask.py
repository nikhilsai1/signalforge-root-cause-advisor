from fastapi import APIRouter

from models.schemas import AskRequest, RagAnswer
from services import rag

router = APIRouter()


@router.post("/ask", response_model=RagAnswer)
def ask(req: AskRequest):
    result = rag.generate_answer(req.question)
    return RagAnswer(**result)
