from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.core.security.dependencies import get_current_active_user
from app.core.security.tokens import decode_access_token
from app.repositories.user import UserRepository
from app.schemas.chat import (
    ChatConversationRead,
    ChatGroupCreate,
    ChatGroupMessageCreate,
    ChatGroupMessageRead,
    ChatGroupRead,
    ChatMessageCreate,
    ChatMessageRead,
)
from app.schemas.user import UserRead
from app.services.chat import ChatService, chat_connection_manager, get_chat_service
from app.services.notifications import NotificationService, get_notification_service

router = APIRouter()


@router.get("/conversations", response_model=list[ChatConversationRead])
def list_conversations(
    current_user: UserRead = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> list[ChatConversationRead]:
    return chat_service.list_conversations(current_user)


@router.get("/messages/{partner_id}", response_model=list[ChatMessageRead])
def list_messages(
    partner_id: UUID,
    current_user: UserRead = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> list[ChatMessageRead]:
    return chat_service.list_messages(partner_id, current_user)


@router.post("/messages", response_model=ChatMessageRead, status_code=status.HTTP_201_CREATED)
async def send_message(
    payload: ChatMessageCreate,
    current_user: UserRead = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service),
    notification_service: NotificationService = Depends(get_notification_service),
) -> ChatMessageRead:
    created = chat_service.send_message(payload, current_user)
    notification_service.create_chat_message_notification(
        created.recipient_id,
        sender_user_id=created.sender_id,
        sender_name=created.sender_name,
        message_text=created.content,
    )
    payload_json = {"type": "chat.message", "message": created.model_dump(mode="json")}
    await chat_connection_manager.send_to_user(created.recipient_id, payload_json)
    await chat_connection_manager.send_to_user(created.sender_id, payload_json)
    return created


@router.post("/messages/{partner_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_conversation_read(
    partner_id: UUID,
    current_user: UserRead = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> None:
    chat_service.mark_conversation_read(partner_id, current_user)
    await chat_connection_manager.send_to_user(
        partner_id,
        {
            "type": "chat.read",
            "partner_id": str(current_user.id),
            "read_by_id": str(current_user.id),
        },
    )


@router.get("/groups", response_model=list[ChatGroupRead])
def list_groups(
    current_user: UserRead = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> list[ChatGroupRead]:
    return chat_service.list_groups(current_user)


@router.post("/groups", response_model=ChatGroupRead, status_code=status.HTTP_201_CREATED)
def create_group(
    payload: ChatGroupCreate,
    current_user: UserRead = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatGroupRead:
    return chat_service.create_group(payload, current_user)


@router.get("/groups/{group_id}/messages", response_model=list[ChatGroupMessageRead])
def list_group_messages(
    group_id: UUID,
    current_user: UserRead = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> list[ChatGroupMessageRead]:
    return chat_service.list_group_messages(group_id, current_user)


@router.post("/groups/{group_id}/messages", response_model=ChatGroupMessageRead, status_code=status.HTTP_201_CREATED)
async def send_group_message(
    group_id: UUID,
    payload: ChatGroupMessageCreate,
    current_user: UserRead = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatGroupMessageRead:
    created = chat_service.send_group_message(group_id, payload, current_user)
    group = chat_service.list_groups(current_user)
    current_group = next((g for g in group if g.id == group_id), None)
    if current_group is not None:
        event_payload = {"type": "chat.group_message", "message": created.model_dump(mode="json")}
        for member_id in current_group.members:
            await chat_connection_manager.send_to_user(member_id, event_payload)
    return created


@router.websocket("/ws")
async def chat_ws(websocket: WebSocket, token: str = Query(...), db: Session = Depends(get_db)) -> None:
    try:
        payload = decode_access_token(token)
    except HTTPException:
        await websocket.close(code=4401)
        return

    user = UserRepository(db).get_by_id(UUID(payload.sub))
    if user is None or not user.is_active:
        await websocket.close(code=4401)
        return

    await chat_connection_manager.connect(user.id, websocket)
    try:
        while True:
            message = await websocket.receive_text()
            if message == "ping":
                await websocket.send_json({"type": "chat.pong"})
    except WebSocketDisconnect:
        chat_connection_manager.disconnect(user.id, websocket)
