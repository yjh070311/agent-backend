
"""公共依赖：从请求头解析当前登录用户。"""

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.utils.errors import UnauthorizedException
from app.utils.security import decode_access_token

BEARER_PREFIX = "Bearer "


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    """从 Authorization: Bearer <token> 解析出当前用户。"""
    if not authorization or not authorization.startswith(BEARER_PREFIX):
        raise UnauthorizedException("缺少 Authorization: Bearer <token> 请求头")

    token = authorization[len(BEARER_PREFIX):].strip()
    if not token:
        raise UnauthorizedException("令牌为空")

    user_id = decode_access_token(token)
    user = db.get(User, user_id)
    if user is None:
        raise UnauthorizedException("用户不存在")
    return user