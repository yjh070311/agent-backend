"""
健康检查路由

每个服务都要有health文件：
    1.监控系统定时ping它，判断服务是否存活
    2.负载均衡器根据它决定流量导向哪个实例
    3.部署时做容器健康检查
"""

from fastapi import APIRouter

#prefix让路径带有health前缀
#tags让接口在.docs里分组显示
router=APIRouter(prefix="/health",tags=["健康检查"])

@router.get("")
async def health_check() ->dict[str,str]:
    """
    返回服务状态

    返回200表示正常
    可以扩展成检查数据库、LLM API是否可用
    """
    return{"status":"ok","service":"agent-backend"}
