
"""处理会话的 CRUD 操作。

统一约定：越权一律返回 404 而不是 403，避免泄露资源是否存在。
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Conversation, User
from app.schemas.conversation import (
    ConversationCreate,
    ConversationOut,
    ConversationUpdate,
)
from app.utils.deps import get_current_user
from app.utils.errors import BusinessException,NotFoundException
from app.utils.response import ApiResponse, PaginatedData

router = APIRouter(prefix="/conversation", tags=["会话"])


def get_owned_conversation(conversation_id: int, db: Session) -> Conversation:
    """取出会话，取不到就 404。"""
    conversation = (
        db.query(Conversation).filter(Conversation.id == conversation_id).one_or_none()
    )
    if conversation is None:
        raise NotFoundException("会话不存在")
    return conversation


@router.get("", response_model=ApiResponse[PaginatedData[ConversationOut]])
async def list_conversation(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> ApiResponse[PaginatedData[ConversationOut]]:
    """会话列表。"""
    base = db.query(Conversation)
    items = (
        base.order_by(Conversation.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return ApiResponse.success(
        data=PaginatedData(
            limit=limit,
            offset=offset,
            items=[ConversationOut.model_validate(item) for item in items],
            total=base.count(),
        )
    )


@router.post("", response_model=ApiResponse[ConversationOut], status_code=201)
async def create_conversation(
    payload: ConversationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[ConversationOut]:
    """创建会话。"""
    conversation = Conversation(user_id=user.id, title=payload.title)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return ApiResponse.success(data=ConversationOut.model_validate(conversation))


@router.get("/{conversation_id}", response_model=ApiResponse[ConversationOut])
async def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
) -> ApiResponse[ConversationOut]:
    """会话详情。"""
    conversation = get_owned_conversation(conversation_id, db)
    return ApiResponse.success(data=ConversationOut.model_validate(conversation))


@router.patch("/{conversation_id}", response_model=ApiResponse[ConversationOut])
async def update_conversation(
    conversation_id: int,
    payload: ConversationUpdate,
    db: Session = Depends(get_db),
) -> ApiResponse[ConversationOut]:
    """只更新客户端真正传过来的字段。"""
    conversation = get_owned_conversation(conversation_id, db)

    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise BusinessException(code=40001, message="没有需要更新的字段")

    for field, value in changes.items():
        setattr(conversation, field, value)

    db.commit()
    db.refresh(conversation)
    return ApiResponse.success(data=ConversationOut.model_validate(conversation))


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
) -> None:
    """删除会话，级联删除消息。"""
    conversation = get_owned_conversation(conversation_id, db)
    db.delete(conversation)
    db.commit()