from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import LLMConfigurationError, service_unavailable
from app.db.session import get_session
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag_service import RAGService

router = APIRouter()


@router.post("/ask", response_model=ChatResponse)
async def ask_question(
    request: ChatRequest,
    session: AsyncSession = Depends(get_session),
) -> ChatResponse:
    try:
        return await RAGService(session).ask(
            question=request.question,
            top_k=request.top_k,
        )
    except LLMConfigurationError as exc:
        raise service_unavailable(str(exc)) from exc
