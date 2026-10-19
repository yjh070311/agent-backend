from datetime import datetime

from pydantic import BaseModel,ConfigDict,Field

class RegisterRequest(BaseModel):
    """注册请求体"""

    model_config=ConfigDict(extra="forbid")

    username: str = Field(min_length=3, max_length=50, description="用户名")
    password: str = Field(min_length=8, max_length=128, description="密码，至少 8 位")


class LoginRequest(BaseModel):
    """登录请求体。"""

    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=50, description="用户名")
    password: str = Field(min_length=1, max_length=128, description="密码")


class TokenResponse(BaseModel):
    """登录成功后返回的令牌。"""

    access_token: str = Field(description="JWT 令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(description="有效期（秒）")


class UserOut(BaseModel):
    """用户响应体。永远不返回 password_hash。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    created_at: datetime