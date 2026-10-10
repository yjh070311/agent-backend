"""
对话路由

接收多轮消息
返回完整响应
校验规则自动生效
"""

from fastapi import APIRouter

from app.schemas.chat import ChatRequest, ChatResponse, TokenUsage

router = APIRouter(prefix="/chat", tags=["对话"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    对话接口--接收消息，返回回复

    Args:
        pydantic校验过的请求体

    Returns：
        ChatResponse

    关键点：
        - response_model=ChatResponse：告诉 FastAPI 返回类型，
          文档里会显示，多余的字段也会被过滤
        - request.messages：因为声明了 ChatRequest 类型，
          FastAPI 已经帮我们解析并校验了 body，这里直接用属性
          用request.last_user_message快速取最后一条消息
    """
    last_msg = request.last_user_message
    reply = f"收到 {len(request.messages)} 条消息，最后一条是：{last_msg}"

    # 构造一个假的 usage（Day 3 换成真实 LLM 返回的 usage）
    fake_usage = TokenUsage(
        prompt_tokens=len(last_msg),  # 粗略估算：按字符数
        completion_tokens=len(reply),
        total_tokens=len(last_msg) + len(reply),
    )

    return ChatResponse(
        reply=reply,
        model="echo-model",
        usage=fake_usage,
    )