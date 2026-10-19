"""认证路由"""

from fastapi import APIRouter,Depends

from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserOut
from app.utils.errors import ConflictException, UnauthorizedException
from app.utils.response import ApiResponse
from app.utils.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth",tags=["认证"])

@router.post("/register",response_model=ApiResponse[UserOut],status_code=201)
async def register(payload:RegisterRequest,db:Session=Depends(get_db))->ApiResponse[UserOut]:
    """注册。用户名唯一，密码只存哈希。"""
    exists = db.query(User).filter(User.username == payload.username).one_or_none()
    if exists is not None:
        raise ConflictException("用户名已被注册")

    user = User(username=payload.username, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return ApiResponse.success(data=UserOut.model_validate(user))


@router.post("/login", response_model=ApiResponse[TokenResponse])
async def login(payload: LoginRequest, db: Session = Depends(get_db)) -> ApiResponse[TokenResponse]:
    """登录换 token。

    「用户名不存在」和「密码错误」返回同一句提示：
    分开提示的话，攻击者能用这个接口枚举出哪些用户名已注册。
    """
    user = db.query(User).filter(User.username == payload.username).one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise UnauthorizedException("用户名或密码错误")

    token = create_access_token(user.id)
    return ApiResponse.success(
        data=TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
    )