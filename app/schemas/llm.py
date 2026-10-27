"""LLM接口请求与响应"""

from pydantic import BaseModel,ConfigDict,Field

class PingRequest(BaseModel):

    """连通性测试"""
    model_config=ConfigDict(extra="forbid")

    prompt:str=Field(min_length=1,max_length=2000,description="要问模型的一句话")

class TokenUsage(BaseModel):
    """Token用量"""

    prompt_tokens:int=0
    completion_tokens:int=0
    total_tokens:int=0


class PingResponse(BaseModel):
    content:str
    model:str
    usage:TokenUsage


    