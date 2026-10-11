"""
FastAPI应用入口

启动方式
    unicorn app.main:app --reload

    app.main 路径
    app 实例变量名

FastAPI和CLI的本质区别：
    是HTTP服务，客户端通过HTTP请求触发
    服务会常驻运行，持续监听8000端口
"""

from fastapi import FastAPI

from app.routers import health,chat,conversations,messages


#创建 FastAPI 应用实例
# title 和 version 会显示在自动文档 /docs 里
app=FastAPI(
    title="Agent Backend",
    description="AI Agent 后端服务骨架",
    version="0.1.0",
)


#挂载路由--把各模块的路由注册到应用上
#每个router有自己的prefix和tags，见各自文件
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(conversations.router)
app.include_router(messages.router)

#根路径，访问本机端口时的提示
@app.get("/")
async def root()->dict[str,str]:
    """
    根路由--返回欢迎信息，指向文档地址

    注意：
        -async def：fastapi支持异步路由
        -dict[str,str],返回值类型注解，自动写入文档
    """
    return {"messages":"Agent Backend 已启动，访问.docs查看接口文档"}

