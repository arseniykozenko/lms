from collections import defaultdict
from uuid import UUID

from fastapi import Depends, HTTPException, WebSocket
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.models.chat_group import ChatGroup, ChatGroupMember, ChatGroupMessage
from app.models.chat_message import ChatMessage
from app.models.course_collaborator import CourseCollaboratorStatus
from app.models.user import UserRole
from app.repositories.chat import ChatRepository
from app.repositories.chat_group import ChatGroupRepository
from app.repositories.course import CourseRepository
from app.repositories.course_collaborator import CourseCollaboratorRepository
from app.repositories.enrollment import EnrollmentRepository
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


class ChatConnectionManager:
    def __init__(self) -> None:
        self.connections: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, user_id: UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections[str(user_id)].append(websocket)

    def disconnect(self, user_id: UUID, websocket: WebSocket) -> None:
        key = str(user_id)
        sockets = self.connections.get(key, [])
        if websocket in sockets:
            sockets.remove(websocket)
        if not sockets and key in self.connections:
            del self.connections[key]

    async def send_to_user(self, user_id: UUID, payload: dict) -> None:
        for socket in list(self.connections.get(str(user_id), [])):
            await socket.send_json(payload)


chat_connection_manager = ChatConnectionManager()


class ChatService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.messages = ChatRepository(db)
        self.group_chats = ChatGroupRepository(db)
        self.users = UserRepository(db)
        self.courses = CourseRepository(db)
        self.collaborators = CourseCollaboratorRepository(db)
        self.enrollments = EnrollmentRepository(db)

    def list_conversations(self, current_user: UserRead) -> list[ChatConversationRead]:
        available_partners = self._available_partners(current_user)
        messages = self.messages.list_for_user(current_user.id)
        unread_by_partner: dict[UUID, int] = defaultdict(int)
        last_message_by_partner: dict[UUID, ChatMessage] = {}

        for message in messages:
            partner_id = message.recipient_id if message.sender_id == current_user.id else message.sender_id
            if message.recipient_id == current_user.id and not message.is_read:
                unread_by_partner[partner_id] += 1
            if partner_id not in last_message_by_partner:
                last_message_by_partner[partner_id] = message

        conversations: list[ChatConversationRead] = []
        for partner_id, payload in available_partners.items():
            last_message = last_message_by_partner.get(partner_id)
            conversations.append(
                ChatConversationRead(
                    partner_id=partner_id,
                    partner_name=payload["name"],
                    partner_profile_photo_url=payload["profile_photo_url"],
                    partner_email=payload["email"],
                    partner_role=payload["role"].value,
                    course_id=payload["course_id"],
                    course_title=payload["course_title"],
                    unread_count=unread_by_partner.get(partner_id, 0),
                    last_message=last_message.content if last_message is not None else None,
                    last_message_at=last_message.created_at if last_message is not None else None,
                )
            )

        conversations.sort(
            key=lambda item: (
                item.last_message_at or self._min_datetime(),
                item.unread_count,
            ),
            reverse=True,
        )
        return conversations

    def list_messages(self, partner_id: UUID, current_user: UserRead, *, limit: int = 100) -> list[ChatMessageRead]:
        partner = self.users.get_by_id(partner_id)
        if partner is None:
            raise HTTPException(status_code=404, detail="Chat partner not found")
        if not self._can_chat(current_user, UserRead.model_validate(partner)):
            raise HTTPException(status_code=403, detail="Chat is not available with this user")

        items = self.messages.list_for_pair(current_user.id, partner_id, limit=limit)
        items.reverse()
        return [self._to_message_read(item) for item in items]

    def send_message(self, payload: ChatMessageCreate, current_user: UserRead) -> ChatMessageRead:
        partner = self.users.get_by_id(payload.recipient_id)
        if partner is None:
            raise HTTPException(status_code=404, detail="Chat partner not found")
        partner_read = UserRead.model_validate(partner)
        if not self._can_chat(current_user, partner_read):
            raise HTTPException(status_code=403, detail="Chat is not available with this user")

        shared_course = self._pick_shared_course(current_user, partner_read)
        message = ChatMessage(
            sender_id=current_user.id,
            recipient_id=partner.id,
            course_id=shared_course.id if shared_course is not None else None,
            content=payload.content.strip(),
        )
        if not message.content:
            raise HTTPException(status_code=422, detail="Message cannot be empty")
        self.messages.create(message)
        self.db.commit()
        self.db.refresh(message)
        return self._to_message_read(message)

    def mark_conversation_read(self, partner_id: UUID, current_user: UserRead) -> None:
        self.messages.mark_read_for_pair(current_user.id, partner_id)
        self.db.commit()

    def create_group(self, payload: ChatGroupCreate, current_user: UserRead) -> ChatGroupRead:
        if current_user.role not in {UserRole.TEACHER, UserRole.ADMIN}:
            raise HTTPException(status_code=403, detail="Only teachers can create group chats")

        member_ids = set(payload.member_ids)
        member_ids.add(current_user.id)
        resolved_members = []
        for user_id in member_ids:
            user = self.users.get_by_id(user_id)
            if user is None:
                raise HTTPException(status_code=404, detail=f"User {user_id} not found")
            user_read = UserRead.model_validate(user)
            if user_id != current_user.id and not self._can_chat(current_user, user_read):
                raise HTTPException(status_code=403, detail="One or more users are not available for teacher chat")
            resolved_members.append(user)

        group = ChatGroup(title=payload.title.strip(), created_by_user_id=current_user.id)
        if not group.title:
            raise HTTPException(status_code=422, detail="Group title cannot be empty")
        self.group_chats.create_group(group)
        for member in resolved_members:
            self.group_chats.create_member(ChatGroupMember(group_id=group.id, user_id=member.id))

        self.db.commit()
        self.db.refresh(group)
        return self._to_group_read(group)

    def list_groups(self, current_user: UserRead) -> list[ChatGroupRead]:
        return [self._to_group_read(item) for item in self.group_chats.list_groups_for_user(current_user.id)]

    def list_group_messages(self, group_id: UUID, current_user: UserRead, *, limit: int = 100) -> list[ChatGroupMessageRead]:
        group = self.group_chats.get_group_for_user(group_id, current_user.id)
        if group is None:
            raise HTTPException(status_code=404, detail="Group not found")
        items = self.group_chats.list_messages(group.id, limit=limit)
        items.reverse()
        return [self._to_group_message_read(item) for item in items]

    def send_group_message(self, group_id: UUID, payload: ChatGroupMessageCreate, current_user: UserRead) -> ChatGroupMessageRead:
        group = self.group_chats.get_group_for_user(group_id, current_user.id)
        if group is None:
            raise HTTPException(status_code=404, detail="Group not found")

        content = payload.content.strip()
        if not content:
            raise HTTPException(status_code=422, detail="Message cannot be empty")

        item = ChatGroupMessage(group_id=group.id, sender_id=current_user.id, content=content)
        self.group_chats.create_message(item)
        self.db.commit()
        self.db.refresh(item)
        return self._to_group_message_read(item)

    def _available_partners(self, current_user: UserRead) -> dict[UUID, dict]:
        partners: dict[UUID, dict] = {}
        if current_user.role == UserRole.STUDENT:
            for enrollment in self.enrollments.list_by_user(current_user.id):
                teacher_ids = {enrollment.course.author_id}
                teacher_ids.update(
                    item.user_id
                    for item in self.collaborators.list_by_course(
                        enrollment.course_id, status=CourseCollaboratorStatus.ACCEPTED
                    )
                )
                for teacher_id in teacher_ids:
                    teacher = self.users.get_by_id(teacher_id)
                    if teacher is None or teacher.id == current_user.id:
                        continue
                    partners[teacher.id] = {
                        "name": teacher.display_name,
                        "profile_photo_url": teacher.profile_photo_url,
                        "email": teacher.email,
                        "role": teacher.role,
                        "course_id": enrollment.course_id,
                        "course_title": enrollment.course.title,
                    }
            return partners

        if current_user.role in {UserRole.TEACHER, UserRole.ADMIN}:
            owned_courses = self.courses.list_by_author(current_user.id)
            collaboration_courses = [
                invite.course
                for invite in self.collaborators.list_by_user(current_user.id, status=CourseCollaboratorStatus.ACCEPTED)
                if invite.course is not None
            ]
            for course in [*owned_courses, *collaboration_courses]:
                for enrollment in self.enrollments.list_by_course(course.id):
                    student = enrollment.user
                    if student.id == current_user.id:
                        continue
                    partners[student.id] = {
                        "name": student.display_name,
                        "profile_photo_url": student.profile_photo_url,
                        "email": student.email,
                        "role": student.role,
                        "course_id": course.id,
                        "course_title": course.title,
                    }
                teacher_ids = {course.author_id}
                teacher_ids.update(
                    item.user_id
                    for item in self.collaborators.list_by_course(course.id, status=CourseCollaboratorStatus.ACCEPTED)
                )
                for teacher_id in teacher_ids:
                    if teacher_id == current_user.id:
                        continue
                    teacher = self.users.get_by_id(teacher_id)
                    if teacher is None:
                        continue
                    partners[teacher.id] = {
                        "name": teacher.display_name,
                        "profile_photo_url": teacher.profile_photo_url,
                        "email": teacher.email,
                        "role": teacher.role,
                        "course_id": course.id,
                        "course_title": course.title,
                    }
        return partners

    def _can_chat(self, current_user: UserRead, partner: UserRead) -> bool:
        if current_user.id == partner.id:
            return False
        if current_user.role == UserRole.STUDENT:
            return partner.id in self._available_partners(current_user)
        if current_user.role in {UserRole.TEACHER, UserRole.ADMIN}:
            return partner.id in self._available_partners(current_user)
        return False

    def _pick_shared_course(self, current_user: UserRead, partner: UserRead):
        available = self._available_partners(current_user)
        course_id = available.get(partner.id, {}).get("course_id")
        if course_id is None:
            return None
        return self.courses.get_by_id(course_id)

    def _to_message_read(self, message: ChatMessage) -> ChatMessageRead:
        sender_name = message.sender.display_name
        recipient_name = message.recipient.display_name
        return ChatMessageRead(
            id=message.id,
            sender_id=message.sender_id,
            recipient_id=message.recipient_id,
            sender_name=sender_name,
            sender_profile_photo_url=message.sender.profile_photo_url,
            recipient_name=recipient_name,
            recipient_profile_photo_url=message.recipient.profile_photo_url,
            content=message.content,
            is_read=message.is_read,
            read_at=message.read_at,
            created_at=message.created_at,
            course_id=message.course_id,
            course_title=message.course.title if message.course is not None else None,
        )

    def _to_group_read(self, item: ChatGroup) -> ChatGroupRead:
        return ChatGroupRead(
            id=item.id,
            title=item.title,
            created_by_user_id=item.created_by_user_id,
            members=[m.user_id for m in item.members],
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    def _to_group_message_read(self, item: ChatGroupMessage) -> ChatGroupMessageRead:
        return ChatGroupMessageRead(
            id=item.id,
            group_id=item.group_id,
            sender_id=item.sender_id,
            sender_name=item.sender.display_name,
            sender_profile_photo_url=item.sender.profile_photo_url,
            content=item.content,
            created_at=item.created_at,
        )

    def _min_datetime(self):
        from datetime import UTC, datetime

        return datetime.min.replace(tzinfo=UTC)


def get_chat_service(db: Session = Depends(get_db)) -> ChatService:
    return ChatService(db)
