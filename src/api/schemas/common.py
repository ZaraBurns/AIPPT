"""
通用API数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class APIResponse(BaseModel):
    """
    非泛型版本的API响应（用于路由返回类型注解）
    """
    code: int = Field(default=200, description="状态码")
    message: str = Field(default="success", description="响应消息")
    data: Optional[dict] = Field(default=None, description="响应数据")
    request_id: str = Field(description="请求ID")
    timestamp: str = Field(description="响应时间戳")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(description="服务状态")
    version: str = Field(description="API版本")
    uptime: float = Field(description="运行时间（秒）")


class ErrorResponse(BaseModel):
    """错误响应"""
    code: int = Field(description="错误码")
    message: str = Field(description="错误消息")
    details: Optional[dict] = Field(default=None, description="错误详情")
    request_id: str = Field(description="请求ID")
