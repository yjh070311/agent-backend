"""
统一响应封装

所有接口响应都走这个外壳
    {"code":0,"message":"success","data"}

统一响应的价值：
    1.调用方写一次逻辑，适配所有接口
    2.业务状态码和HTTP状态码分离
    --可能不是http方面的错误，但也要返回
    3.前端容易看

约定：
    code=0表示成功，非0业务错误
    data放实际返回数据
    message放可读说明
"""

from typing import Any ,Generic,TypeVar,Optional

from pydantic import BaseModel

T=TypeVar("T")

class ApiResponse(BaseModel,Generic[T]):
    """
    统一api响应外壳
    T让data类型可变化
    """

    code:int =0
    message:str="success"
    data:Optional[T]=None

    @classmethod
    def success(cls,data:Any=None,message:str="success")->"ApiResponse":
        return cls(code=0,message=message,data=data)
    
    
    
    @classmethod
    def error(cls,code:int,message:str)->"ApiResponse":
        return cls(code=code,message=message,data=None)

class PaginatedData(BaseModel,Generic[T]):
    """
    分页数据结构，嵌套在ApiResponse.data里

    items当前页数据，total总条数
    limit，offset回显本次分页参数
    """

    items:list[T]
    total:int
    limit:int
    offset:int
