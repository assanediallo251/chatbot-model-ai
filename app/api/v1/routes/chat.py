from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    LLMConfigurationError,
    LLMRateLimitError,
    LLMTransientError,
    service_unavailable,
    too_many_requests,
)
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
    except LLMRateLimitError as exc:
        raise too_many_requests(str(exc)) from exc
    except LLMTransientError as exc:
        raise service_unavailable(str(exc)) from exc
