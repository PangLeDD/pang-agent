from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.conversation_service import ConversationService
from app.core.database import get_session
from app.core.response import success
from app.core.security import get_current_user
from app.schemas.conversation import ConversationMessageResponse, ConversationResponse

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("")
async def list_conversations(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[dict[str, str], Depends(get_current_user)],
):
    conversations = await ConversationService(session).list_conversations(current_user["id"])
    return success([ConversationResponse.model_validate(c).model_dump(mode="json") for c in conversations])


@router.get("/{conversation_id}/messages")
async def list_messages(
    conversation_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[dict[str, str], Depends(get_current_user)],
):
    messages = await ConversationService(session).list_messages(conversation_id, current_user["id"])
    return success([ConversationMessageResponse.model_validate(m).model_dump(mode="json") for m in messages])
