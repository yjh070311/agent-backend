"""
处理会话的CRUD操作
"""

from fastapi import APIRouter,Depends,HTTPException,Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Conversation,User

from app.schemas.conversation import ConversationCreate,ConversationOut,ConversationUpdate
from app.utils.response import ApiResponse,PaginatedData
from app.utils.deps import get_current_user

router=APIRouter(prefix="/conversation",tags=["会话"])

@router.get("",response_model=ApiResponse[PaginatedData[ConversationOut]])
async def list_conversation(
    limit:int=Query(default=20,ge=1,le=100),
    offset:int=Query(default=0,ge=0),
    db:Session=Depends(get_db),  #获得数据库对话
):

    total=db.query(Conversation).count()    #查询数据库对应的Conversation部分

    items=(db.query(Conversation)
           .order_by(Conversation.created_at.desc())
           .offset(offset)
           .limit(limit)
           .all()
           
           )

    return ApiResponse.success(data=PaginatedData(limit=limit,offset=offset,items=items,total=total))   #返回查询结果

@router.post("",response_model=ApiResponse[ConversationOut],status_code=201)
async def create_conversation(
    payload:ConversationCreate,
    db:Session=Depends(get_db), #depends只在函数签名默认值，被调用才执行
    user:User=Depends(get_current_user)
):
    conversation=Conversation(
        user_id=user.id,
        title=payload.title,
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return ApiResponse.success(data=conversation)


@router.get("/{conversation_id}",response_model=ApiResponse[ConversationOut])
async def get_conversation(
    conversation_id:int,
    db:Session=Depends(get_db),
):
    conversation=db.query(Conversation).filter(Conversation.id==conversation_id).first()

    if conversation is None:
        raise HTTPException(status_code=404,detail="不存在")

    return ApiResponse.success(data=conversation)

@router.patch("/{conversation_id}",response_model=ApiResponse[ConversationOut])
async def update_conversation(
    conversation_id:int,
    payload:ConversationUpdate,
    db:Session=Depends(get_db)
):
    conversation=db.query(Conversation).filter(Conversation.id==conversation_id).first()
    if conversation is None:
        raise HTTPException(status_code=404,detail="不存在")

    update_data=payload.model_dump(exclude_unset=True)  #只更新传入的字段
    for key,value in update_data.items():
        setattr(conversation,key,value)

    db.commit()
    db.refresh(conversation)

    return ApiResponse.success(data=conversation)


@router.delete("/{conversation_id}",status_code=204)
async def delete_conversation(
    conversation_id:int,
    db:Session=Depends(get_db)
):
    conversation=db.query(Conversation).filter(Conversation.id==conversation_id).first()
    if conversation is None:
        raise HTTPException(status_code=404,detail="不存在")

    db.delete(conversation)
    db.commit()

    return None