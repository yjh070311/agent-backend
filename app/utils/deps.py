"""公共依赖：Week 2 临时当前用户，Day 13 会换成真正的 JWT 认证。"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User

DEMO_USERNAME = "demo"


def get_current_user(db: Session = Depends(get_db)) -> User:
    """返回当前登录用户（临时版：固定返回演示用户）。"""
    user = db.query(User).filter(User.username == DEMO_USERNAME).one_or_none()
    if user is None:
        
        user = User(
            username=DEMO_USERNAME,
            password_hash="demo-placeholder-not-a-real-hash",
        )
       
        db.add(user)
        db.commit()
        db.refresh(user)
    return user