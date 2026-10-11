"""消息的分页查询"""

from fastapi import APIRouter,Query,Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.message import MessageOut
from app.models import Message

from app.utils.response import ApiResponse,PaginatedData

router=APIRouter(prefix="/conversation/{conversation_id}/message"tags=["消息"])

@router.get("",response_model=ApiResponse[PaginatedData[MessageOut]])
async def list_message(
    conversation_id:int,
    limit:int=Query(default=20,ge=1,le=100),
    offset:int=Query(default=0,ge=0),
    db:Session=Depends(get_db)
):
    query_base=db.query(Message).filter(Message.conversation_id==conversation_id).first()
    total=query_base.count()

    items=(
        query_base
        .order_by(Message.created_at.asc())
        .limit(limit)
        .offset(offset)
        .all
    )

    return ApiResponse.success(data=PaginatedData(items=items,total=total,limit=limit,offset=offset,))
